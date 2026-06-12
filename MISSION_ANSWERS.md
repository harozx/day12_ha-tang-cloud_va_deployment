# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
Trong file `01-localhost-vs-production/develop/app.py`, có 5 vấn đề chống chỉ định (anti-patterns) sau:
1. **Hardcoded Secrets:** API key (`OPENAI_API_KEY`) và thông tin đăng nhập database (`DATABASE_URL`) được ghi trực tiếp vào mã nguồn. Nếu mã nguồn được tải lên GitHub hoặc chia sẻ, thông tin nhạy cảm này sẽ bị rò rỉ ngay lập tức.
2. **Không có Configuration Management:** Các giá trị cấu hình như `DEBUG = True` và `MAX_TOKENS = 500` được định nghĩa cứng trong mã nguồn thay vì đọc từ môi trường (environment variables).
3. **Sử dụng Print thay vì Structured Logging:** Sử dụng các lệnh `print()` để debug. Điều này làm cho việc thu thập và phân tích log ở môi trường production trở nên khó khăn, và nguy hiểm hơn là nó ghi thẳng các API key nhạy cảm ra log.
4. **Không có Health Check Endpoint:** Server không có các API endpoint báo cáo trạng thái như `/health` hoặc `/ready`. Nếu ứng dụng bị treo hoặc gặp lỗi kết nối cơ sở dữ liệu, hạ tầng cloud (như Railway, Kubernetes) sẽ không phát hiện ra để tự động khởi động lại container.
5. **Cấu hình Host và Port Cố định:** Cố định `host="localhost"` và `port=8000` trong mã nguồn. Khi deploy lên cloud (như Railway, Render), cổng (port) sẽ được hệ thống gán động qua biến môi trường `PORT`, và host phải là `0.0.0.0` để có thể nhận kết nối từ bên ngoài container. Ngoài ra, việc bật `reload=True` khi khởi chạy uvicorn chỉ phù hợp cho phát triển (development), không tối ưu và không an toàn cho production.

### Exercise 1.3: Comparison table

| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| **Config** | Hardcode trong code. | Sử dụng environment variables thông qua file `.env` hoặc hệ thống quản lý biến môi trường của cloud. | Tránh rò rỉ thông tin bảo mật, cho phép thay đổi cấu hình linh hoạt giữa các môi trường mà không cần sửa code. |
| **Health Check** | Không hỗ trợ. | Định nghĩa rõ ràng `/health` (liveness) và `/ready` (readiness) endpoints. | Giúp các công cụ quản lý hạ tầng (Railway, Render, Kubernetes) tự động theo dõi trạng thái, định tuyến traffic và restart container bị lỗi. |
| **Logging** | Dùng `print()`. | Sử dụng structured logging (định dạng JSON). | Thuận tiện cho các bộ thu thập logs (Loki, Datadog) phân tích tự động; không in các thông tin nhạy cảm. |
| **Shutdown** | Tắt đột ngột (crash/kill). | Xử lý sự kiện SIGTERM, kiểm tra in-flight requests và đợi hoàn thành trước khi dừng ứng dụng. | Tránh làm mất hoặc hỏng dữ liệu của người dùng khi ứng dụng thực hiện cập nhật hoặc restart. |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image:** Base image là `python:3.11`. Đây là một bản phân phối Python đầy đủ chạy trên nền Debian, có dung lượng khá lớn (khoảng 1 GB) vì chứa đầy đủ build tools, compilers và packages.
2. **Working directory:** Thư mục làm việc trong container được cấu hình bằng lệnh `WORKDIR /app`. Mọi câu lệnh tiếp theo như `COPY`, `RUN`, `CMD` sẽ được thực thi bên trong thư mục này.
3. **Tại sao COPY requirements.txt trước?** Nhằm tận dụng cơ chế lưu trữ cache theo lớp (layer caching) của Docker. Docker sẽ kiểm tra xem nội dung file `requirements.txt` có thay đổi hay không. Nếu không thay đổi, Docker sẽ tái sử dụng cache cho layer cài đặt thư viện (`RUN pip install...`) thay vì chạy lại từ đầu, giúp giảm đáng kể thời gian build image ở những lần sau.
4. **CMD vs ENTRYPOINT khác nhau thế nào?**
   - `CMD` định nghĩa câu lệnh mặc định sẽ chạy khi container được khởi động. Câu lệnh này có thể dễ dàng bị ghi đè hoàn toàn khi ta truyền tham số ở cuối lệnh `docker run`.
   - `ENTRYPOINT` định nghĩa câu lệnh cố định luôn chạy khi container khởi động. Các tham số truyền thêm từ `docker run` sẽ được append (nối vào) làm đối số cho lệnh của entrypoint chứ không ghi đè nó.

