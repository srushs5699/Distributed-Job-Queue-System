import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from app import app
from tasks import process_data, send_email, generate_report


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_redis():
    """Mock Redis connection"""
    with patch('app.redis_conn') as mock:
        mock.ping.return_value = True
        yield mock


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_success(self, client, mock_redis):
        """Test successful health check"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['redis'] == 'connected'
    
    def test_health_check_redis_down(self, client, mock_redis):
        """Test health check when Redis is down"""
        mock_redis.ping.side_effect = Exception("Connection failed")
        response = client.get('/health')
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['status'] == 'unhealthy'


class TestJobSubmission:
    """Test job submission endpoint"""
    
    @patch('app.QUEUE_MAP')
    def test_submit_job_success(self, mock_queue_map, client):
        """Test successful job submission"""
        mock_queue = Mock()
        mock_job = Mock()
        mock_job.id = 'test-job-123'
        mock_queue.enqueue.return_value = mock_job
        mock_queue_map.__getitem__.return_value = mock_queue
        
        payload = {
            'task': 'process_data',
            'data': {'items': 100},
            'priority': 'default',
            'retry': True
        }
        
        response = client.post('/api/v1/jobs',
                              data=json.dumps(payload),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['job_id'] == 'test-job-123'
        assert data['task'] == 'process_data'
        assert data['priority'] == 'default'
        assert data['status'] == 'queued'
        assert 'response_time_ms' in data
        assert data['response_time_ms'] < 200  # Sub 200ms requirement
    
    def test_submit_job_invalid_task(self, client):
        """Test job submission with invalid task"""
        payload = {
            'task': 'invalid_task',
            'data': {}
        }
        
        response = client.post('/api/v1/jobs',
                              data=json.dumps(payload),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_submit_job_invalid_priority(self, client):
        """Test job submission with invalid priority"""
        payload = {
            'task': 'process_data',
            'data': {},
            'priority': 'invalid'
        }
        
        response = client.post('/api/v1/jobs',
                              data=json.dumps(payload),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_submit_job_no_payload(self, client):
        """Test job submission without payload"""
        response = client.post('/api/v1/jobs',
                              data='',
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestJobStatus:
    """Test job status endpoint"""
    
    @patch('app.Job')
    def test_get_job_status_queued(self, mock_job_class, client):
        """Test getting status of queued job"""
        mock_job = Mock()
        mock_job.id = 'test-job-123'
        mock_job.get_status.return_value = 'queued'
        mock_job.created_at = None
        mock_job.started_at = None
        mock_job.ended_at = None
        mock_job.is_finished = False
        mock_job.is_failed = False
        mock_job_class.fetch.return_value = mock_job
        
        response = client.get('/api/v1/jobs/test-job-123')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['job_id'] == 'test-job-123'
        assert data['status'] == 'queued'
        assert 'response_time_ms' in data
        assert data['response_time_ms'] < 200
    
    @patch('app.Job')
    def test_get_job_status_finished(self, mock_job_class, client):
        """Test getting status of finished job"""
        mock_job = Mock()
        mock_job.id = 'test-job-123'
        mock_job.get_status.return_value = 'finished'
        mock_job.is_finished = True
        mock_job.is_failed = False
        mock_job.result = {'status': 'success'}
        mock_job.created_at = None
        mock_job.started_at = None
        mock_job.ended_at = None
        mock_job_class.fetch.return_value = mock_job
        
        response = client.get('/api/v1/jobs/test-job-123')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'finished'
        assert 'result' in data
    
    @patch('app.Job')
    def test_get_job_status_failed(self, mock_job_class, client):
        """Test getting status of failed job"""
        mock_job = Mock()
        mock_job.id = 'test-job-123'
        mock_job.get_status.return_value = 'failed'
        mock_job.is_finished = False
        mock_job.is_failed = True
        mock_job.exc_info = "Error message"
        mock_job.created_at = None
        mock_job.started_at = None
        mock_job.ended_at = None
        mock_job_class.fetch.return_value = mock_job
        
        response = client.get('/api/v1/jobs/test-job-123')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'failed'
        assert 'error' in data
    
    @patch('app.Job')
    def test_get_job_status_not_found(self, mock_job_class, client):
        """Test getting status of non-existent job"""
        mock_job_class.fetch.side_effect = Exception("Not found")
        
        response = client.get('/api/v1/jobs/invalid-job')
        
        assert response.status_code == 404


class TestJobCancellation:
    """Test job cancellation endpoint"""
    
    @patch('app.Job')
    def test_cancel_queued_job(self, mock_job_class, client):
        """Test cancelling a queued job"""
        mock_job = Mock()
        mock_job.id = 'test-job-123'
        mock_job.get_status.return_value = 'queued'
        mock_job_class.fetch.return_value = mock_job
        
        response = client.delete('/api/v1/jobs/test-job-123')
        
        assert response.status_code == 200
        mock_job.cancel.assert_called_once()
    
    @patch('app.Job')
    def test_cancel_finished_job(self, mock_job_class, client):
        """Test cancelling a finished job"""
        mock_job = Mock()
        mock_job.get_status.return_value = 'finished'
        mock_job_class.fetch.return_value = mock_job
        
        response = client.delete('/api/v1/jobs/test-job-123')
        
        assert response.status_code == 400


class TestMetrics:
    """Test metrics endpoint"""
    
    @patch('app.QUEUE_MAP')
    @patch('app.Worker')
    def test_get_metrics(self, mock_worker, mock_queue_map, client):
        """Test getting queue metrics"""
        mock_queue = Mock()
        mock_queue.__len__.return_value = 10
        mock_queue.started_job_registry.count = 2
        mock_queue.finished_job_registry.count = 100
        mock_queue.failed_job_registry.count = 5
        mock_queue.deferred_job_registry.count = 0
        
        mock_queue_map.items.return_value = [('default', mock_queue)]
        mock_worker.all.return_value = [Mock(), Mock()]
        
        response = client.get('/api/v1/metrics')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'default' in data
        assert 'workers' in data


class TestTasks:
    """Test task functions"""
    
    def test_process_data_success(self):
        """Test successful data processing"""
        result = process_data({'items': 10})
        assert result['status'] == 'success'
        assert result['processed_items'] == 10
        assert 'processing_time' in result
    
    def test_send_email_success(self):
        """Test successful email sending"""
        result = send_email({'to': 'test@example.com', 'subject': 'Test'})
        assert result['status'] == 'sent'
        assert result['to'] == 'test@example.com'
    
    def test_generate_report_success(self):
        """Test successful report generation"""
        result = generate_report({'report_type': 'monthly'})
        assert result['status'] == 'completed'
        assert result['report_type'] == 'monthly'
        assert 'report_url' in result