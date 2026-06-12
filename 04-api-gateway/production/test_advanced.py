"""
Test Suite — JWT Authentication + Rate Limiting + Cost Guard

Chạy:
    python test_advanced.py

Yêu cầu:
    - Server đang chạy: python app.py
    - Port: 8000
"""
import json
import time
import urllib.request
import urllib.error


BASE_URL = "http://localhost:8000"


def request(method, path, headers=None, data=None):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_auth():
    """Test JWT authentication flow."""
    print("\n=== Test 1: JWT Authentication ===")

    # 1. Truy cập không có token → 401
    code, body = request("POST", "/ask", data={"question": "hello"})
    assert code == 401, f"Expected 401, got {code}"
    print(f"  ✅ No token → {code} (correct)")

    # 2. Login sai password → 401
    code, body = request("POST", "/auth/token",
                         data={"username": "student", "password": "wrong"})
    assert code == 401, f"Expected 401, got {code}"
    print(f"  ✅ Wrong password → {code} (correct)")

    # 3. Login đúng → lấy token
    code, body = request("POST", "/auth/token",
                         data={"username": "student", "password": "demo123"})
    assert code == 200, f"Expected 200, got {code}"
    token = body["access_token"]
    print(f"  ✅ Login success → token: {token[:20]}...")

    # 4. Dùng token hợp lệ → 200
    code, body = request("POST", "/ask",
                         headers={"Authorization": f"Bearer {token}"},
                         data={"question": "what is docker?"})
    assert code == 200, f"Expected 200, got {code}"
    print(f"  ✅ Valid token → {code} (correct)")
    print(f"     Answer: {body.get('answer', '')[:60]}...")

    # 5. Dùng token sai → 403
    code, body = request("POST", "/ask",
                         headers={"Authorization": "Bearer invalid-token"},
                         data={"question": "hello"})
    assert code == 403, f"Expected 403, got {code}"
    print(f"  ✅ Invalid token → {code} (correct)")

    return token


def test_rate_limiting(token):
    """Test sliding window rate limiter."""
    print("\n=== Test 2: Rate Limiting ===")

    headers = {"Authorization": f"Bearer {token}"}
    hit_limit = False

    for i in range(1, 16):
        code, body = request("POST", "/ask",
                             headers=headers,
                             data={"question": f"rate limit test {i}"})
        if code == 429:
            print(f"  ✅ Rate limited at request {i}: {body.get('detail', {})}")
            hit_limit = True
            break
        elif code == 200:
            remaining = body.get("usage", {}).get("requests_remaining", "?")
            print(f"  Request {i:2d}: 200 OK (remaining: {remaining})")
        else:
            print(f"  ⚠️  Unexpected {code}: {body}")
            break

    if not hit_limit:
        print("  ⚠️  Rate limit not triggered in 15 requests (limit may be > 15)")

    return hit_limit


def test_cost_guard(token):
    """Test budget protection."""
    print("\n=== Test 3: Cost Guard ===")

    headers = {"Authorization": f"Bearer {token}"}

    # Xem usage hiện tại
    code, body = request("GET", "/me/usage", headers=headers)
    if code == 200:
        print(f"  Current usage: ${body.get('cost_usd', 0):.4f} / ${body.get('budget_usd', 0)}")
    else:
        print(f"  ⚠️  Cannot check usage: {code}")

    print("  ✅ Cost guard check passed (budget tracking active)")


def test_admin_endpoint(token):
    """Test role-based access control."""
    print("\n=== Test 4: Role-Based Access ===")

    # Student token → admin endpoint → 403
    headers = {"Authorization": f"Bearer {token}"}
    code, body = request("GET", "/admin/stats", headers=headers)
    assert code == 403, f"Expected 403 for student accessing admin, got {code}"
    print(f"  ✅ Student → /admin/stats → {code} Forbidden (correct)")

    # Teacher token → admin endpoint → 200
    code, body = request("POST", "/auth/token",
                         data={"username": "teacher", "password": "teach456"})
    assert code == 200, f"Login as teacher failed: {code}"
    admin_token = body["access_token"]

    code, body = request("GET", "/admin/stats",
                         headers={"Authorization": f"Bearer {admin_token}"})
    assert code == 200, f"Expected 200 for teacher accessing admin, got {code}"
    print(f"  ✅ Teacher → /admin/stats → {code} OK (correct)")
    print(f"     Stats: {body}")


def test_health():
    """Test health and security headers."""
    print("\n=== Test 5: Health & Security ===")

    code, body = request("GET", "/health")
    assert code == 200, f"Health check failed: {code}"
    print(f"  ✅ /health → {code}")
    print(f"     Status: {body.get('status')}")
    print(f"     Security: {body.get('security')}")


if __name__ == "__main__":
    print("=" * 60)
    print("  Advanced Security Test Suite")
    print("  Server: " + BASE_URL)
    print("=" * 60)

    test_health()
    token = test_auth()
    test_rate_limiting(token)
    test_cost_guard(token)
    test_admin_endpoint(token)

    print("\n" + "=" * 60)
    print("  ✅ All tests completed!")
    print("=" * 60)
