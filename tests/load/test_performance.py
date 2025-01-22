import asyncio
import aiohttp
import time
import json
import uuid
from datetime import datetime

async def create_box(session, api_url, customer_id, box_number):
    """Create a single box"""
    box_data = {
        'customer_id': customer_id,
        'room_id#box_id': f'ROOM1#BOX{box_number:03d}',
        'action': 'IN',
        'weight': 50,
        'variety': 'Potato',
        'temperature': 5
    }
    
    start_time = time.time()
    async with session.post(f"{api_url}/box", json=box_data) as response:
        duration = time.time() - start_time
        status = response.status
        return {
            'duration': duration,
            'status': status,
            'box_number': box_number
        }

async def run_load_test(api_url, num_requests=100, concurrent_requests=10):
    """Run load test with specified number of concurrent requests"""
    test_customer_id = f'LOADTEST{uuid.uuid4().hex[:8]}'
    
    # Create test user
    user_data = {
        'customer_id': test_customer_id,
        'company_name': 'Load Test Company',
        'email': f'loadtest_{test_customer_id}@example.com'
    }
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        # Create user
        async with session.post(f"{api_url}/user", json=user_data) as response:
            if response.status != 201:
                print("Failed to create test user")
                return
        
        print(f"Starting load test with {num_requests} requests...")
        start_time = time.time()
        
        # Create tasks in batches
        for batch_start in range(0, num_requests, concurrent_requests):
            batch_end = min(batch_start + concurrent_requests, num_requests)
            batch_tasks = []
            
            for i in range(batch_start, batch_end):
                task = create_box(session, api_url, test_customer_id, i)
                batch_tasks.append(task)
            
            # Run batch of requests
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calculate statistics
        successful_requests = sum(1 for r in results if r['status'] == 201)
        failed_requests = len(results) - successful_requests
        avg_duration = sum(r['duration'] for r in results) / len(results)
        
        print("\nLoad Test Results:")
        print(f"Total Requests: {num_requests}")
        print(f"Concurrent Requests: {concurrent_requests}")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"Average Request Duration: {avg_duration:.3f} seconds")
        print(f"Requests per second: {num_requests/total_duration:.2f}")
        print(f"Successful Requests: {successful_requests}")
        print(f"Failed Requests: {failed_requests}")
        
        # Cleanup
        async with session.delete(f"{api_url}/user/{test_customer_id}") as response:
            if response.status != 200:
                print("Failed to cleanup test user")

if __name__ == '__main__':
    with open('config/dev.json') as f:
        config = json.load(f)
    api_url = config.get('ApiUrl')
    
    print(f"Starting load test against {api_url}")
    asyncio.run(run_load_test(api_url, num_requests=100, concurrent_requests=10))