### Exercise 2.3: Image size comparison
Sau khi build thử cả 2 phiên bản image:
- **Develop (Single-stage, base `python:3.11`):** ~1.02 GB
- **Production (Multi-stage, base `python:3.11-slim`):** ~143 MB
- **Difference:** Giảm khoảng **86%** dung lượng của image. Điều này giúp đẩy nhanh tốc độ deployment, tiết kiệm băng thông và giảm bề mặt tấn công bảo mật vì loại bỏ bớt các công cụ không cần thiết.

### Exercise 2.4: Docker Compose stack
- **Services được khởi chạy:**
  1. `agent`: Service chứa mã nguồn FastAPI chạy AI Agent (được scale lên 3 instances).
  2. `redis`: Service làm nhiệm vụ lưu trữ session của cuộc trò chuyện và phục vụ tính năng rate limiting.
  3. `qdrant`: Vector database dùng cho tác vụ RAG (Retrieval-Augmented Generation).
  4. `nginx`: Load balancer, reverse proxy nhận request từ cổng 80/443 của người dùng rồi chuyển tiếp đến các instances của agent.
- **Cách thức giao tiếp:**
  Các service giao tiếp với nhau trong một mạng cầu nội bộ (`internal` bridge network). Nginx lắng nghe ở cổng bên ngoài (port 80) và chuyển tiếp các requests tới các instances của `agent` (port 8000) dựa trên cơ chế Load Balancing. Các instances của `agent` trao đổi với `redis` (port 6379) và `qdrant` (port 6333) bằng cách sử dụng tên service làm hostname (nhờ cơ chế DNS nội bộ của Docker Compose).

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- **Public URL:** `https://day12-production-agent.up.railway.app` *(mẫu)*
- **Cách thực hiện:**
  1. Cài đặt Railway CLI qua npm: `npm i -g @railway/cli`.
  2. Đăng nhập: `railway login`.
  3. Khởi tạo project: `railway init`.
  4. Thiết lập biến môi trường thông qua command line hoặc dashboard:
     `PORT=8000`, `AGENT_API_KEY=my-secret-key`, `REDIS_URL=redis://...`.
  5. Deploy dự án lên cloud: `railway up`.

---

## Part 4: API Security

### Exercise 4.1-4.3: Test results
Dưới đây là kết quả kiểm thử bảo mật API của Agent:
- **Test 1: Gọi API không kèm theo API Key (Không hợp lệ):**
  ```bash
  curl -i -X POST -H "Content-Type: application/json" -d '{"question":"hello"}' http://localhost:8000/ask
  ```
  *Kết quả trả về:* `401 Unauthorized`
  ```json
  {"detail": "Invalid or missing API key. Include header: X-API-Key: <key>"}
  ```

- **Test 2: Gọi API với API Key sai:**
  ```bash
  curl -i -H "X-API-Key: wrong-key" -X POST -H "Content-Type: application/json" -d '{"question":"hello"}' http://localhost:8000/ask
  ```
  *Kết quả trả về:* `401 Unauthorized`
  ```json
  {"detail": "Invalid or missing API key. Include header: X-API-Key: <key>"}
  ```

