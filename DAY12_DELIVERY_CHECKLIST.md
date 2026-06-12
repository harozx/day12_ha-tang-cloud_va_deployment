#  Delivery Checklist — Day 12 Lab Submission

> **Student Name:** Cao Văn Hảo  
> **Student ID:** 2A202600874  
> **Date:** 12/06/2026

---

##  Submission Requirements

Submit a **GitHub repository** containing:

### 1. Mission Answers (40 points)

✅ File `MISSION_ANSWERS.md` đã hoàn thành với đáp án đầy đủ:

```markdown
# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Hardcoded Secrets — API key (`OPENAI_API_KEY`) và database URL ghi trực tiếp trong code
2. Không có Configuration Management — DEBUG, MAX_TOKENS hardcode thay vì env vars
3. Dùng print() thay vì Structured Logging — khó thu thập/phân tích log trong production
4. Không có Health Check Endpoint — cloud platform không detect được khi agent bị treo
5. Host/Port cố định — hardcode localhost:8000, không đọc PORT env var

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcode trong code | Environment variables (.env) | Tránh rò rỉ secrets, linh hoạt giữa các môi trường |
| Health Check | Không có | /health (liveness) + /ready (readiness) | Platform tự động restart container bị lỗi |
| Logging | print() | Structured JSON logging | Thuận tiện cho log collectors phân tích tự động |
| Shutdown | Tắt đột ngột (crash) | Graceful shutdown (SIGTERM + chờ in-flight) | Không mất data người dùng khi restart |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: python:3.11 (Debian, ~1 GB, có đầy đủ build tools)
2. Working directory: WORKDIR /app — mọi lệnh COPY/RUN/CMD chạy trong thư mục này
3. COPY requirements.txt trước: tận dụng Docker layer caching, không reinstall khi code thay đổi
4. CMD vs ENTRYPOINT: CMD bị ghi đè bởi docker run args, ENTRYPOINT cố định + args append vào

### Exercise 2.3: Image size comparison
- Develop (single-stage, python:3.11): ~1.02 GB
- Production (multi-stage, python:3.11-slim): ~143 MB
- Difference: giảm ~86%

### Exercise 2.4: Docker Compose stack
- Services: agent (3 instances), redis (session store), qdrant (vector DB), nginx (load balancer)
- Giao tiếp qua Docker bridge network, Nginx round-robin đến agent:8000

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://day12-agent-production-6443.up.railway.app
- Screenshot: [Dashboard](screenshots/dashboard.png)

## Part 4: API Security

### Exercise 4.1-4.3: Test results
- Gọi không có API Key → 401 Unauthorized ✅
- Gọi với API Key sai → 401 Unauthorized ✅
- Gọi với API Key đúng → 200 OK + response từ Mock LLM ✅
- Spam 11+ requests/min → 429 Too Many Requests ✅

### Exercise 4.4: Cost guard implementation
- Daily budget $5.0 (configurable qua DAILY_BUDGET_USD env var)
- Ước lượng token: input_tokens = len(question.split()) * 2
- Chi phí: (input/1000) * $0.00015 + (output/1000) * $0.0006
- Lưu tích lũy trong Redis (INCRBYFLOAT) với key `cost:global:YYYY-MM-DD`
- Vượt budget → 503 "Daily budget exhausted"

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
1. Health checks: /health (liveness) trả status+uptime+checks, /ready (readiness) trả 503 khi shutdown
2. Graceful shutdown: SIGTERM → _is_ready=False → chờ in_flight_requests==0 (max 30s) → exit
3. Stateless design: Session, rate-limit counter, cost spending đều lưu Redis
4. Load balancing: Nginx reverse proxy, round-robin đến 3 agent instances
```

---

### 2. Full Source Code - Lab 06 Complete (60 points)

✅ Production-ready agent đầy đủ tại `06-lab-complete/`:

```
06-lab-complete/
├── app/
│   ├── __init__.py          # Package marker
│   ├── main.py              # Main application (275 lines)
│   ├── config.py            # 12-Factor config (56 lines)
│   ├── auth.py              # API Key authentication (14 lines)
│   ├── rate_limiter.py      # Sliding window rate limiting (62 lines)
│   └── cost_guard.py        # Daily budget protection (63 lines)
├── utils/
│   └── mock_llm.py          # Mock LLM (provided)
├── Dockerfile               # Multi-stage build, < 500 MB, non-root
├── docker-compose.yml       # agent + redis stack
├── requirements.txt         # fastapi, uvicorn, redis, pyjwt, psutil
├── .env.example             # Environment template (31 vars)
├── .env.local               # Dev defaults (gitignored)
├── .dockerignore            # Excludes .env, __pycache__, .git
├── railway.toml             # Railway deploy config
├── render.yaml              # Render deploy config
├── test_app.py              # Integration test script
├── check_production_ready.py # 20-point production readiness checker
└── README.md                # Setup + deploy instructions
```

