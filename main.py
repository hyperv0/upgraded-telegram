from apify import Actor
import threading
import requests
import time
from datetime import datetime
from typing import List
import queue

class IPFetcher:
    def __init__(self, num_threads: int = 20):
        self.num_threads = num_threads
        self.queue = queue.Queue()
        self.results = []
        self.lock = threading.Lock()

    def worker(self):
        while True:
            try:
                # Get task from queue with timeout
                task_id = self.queue.get(timeout=1)
            except queue.Empty:
                break

            try:
                # Fetch IP from ifconfig.me
                response = requests.get('https://ifconfig.me/ip', timeout=10)
                ip_address = response.text.strip()
                
                # Store result with timestamp
                with self.lock:
                    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    self.results.append({
                        'task_id': task_id,
                        'ip_address': ip_address,
                        'timestamp': timestamp
                    })
                    
                    # Log to Apify console
                    Actor.log.info(f'Task {task_id}: IP Address: {ip_address} at {timestamp}')
            
            except requests.RequestException as e:
                Actor.log.error(f'Task {task_id}: Error fetching IP: {str(e)}')
            
            finally:
                self.queue.task_done()

    def run(self, num_requests: int = 50):
        # Fill queue with tasks
        for i in range(num_requests):
            self.queue.put(i)

        threads: List[threading.Thread] = []
        
        # Create and start threads
        for _ in range(self.num_threads):
            thread = threading.Thread(target=self.worker)
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        return self.results

async def main():
    async with Actor:
        # Log the start of the actor
        Actor.log.info('Starting IP fetcher actor...')

        # Get input if any
        actor_input = await Actor.get_input() or {}
        num_requests = actor_input.get('num_requests', 50)
        
        # Initialize and run IP fetcher
        fetcher = IPFetcher(num_threads=20)
        results = fetcher.run(num_requests=num_requests)

        # Store results in default dataset
        await Actor.push_data(results)

        # Log summary
        Actor.log.info(f'Completed fetching {len(results)} IP addresses')
        
if __name__ == "__main__":
    Actor.main()