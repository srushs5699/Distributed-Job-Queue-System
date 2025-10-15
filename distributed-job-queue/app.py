from flask import Flask, request, jsonify
from redis import Redis
from rq import Queue
from rq.job import Job
from tasks import process_data, send_email, generate_report
import time
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Redis connection
redis_conn = Redis(host='redis', port=6379, db=0, decode_responses=True)

# Define queues with different priorities
high_priority_queue = Queue('high', connection=redis_conn)
default_queue = Queue('default', connection=redis_conn)
low_priority_queue = Queue('low', connection=redis_conn)

QUEUE_MAP = {
    'high': high_priority_queue,
    'default': default_queue,
    'low': low_priority_queue
}

TASK_MAP = {
    'process_data': process_data,
    'send_email': send_email,
    'generate_report': generate_report
}


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        redis_conn.ping()
        return jsonify({'status': 'healthy', 'redis': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503


@app.route('/api/v1/jobs', methods=['POST'])
def submit_job():
    """
    Submit a new job to the queue
    
    Request body:
    {
        "task": "process_data",
        "data": {"key": "value"},
        "priority": "default",  # high, default, low
        "retry": true
    }
    """
    start_time = time.time()
    
    try:
        payload = request.get_json()
        
        if not payload:
            return jsonify({'error': 'Invalid JSON payload'}), 400
        
        task_name = payload.get('task')
        task_data = payload.get('data', {})
        priority = payload.get('priority', 'default')
        retry = payload.get('retry', True)
        
        if task_name not in TASK_MAP:
            return jsonify({'error': f'Invalid task: {task_name}'}), 400
        
        if priority not in QUEUE_MAP:
            return jsonify({'error': f'Invalid priority: {priority}'}), 400
        
        # Get the appropriate queue and task
        queue = QUEUE_MAP[priority]
        task_func = TASK_MAP[task_name]
        
        # Enqueue job with retry configuration
        job = queue.enqueue(
            task_func,
            task_data,
            job_timeout='10m',
            result_ttl=86400,  # Keep results for 24 hours
            failure_ttl=86400,
            retry=3 if retry else 0,
            retry_intervals=[60, 300, 900]  # Retry after 1min, 5min, 15min
        )
        
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return jsonify({
            'job_id': job.id,
            'task': task_name,
            'priority': priority,
            'status': 'queued',
            'response_time_ms': round(response_time, 2)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status and result"""
    start_time = time.time()
    
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        
        response = {
            'job_id': job.id,
            'status': job.get_status(),
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'ended_at': job.ended_at.isoformat() if job.ended_at else None,
        }
        
        if job.is_finished:
            response['result'] = job.result
        elif job.is_failed:
            response['error'] = str(job.exc_info)
        
        if hasattr(job, 'retries_left'):
            response['retries_left'] = job.retries_left
        
        response_time = (time.time() - start_time) * 1000
        response['response_time_ms'] = round(response_time, 2)
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': f'Job not found: {str(e)}'}), 404


@app.route('/api/v1/jobs/<job_id>', methods=['DELETE'])
def cancel_job(job_id):
    """Cancel a queued or running job"""
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        
        if job.get_status() in ['queued', 'started']:
            job.cancel()
            return jsonify({
                'job_id': job_id,
                'status': 'cancelled'
            }), 200
        else:
            return jsonify({
                'error': f'Cannot cancel job in status: {job.get_status()}'
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 404


@app.route('/api/v1/jobs', methods=['GET'])
def list_jobs():
    """List jobs with optional status filter"""
    try:
        status_filter = request.args.get('status', None)
        limit = int(request.args.get('limit', 100))
        
        jobs_data = []
        
        # Get jobs from all queues
        for queue_name, queue in QUEUE_MAP.items():
            job_ids = queue.job_ids
            
            for job_id in job_ids[:limit]:
                try:
                    job = Job.fetch(job_id, connection=redis_conn)
                    job_status = job.get_status()
                    
                    if status_filter and job_status != status_filter:
                        continue
                    
                    jobs_data.append({
                        'job_id': job.id,
                        'status': job_status,
                        'queue': queue_name,
                        'created_at': job.created_at.isoformat() if job.created_at else None
                    })
                except:
                    continue
        
        return jsonify({
            'jobs': jobs_data,
            'count': len(jobs_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/metrics', methods=['GET'])
def get_metrics():
    """Get queue metrics for monitoring"""
    try:
        metrics = {}
        
        for queue_name, queue in QUEUE_MAP.items():
            metrics[queue_name] = {
                'queued': len(queue),
                'started': queue.started_job_registry.count,
                'finished': queue.finished_job_registry.count,
                'failed': queue.failed_job_registry.count,
                'deferred': queue.deferred_job_registry.count
            }
        
        # Get worker information
        from rq.worker import Worker
        workers = Worker.all(connection=redis_conn)
        metrics['workers'] = {
            'total': len(workers),
            'busy': len([w for w in workers if w.get_state() == 'busy']),
            'idle': len([w for w in workers if w.get_state() == 'idle'])
        }
        
        return jsonify(metrics), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)