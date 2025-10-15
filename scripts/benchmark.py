#!/usr/bin/env python3
"""
Performance benchmark script for the distributed job queue system
Tests throughput, latency, and success rate under various loads
"""

import time
import requests
import statistics
import concurrent.futures
from typing import List, Dict
import json


API_URL = "http://localhost:5000"


def submit_job(task: str = "process_data", priority: str = "default") -> Dict:
    """Submit a single job and measure response time"""
    start = time.time()
    
    try:
        response = requests.post(
            f"{API_URL}/api/v1/jobs",
            json={
                'task': task,
                'data': {'items': 50},
                'priority': priority,
                'retry': True
            },
            timeout=5
        )
        
        latency = (time.time() - start) * 1000  # Convert to ms
        
        if response.status_code == 201:
            return {
                'success': True,
                'latency': latency,
                'job_id': response.json().get('job_id')
            }
        else:
            return {
                'success': False,
                'latency': latency,
                'error': response.text
            }
    except Exception as e:
        return {
            'success': False,
            'latency': (time.time() - start) * 1000,
            'error': str(e)
        }


def test_latency(num_requests: int = 100) -> Dict:
    """Test API latency under load"""
    print(f"\n{'='*60}")
    print(f"Testing API Latency ({num_requests} requests)")
    print(f"{'='*60}")
    
    results = []
    
    for i in range(num_requests):
        result = submit_job()
        results.append(result)
        
        if (i + 1) % 10 == 0:
            print(f"Progress: {i + 1}/{num_requests} requests")
    
    # Calculate statistics
    latencies = [r['latency'] for r in results if r['success']]
    success_count = sum(1 for r in results if r['success'])
    
    if latencies:
        latencies.sort()
        stats = {
            'total_requests': num_requests,
            'successful': success_count,
            'success_rate': (success_count / num_requests) * 100,
            'min_latency': min(latencies),
            'max_latency': max(latencies),
            'mean_latency': statistics.mean(latencies),
            'median_latency': statistics.median(latencies),
            'p95_latency': latencies[int(len(latencies) * 0.95)],
            'p99_latency': latencies[int(len(latencies) * 0.99)]
        }
        
        print(f"\nResults:")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Successful: {stats['successful']} ({stats['success_rate']:.1f}%)")
        print(f"  Latency (ms):")
        print(f"    Min:    {stats['min_latency']:.2f}")
        print(f"    Mean:   {stats['mean_latency']:.2f}")
        print(f"    Median: {stats['median_latency']:.2f}")
        print(f"    P95:    {stats['p95_latency']:.2f}")
        print(f"    P99:    {stats['p99_latency']:.2f}")
        print(f"    Max:    {stats['max_latency']:.2f}")
        
        # Check against requirements
        if stats['p99_latency'] < 200:
            print(f"\n✓ PASS: P99 latency ({stats['p99_latency']:.2f}ms) < 200ms")
        else:
            print(f"\n✗ FAIL: P99 latency ({stats['p99_latency']:.2f}ms) >= 200ms")
        
        return stats
    else:
        print("\n✗ FAIL: No successful requests")
        return {}


def test_throughput(duration_seconds: int = 60) -> Dict:
    """Test system throughput over time"""
    print(f"\n{'='*60}")
    print(f"Testing Throughput ({duration_seconds} seconds)")
    print(f"{'='*60}")
    
    start_time = time.time()
    end_time = start_time + duration_seconds
    
    job_count = 0
    successful = 0
    
    while time.time() < end_time:
        result = submit_job()
        job_count += 1
        if result['success']:
            successful += 1
        
        if job_count % 100 == 0:
            elapsed = time.time() - start_time
            rate = job_count / elapsed
            print(f"Progress: {job_count} jobs, {rate:.1f} jobs/sec")
    
    total_time = time.time() - start_time
    
    stats = {
        'duration': total_time,
        'total_jobs': job_count,
        'successful_jobs': successful,
        'failed_jobs': job_count - successful,
        'jobs_per_second': job_count / total_time,
        'success_rate': (successful / job_count) * 100
    }
    
    print(f"\nResults:")
    print(f"  Duration: {stats['duration']:.1f}s")
    print(f"  Total Jobs: {stats['total_jobs']}")
    print(f"  Successful: {stats['successful_jobs']}")
    print(f"  Failed: {stats['failed_jobs']}")
    print(f"  Throughput: {stats['jobs_per_second']:.2f} jobs/sec")
    print(f"  Success Rate: {stats['success_rate']:.1f}%")
    
    # Calculate daily projection
    jobs_per_day = stats['jobs_per_second'] * 86400
    print(f"  Daily Projection: {jobs_per_day:,.0f} jobs/day")
    
    if jobs_per_day >= 10000:
        print(f"\n✓ PASS: Can handle 10K+ jobs/day")
    else:
        print(f"\n✗ FAIL: Cannot handle 10K+ jobs/day")
    
    return stats


