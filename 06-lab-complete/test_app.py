import urllib.request
import json
import sys

def test_endpoint(url, method="GET", headers=None, data=None):
    req = urllib.request.Request(url, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    if data:
        if isinstance(data, dict):
            req.add_header("Content-Type", "application/json")
            req_data = json.dumps(data).encode("utf-8")
        else:
            req_data = data
    else:
        req_data = None
        
    try:
        with urllib.request.urlopen(req, data=req_data) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)

def main():
    print("Starting API Integration Tests...")
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    api_key = sys.argv[2] if len(sys.argv) > 2 else "test-api-key"
    print(f"Testing against base URL: {base_url} (Key: {api_key})")
    
    # 1. Health check
    code, body = test_endpoint(f"{base_url.rstrip('/')}/health")
    print(f"Health check: {code} -> {body}")
    assert code == 200, "Health check failed"
    
    # 2. Ready check
    code, body = test_endpoint(f"{base_url.rstrip('/')}/ready")
    print(f"Ready check: {code} -> {body}")
    assert code == 200, "Ready check failed"
    
    # 3. Auth failure
    code, body = test_endpoint(f"{base_url.rstrip('/')}/ask", method="POST", data={"question": "Hello"})
    print(f"Auth failure (no key): {code} -> {body}")
    assert code == 401, "Expected 401 Unauthorized"
    
    # 4. Auth success
    code, body = test_endpoint(
        f"{base_url.rstrip('/')}/ask", 
        method="POST", 
        headers={"X-API-Key": api_key}, 
        data={"question": "What is Docker?"}
    )
    print(f"Auth success: {code} -> {body}")
    assert code == 200, "Expected 200 OK"
    
    # 5. Rate limiting & Cost Guard test
    print("Sending multiple requests to trigger rate limit (20 req/min)...")
    for i in range(25):
        code, body = test_endpoint(
            f"{base_url.rstrip('/')}/ask", 
            method="POST", 
            headers={"X-API-Key": api_key}, 
            data={"question": f"Test question number {i}"}
        )
        if code == 429:
            print(f"Rate limited successfully at request {i}: {code} -> {body}")
            break
        elif code == 503:
            print(f"Daily budget exhausted (Cost Guard) at request {i}: {code} -> {body}")
            break
        elif code != 200:
            print(f"Unexpected response code {code}: {body}")
            break
            
    print("Tests finished successfully!")

if __name__ == "__main__":
    main()
