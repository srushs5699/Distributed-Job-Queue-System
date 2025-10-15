import os
import sys
from redis import Redis
from rq import Worker, Queue, Connection

# Get Redis connection details from environment
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
queue_name = os.getenv('QUEUE', 'default')

# Configure Redis connection
redis_conn = Redis(
    host=redis_host,
    port=redis_port,
    db=0,
    decode_responses=True
)

def main():
    """Start RQ worker"""
    try:
        # Test Redis connection
        redis_conn.ping()
        print(f"Connected to Redis at {redis_host}:{redis_port}")
        print(f"Worker listening on queue: {queue_name}")
        
        # Create queue
        queue = Queue(queue_name, connection=redis_conn)
        
        # Start worker with connection context
        with Connection(redis_conn):
            worker = Worker([queue], connection=redis_conn)
            worker.work(with_scheduler=True)
            
    except Exception as e:
        print(f"Error starting worker: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()