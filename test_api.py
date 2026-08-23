import time
import requests

def test_api():
    # Cache miss
    start = time.time()
    res = requests.get("http://localhost:8000/api/migrations/history")
    miss_time = (time.time() - start) * 1000
    
    # Cache hit
    start = time.time()
    res2 = requests.get("http://localhost:8000/api/migrations/history")
    hit_time = (time.time() - start) * 1000
    
    print(f"History Cache Miss: {miss_time:.2f}ms")
    print(f"History Cache Hit: {hit_time:.2f}ms")
    
    # Test GZip - let's find an existing job and fetch details
    jobs = res.json().get("items", [])
    if jobs:
        job_id = jobs[0]["id"]
        res3 = requests.get(f"http://localhost:8000/api/migrations/{job_id}/details", headers={"Accept-Encoding": "gzip"})
        print(f"GZip applied: {'Content-Encoding' in res3.headers}")
        if 'Content-Encoding' in res3.headers:
            print(f"Content-Encoding value: {res3.headers['Content-Encoding']}")
    else:
        print("No jobs found to test GZip.")

if __name__ == "__main__":
    time.sleep(2) # Give server time to start
    test_api()