- **Test 3: Gọi API với API Key đúng:**
  ```bash
  curl -i -H "X-API-Key: test-api-key" -X POST -H "Content-Type: application/json" -d '{"question":"What is Docker?"}' http://localhost:8000/ask
  ```
  *Kết quả trả về:* `200 OK` kèm theo câu trả lời từ Mock LLM.

- **Test 4: Spam liên tiếp để kích hoạt Rate Limiting (Vượt quá 10 req/min):**
  Khi gửi request thứ 11 trong vòng 1 phút, hệ thống sẽ chặn và trả về:
  *Kết quả trả về:* `429 Too Many Requests`
  ```json
  {"detail": "Rate limit exceeded: 10 req/min"}
  ```

### Exercise 4.4: Cost guard implementation
- **Ý tưởng tiếp cận:**
  - Định cấu hình ngân sách tối đa hàng ngày/hàng tháng cho từng người dùng (`daily_budget_usd = 1.0` hoặc `monthly_budget_usd = 10.0`).
  - Mỗi khi nhận một câu hỏi (`question`), ta ước lượng số lượng token đầu vào (input tokens). Trước khi gọi LLM, ứng dụng sẽ kiểm tra chi phí tích lũy của người dùng trong ngày/tháng đó xem có vượt quá giới hạn không. Nếu vượt quá, lập tức ném ra lỗi `402 Payment Required` (hoặc `503 Service Unavailable` đối với budget tổng).
  - Sau khi LLM trả về kết quả, tính toán chính xác số lượng token của cả input và output, quy đổi ra tiền USD thực tế dựa trên giá của model (ví dụ GPT-4o-mini: $0.15/1M input, $0.60/1M output), sau đó cộng dồn vào Redis (ở dạng stateless) bằng lệnh `INCRBYFLOAT` với key dạng `budget:user_id:YYYY-MM-DD`.

---

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
1. **Health checks (`/health` & `/ready`):**
   - Endpoint `/health` (Liveness) trả về `{"status": "ok"}` khi tiến trình FastAPI đang hoạt động tốt.
   - Endpoint `/ready` (Readiness) chỉ trả về `{"ready": true}` sau khi ứng dụng đã khởi chạy thành công (lifespan startup đã chạy xong) và các kết nối phụ thuộc (như Redis) đang hoạt động ổn định. Nó sẽ trả về `503` nếu Redis bị mất kết nối hoặc khi ứng dụng đang trong quá trình shutdown.
2. **Graceful shutdown:**
   - Ứng dụng đăng ký bắt tín hiệu `SIGTERM` và `SIGINT`. Khi nhận được tín hiệu tắt máy, ứng dụng sẽ gán cờ `is_ready = False` ngay lập tức để ngắt traffic mới đổ vào (các request mới tới `/ready` sẽ nhận mã 503).
   - Middleware ghi nhận số lượng request đang được xử lý (`_in_flight_requests`). Tiến trình shutdown trong lifespan sẽ lặp kiểm tra và chờ cho tới khi toàn bộ các requests đang dang dở được phản hồi hết (hoặc hết thời gian timeout tối đa 30s) mới tiến hành đóng kết nối và tắt hẳn container.
3. **Stateless design với Redis:**
   - Để đảm bảo hệ thống có thể mở rộng (scale) ngang bằng cách chạy song song nhiều instances, tất cả trạng thái động (như hội thoại history, rate limiter counter, cost-guard spending) được chuyển từ bộ nhớ trong (in-memory) sang cơ sở dữ liệu dùng chung là Redis. Bất kỳ instance nào được điều phối request bởi Load Balancer đều có thể đọc và ghi dữ liệu của cùng một user.
4. **Load balancing với Nginx:**
   - Sử dụng Nginx làm reverse proxy đứng trước. Khi người dùng gửi request đến cổng 80 của Nginx, cấu hình upstream của Nginx sẽ phân phối request xoay vòng (round-robin) đến danh sách các agent containers (`agent:8000`). Nếu một container gặp sự cố, Nginx sẽ tự động định tuyến lại sang các container còn hoạt động tốt.