**Requirements — tất cả đã đạt:**
- [x] All code runs without errors
- [x] Multi-stage Dockerfile (image < 500 MB) — python:3.11-slim, 2 stages
- [x] API key authentication — `X-API-Key` header, verify qua `app/auth.py`
- [x] Rate limiting (20 req/min, configurable) — sliding window, Redis-backed
- [x] Cost guard ($5/day, configurable) — token-based cost estimation
- [x] Health + readiness checks — `GET /health` + `GET /ready`
- [x] Graceful shutdown — SIGTERM handler + `timeout_graceful_shutdown=30`
- [x] Stateless design (Redis) — rate limit + cost guard + session đều dùng Redis
- [x] No hardcoded secrets — tất cả config qua environment variables

**Production Readiness Check: 20/20 ✅**
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

---

### 3. Service Domain Link

✅ File `DEPLOYMENT.md` đã hoàn thành:

```markdown
# Deployment Information

## Public URL
https://day12-agent-production-6443.up.railway.app

## Platform
Railway

## Test Commands

### Health Check
curl -i https://day12-agent-production-6443.up.railway.app/health
# Expected: {"status": "ok", "version": "1.0.0", "environment": "production", ...}

### Readiness Check
curl -i https://day12-agent-production-6443.up.railway.app/ready
# Expected: {"ready": true}

### API Test (with authentication)
curl -X POST https://day12-agent-production-6443.up.railway.app/ask \
  -H "X-API-Key: test-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello AI Agent"}'

### Rate Limiting Test
for i in {1..15}; do
  curl -H "X-API-Key: test-api-key" \
    https://day12-agent-production-6443.up.railway.app/ask \
    -X POST -d '{"question":"test"}' -H "Content-Type: application/json";
done
# Expected: HTTP 429 Too Many Requests after 10 requests

## Environment Variables Set
- PORT: 8000 (auto-injected by Railway)
- AGENT_API_KEY: test-api-key
- ENVIRONMENT: production
- RATE_LIMIT_PER_MINUTE: 10
- DAILY_BUDGET_USD: 1.0
- LOG_LEVEL: INFO
- REDIS_URL: redis://redis:6379/0

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running (health check)](screenshots/running.png)
- [Test results (readiness)](screenshots/test.png)
```

---

##  Pre-Submission Checklist

- [x] Repository is public (or instructor has access)
- [x] `MISSION_ANSWERS.md` completed with all exercises
- [x] `DEPLOYMENT.md` has working public URL
- [x] All source code in `app/` directory
- [x] `README.md` has clear setup instructions
- [x] No `.env` file committed (only `.env.example`)
- [x] No hardcoded secrets in code
- [x] Public URL is accessible and working
- [x] Screenshots included in `screenshots/` folder
- [x] Repository has clear commit history

---

##  Self-Test

Đã kiểm tra deployment (12/06/2026):

```bash
# 1. Health check ✅
curl https://day12-agent-production-6443.up.railway.app/health
# → {"status":"ok","version":"1.0.0","environment":"production","uptime_seconds":...}

# 2. Authentication required ✅
curl -X POST https://day12-agent-production-6443.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'
# → 401 {"detail":"Invalid or missing API key. Include header: X-API-Key: <key>"}

# 3. With API key works ✅
curl -H "X-API-Key: test-api-key" \
  -X POST https://day12-agent-production-6443.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is Docker?"}'
# → 200 {"question":"What is Docker?","answer":"Container là cách đóng gói app...","model":"gpt-4o-mini","timestamp":"..."}

# 4. Rate limiting ✅
for i in {1..15}; do
  curl -s -H "X-API-Key: test-api-key" \
    -X POST https://day12-agent-production-6443.up.railway.app/ask \
    -H "Content-Type: application/json" \
    -d '{"question":"test"}';
done
# → 429 {"detail":"Rate limit exceeded: 10 req/min"} after request 11
```

---

##  Submission

**Submit your GitHub repository URL:**

```
https://github.com/harozx/day12_2A202600874_CaoVanHao
```

**Deadline:** 17/4/2026

---

##  Quick Tips

1. ✅ Test your public URL from a different device
2. ✅ Make sure repository is public or instructor has access
3. ✅ Include screenshots of working deployment
4. ✅ Write clear commit messages
5. ✅ Test all commands in DEPLOYMENT.md work
6. ✅ No secrets in code or commit history

---

##  Need Help?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [CODE_LAB.md](CODE_LAB.md)
- Ask in office hours
- Post in discussion forum

---

**✅ ALL REQUIREMENTS COMPLETED — READY TO SUBMIT! 🎉**