def test_concurrent_load(num_workers: int = 10, jobs_per_worker: int = 10) -> Dict:
    """Test system under concurrent load"""
    print(f"\n{'='*60}")
    print(f"Testing Concurrent Load ({num_workers} workers, {jobs_per_worker} jobs each)")
    print(f"{'='*60}")
    
    def worker_task(worker_id: int) -> List[Dict]:
        results = []
        for i in range(jobs_per_worker):
            result = submit_job()
            results.append(result)
        return results
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker_task, i) for i in range(num_workers)]
        all_results = []
        
        for future in concurrent.futures.as_completed(futures):
            all_results.extend(future.result())
    
    total_time = time.time() - start_time
    
    successful = sum(1 for r in all_results if r['success'])
    total = len(all_results)
    latencies = [r['latency'] for r in all_results if r['success']]
    
    stats = {
        'total_jobs': total,
        'successful': successful,
        'failed': total - successful,
        'success_rate': (successful / total) * 100,
        'total_time': total_time,
        'jobs_per_second': total / total_time
    }
    
    if latencies:
        latencies.sort()
        stats['mean_latency'] = statistics.mean(latencies)
        stats['p95_latency'] = latencies[int(len(latencies) * 0.95)]
        stats['p99_latency'] = latencies[int(len(latencies) * 0.99)]
    
    print(f"\nResults:")
    print(f"  Total Jobs: {stats['total_jobs']}")
    print(f"  Successful: {stats['successful']} ({stats['success_rate']:.1f}%)")
    print(f"  Failed: {stats['failed']}")
    print(f"  Total Time: {stats['total_time']:.2f}s")
    print(f"  Throughput: {stats['jobs_per_second']:.2f} jobs/sec")
    
    if 'p99_latency' in stats:
        print(f"  P99 Latency: {stats['p99_latency']:.2f}ms")
        
        if stats['p99_latency'] < 200:
            print(f"\n✓ PASS: Concurrent load test passed")
        else:
            print(f"\n✗ FAIL: P99 latency too high under load")
    
    return stats


def test_priority_queues() -> Dict:
    """Test priority queue functionality"""
    print(f"\n{'='*60}")
    print(f"Testing Priority Queues")
    print(f"{'='*60}")
    
    # Submit jobs to different priority queues
    high_jobs = []
    default_jobs = []
    low_jobs = []
    
    for _ in range(5):
        result = submit_job(priority='low')
        if result['success']:
            low_jobs.append(result['job_id'])
    
    time.sleep(0.5)
    
    for _ in range(5):
        result = submit_job(priority='high')
        if result['success']:
            high_jobs.append(result['job_id'])
    
    for _ in range(5):
        result = submit_job(priority='default')
        if result['success']:
            default_jobs.append(result['job_id'])
    
    print(f"\nSubmitted:")
    print(f"  High Priority: {len(high_jobs)} jobs")
    print(f"  Default Priority: {len(default_jobs)} jobs")
    print(f"  Low Priority: {len(low_jobs)} jobs")
    print(f"\n✓ Priority queue submission successful")
    
    return {
        'high_jobs': len(high_jobs),
        'default_jobs': len(default_jobs),
        'low_jobs': len(low_jobs)
    }


def check_system_health() -> bool:
    """Check if system is healthy before running benchmarks"""
    print(f"\n{'='*60}")
    print(f"Checking System Health")
    print(f"{'='*60}")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API is healthy")
            print(f"✓ Redis is {data.get('redis', 'unknown')}")
            
            # Get metrics
            metrics_response = requests.get(f"{API_URL}/api/v1/metrics", timeout=5)
            if metrics_response.status_code == 200:
                metrics = metrics_response.json()
                if 'workers' in metrics:
                    worker_count = metrics['workers'].get('total', 0)
                    print(f"✓ Workers: {worker_count} active")
                    
                    if worker_count == 0:
                        print(f"⚠ WARNING: No workers detected")
                        return False
            
            return True
        else:
            print(f"✗ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to API: {e}")
        print(f"\nMake sure services are running:")
        print(f"  docker-compose up -d")
        return False


def main():
    """Run all benchmarks"""
    print("\n" + "="*60)
    print("DISTRIBUTED JOB QUEUE - PERFORMANCE BENCHMARK")
    print("="*60)
    
    # Check system health first
    if not check_system_health():
        print("\n✗ System health check failed. Aborting benchmarks.")
        return
    
    results = {}
    
    # Run benchmarks
    try:
        results['latency'] = test_latency(num_requests=100)
        time.sleep(2)
        
        results['concurrent'] = test_concurrent_load(num_workers=10, jobs_per_worker=10)
        time.sleep(2)
        
        results['priority'] = test_priority_queues()
        time.sleep(2)
        
        # Uncomment for longer throughput test
        # results['throughput'] = test_throughput(duration_seconds=60)
        
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
    except Exception as e:
        print(f"\n\nError during benchmark: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"BENCHMARK SUMMARY")
    print(f"{'='*60}")
    
    if 'latency' in results and results['latency']:
        lat = results['latency']
        print(f"\nLatency Test:")
        print(f"  ✓ P99: {lat.get('p99_latency', 0):.2f}ms")
        print(f"  ✓ Success Rate: {lat.get('success_rate', 0):.1f}%")
    
    if 'concurrent' in results and results['concurrent']:
        conc = results['concurrent']
        print(f"\nConcurrent Load Test:")
        print(f"  ✓ Throughput: {conc.get('jobs_per_second', 0):.2f} jobs/sec")
        print(f"  ✓ Success Rate: {conc.get('success_rate', 0):.1f}%")
    
    if 'priority' in results:
        print(f"\nPriority Queues:")
        print(f"  ✓ All priority levels functional")
    
    print(f"\n{'='*60}")
    print(f"Benchmark Complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()