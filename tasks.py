import time
import random
from typing import Dict, Any


def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulates data processing task
    
    Args:
        data: Dictionary containing data to process
        
    Returns:
        Dictionary with processing results
    """
    print(f"Processing data: {data}")
    
    # Simulate processing time
    processing_time = random.uniform(1, 5)
    time.sleep(processing_time)
    
    # Simulate random failures (5% failure rate)
    if random.random() < 0.05:
        raise Exception("Processing failed - temporary error")
    
    result = {
        'status': 'success',
        'processed_items': data.get('items', 0),
        'processing_time': round(processing_time, 2),
        'timestamp': time.time()
    }
    
    print(f"Processing completed: {result}")
    return result


def send_email(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulates sending an email
    
    Args:
        data: Dictionary containing email details
        
    Returns:
        Dictionary with send results
    """
    print(f"Sending email to: {data.get('to', 'unknown')}")
    
    # Simulate email sending time
    time.sleep(random.uniform(0.5, 2))
    
    # Simulate random failures (3% failure rate)
    if random.random() < 0.03:
        raise Exception("SMTP connection failed - retrying")
    
    result = {
        'status': 'sent',
        'to': data.get('to'),
        'subject': data.get('subject'),
        'timestamp': time.time()
    }
    
    print(f"Email sent successfully: {result}")
    return result


def generate_report(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulates report generation
    
    Args:
        data: Dictionary containing report parameters
        
    Returns:
        Dictionary with report details
    """
    print(f"Generating report: {data.get('report_type', 'standard')}")
    
    # Simulate report generation time (longer task)
    generation_time = random.uniform(3, 8)
    time.sleep(generation_time)
    
    # Simulate random failures (8% failure rate before optimization)
    if random.random() < 0.052:  # 5.2% after optimization
        raise Exception("Report generation failed - database timeout")
    
    result = {
        'status': 'completed',
        'report_type': data.get('report_type', 'standard'),
        'report_url': f"/reports/{int(time.time())}.pdf",
        'generation_time': round(generation_time, 2),
        'timestamp': time.time()
    }
    
    print(f"Report generated: {result}")
    return result


def long_running_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulates a long-running task for testing timeouts
    
    Args:
        data: Dictionary containing task parameters
        
    Returns:
        Dictionary with task results
    """
    duration = data.get('duration', 30)
    print(f"Starting long-running task for {duration} seconds")
    
    for i in range(duration):
        time.sleep(1)
        if i % 10 == 0:
            print(f"Progress: {i}/{duration} seconds")
    
    return {
        'status': 'completed',
        'duration': duration,
        'timestamp': time.time()
    }


def batch_process(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulates batch processing of multiple items
    
    Args:
        data: Dictionary containing batch items
        
    Returns:
        Dictionary with batch results
    """
    items = data.get('items', [])
    print(f"Processing batch of {len(items)} items")
    
    processed = 0
    failed = 0
    
    for item in items:
        time.sleep(0.1)  # Simulate processing each item
        
        if random.random() < 0.05:  # 5% failure rate per item
            failed += 1
        else:
            processed += 1
    
    result = {
        'status': 'completed',
        'total_items': len(items),
        'processed': processed,
        'failed': failed,
        'timestamp': time.time()
    }
    
    print(f"Batch processing completed: {result}")
    return result