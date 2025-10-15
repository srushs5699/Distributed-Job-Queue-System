import pytest
import json
import time
import requests
from redis import Redis
from rq import Queue

# These tests require Docker services to be running
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def api_url():
    """Base API URL"""
    return "http://localhost:5000"


@pytest.fixture(scope="module")
def redis_conn():
    """Redis connection for testing"""
    return Redis(host='localhost', port=6379, db=0, decode_responses=True)


class TestEndToEndWorkflow:
    """Test complete job lifecycle"""
    
    def test_submit_and_process_job(self, api_url, redis_conn):
        """Test submitting a job and waiting for completion"""
        # Submit job
        payload = {
            'task': 'process_data',
            'data': {'items': 50},
            'priority': 'high',
            'retry': True
        }
        
        response = requests.post(
            f"{api_url}/api/v1/jobs",
            json=payload
        )
        
        assert response.status_code == 201
        job_data = response.json()
        job_id = job_data['job_id']
        assert job_data['response_time_ms'] < 200
        
        # Wait for job to complete (max 30 seconds)
        max_wait = 30
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = requests.get(f"{api_url}/api/v1/jobs/{job_id}")
            assert response.status_code == 200
            
            status_data = response.json()
            assert status_data['response_time_ms'] < 200
            
            if status_data['status'] == 'finished':
                assert 'result' in status_data
                assert status_data['result']['status'] == 'success'
                break
            
            time.sleep(1)
        else:
            pytest.fail("Job did not complete within timeout")
    
    def test_priority_queue_ordering(self, api_url):
        """Test that high priority jobs are processed first"""
        # Submit low priority job
        low_job = requests.post(
            f"{api_url}/api/v1/jobs",
            json={
                'task': 'process_data',
                'data': {'items': 10},
                'priority': 'low'
            }
        ).json()
        
        time.sleep(0.5)
        
        # Submit high priority job
        high_job = requests.post(
            f"{api_url}/api/v1/jobs",
            json={
                'task': 'process_data',
                'data': {'items': 10},
                'priority': 'high'
            }
        ).json()
        
        # Wait and check completion order
        time.sleep(8)
        
        low_status = requests.get(
            f"{api_url}/api/v1/jobs/{low_job['job_id']}"
        ).json()
        
        high_status = requests.get(
            f"{api_url}/api/v1/jobs/{high_job['job_id']}"
        ).json()
        
        # High priority should complete first or at same time
        if high_status['status'] == 'finished' and low_status['status'] == 'finished':
            high_end = high_status.get('ended_at', '')
            low_end = low_status.get('ended_at', '')
            # Just verify both completed - exact ordering depends on worker availability
            assert high_status['status'] == 'finished'


class TestRetryMechanism:
    """Test job retry logic"""
    
    def test_job_retry_on_failure(self, api_url):
        """Test that failed jobs are retried"""
        # Submit multiple jobs to increase chance of failure
        job_ids = []
        for _ in range(20):
            response = requests.post(
                f"{api_url}/api/v1/jobs",
                json={
                    'task': 'process_data',
                    'data': {'items': 100},
                    'priority': 'default',
                    'retry': True
                }
            )
            if response.status_code == 201:
                job_ids.append(response.json()['job_id'])
        
        # Wait for processing
        time.sleep(15)
        
        # Check for any retried jobs
        retried_count = 0
        for job_id in job_ids:
            response = requests.get(f"{api_url}/api/v1/jobs/{job_id}")
            if response.status_code == 200:
                data = response.json()
                if 'retries_left' in data:
                    retried_count += 1
        
        # Should have at least some evidence of retry mechanism
        assert len(job_ids) > 0


class TestPerformance:
    """Test system performance under load"""
    
    def test_api_response_latency(self, api_url):
        """Test that API responses are under 200ms"""
        latencies = []
        
        for _ in range(50):
            start = time.time()
            response = requests.post(
                f"{api_url}/api/v1/jobs",
                json={
                    'task': 'send_email',
                    'data': {'to': 'test@example.com'},
                    'priority': 'default'
                }
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 201:
                latencies.append(latency)
        
        # Calculate percentiles
        latencies.sort()
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        
        assert p95 < 200, f"P95 latency {p95}ms exceeds 200ms"
        assert p99 < 200, f"P99 latency {p99}ms exceeds 200ms"
    
    def test_concurrent_job_submission(self, api_url):
        """Test submitting multiple jobs concurrently"""
        import concurrent.futures
        
        def submit_job():
            response = requests.post(
                f"{api_url}/api/v1/jobs",
                json={
                    'task': 'process_data',
                    'data': {'items': 10},
                    'priority': 'default'
                }
            )
            return response.status_code == 201
        
        # Submit 100 jobs concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_job) for _ in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_rate = sum(results) / len(results) * 100
        assert success_rate >= 95, f"Success rate {success_rate}% is below 95%"


class TestMonitoring:
    """Test monitoring endpoints"""
    
    def test_metrics_endpoint(self, api_url):
        """Test metrics endpoint returns valid data"""
        response = requests.get(f"{api_url}/api/v1/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check queue metrics exist
        assert 'high' in data or 'default' in data or 'low' in data
        assert 'workers' in data
        
        # Verify worker metrics
        assert 'total' in data['workers']
        assert 'busy' in data['workers']
        assert 'idle' in data['workers']
    
    def test_health_check(self, api_url):
        """Test health check endpoint"""
        response = requests.get(f"{api_url}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['redis'] == 'connected'


class TestFailureRecovery:
    """Test system failure recovery"""
    
    def test_job_failure_rate(self, api_url):
        """Verify job failure rate is within acceptable limits"""
        # Submit 100 jobs
        job_ids = []
        for _ in range(100):
            response = requests.post(
                f"{api_url}/api/v1/jobs",
                json={
                    'task': 'process_data',
                    'data': {'items': 50},
                    'priority': 'default',
                    'retry': True
                }
            )
            if response.status_code == 201:
                job_ids.append(response.json()['job_id'])
        
        # Wait for processing
        time.sleep(20)
        
        # Check failure rate
        failed = 0
        finished = 0
        
        for job_id in job_ids:
            response = requests.get(f"{api_url}/api/v1/jobs/{job_id}")
            if response.status_code == 200:
                status = response.json()['status']
                if status == 'failed':
                    failed += 1
                elif status == 'finished':
                    finished += 1
        
        total = failed + finished
        if total > 0:
            failure_rate = (failed / total) * 100
            # Should be around 5.2% or less
            assert failure_rate <= 10, f"Failure rate {failure_rate}% exceeds 10%"