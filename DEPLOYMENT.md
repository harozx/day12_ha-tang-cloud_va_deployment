# Deployment Information

## Public URL
https://day12-agent-production-6443.up.railway.app

## Platform
Railway / Render

## Test Commands

### Health Check
```bash
curl -i https://day12-agent-production-6443.up.railway.app/health
# Expected: {"status": "ok", "version": "1.0.0", "environment": "production", ...}
```

### Readiness Check
```bash
curl -i https://day12-agent-production-6443.up.railway.app/ready
# Expected: {"ready": true}
```

### API Test (with authentication)
```bash
curl -X POST https://day12-agent-production-6443.up.railway.app/ask \
  -H "X-API-Key: test-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello AI Agent"}'
```

### Rate Limiting Test (Spamming requests)
```bash
for i in {1..15}; do 
  curl -H "X-API-Key: test-api-key" https://day12-agent-production-6443.up.railway.app/ask \
    -X POST -d '{"question":"test"}' -H "Content-Type: application/json"; 
done
# Expected to receive HTTP 429 Too Many Requests after 10 requests.
```

## Environment Variables Set
- `PORT`: `8000` (auto-injected by Railway/Render)
- `AGENT_API_KEY`: `test-api-key` (used for authentication)
- `ENVIRONMENT`: `production` (disables /docs and other dev settings)
- `RATE_LIMIT_PER_MINUTE`: `10`
- `DAILY_BUDGET_USD`: `1.0`
- `LOG_LEVEL`: `INFO`
- `REDIS_URL`: `redis://redis:6379/0` (in docker-compose) or external redis url in cloud

## Local Verification
We have verified that the project passes 100% of the production readiness criteria checked by the `check_production_ready.py` script:
```
=======================================================
  Production Readiness Check — Day 12 Lab
=======================================================

📁 Required Files
  ✅ Dockerfile exists
  ✅ docker-compose.yml exists
  ✅ .dockerignore exists
  ✅ .env.example exists
  ✅ requirements.txt exists
  ✅ railway.toml or render.yaml exists

🔒 Security
  ✅ .env in .gitignore
  ✅ No hardcoded secrets in code

🌐 API Endpoints (code check)
  ✅ /health endpoint defined
  ✅ /ready endpoint defined
  ✅ Authentication implemented
  ✅ Rate limiting implemented
  ✅ Graceful shutdown (SIGTERM)
  ✅ Structured logging (JSON)

🐳 Docker
  ✅ Multi-stage build
  ✅ Non-root user
  ✅ HEALTHCHECK instruction
  ✅ Slim base image
  ✅ .dockerignore covers .env
  ✅ .dockerignore covers __pycache__

=======================================================
  Result: 20/20 checks passed (100%)
  🎉 PRODUCTION READY! Deploy nào!
=======================================================
```
