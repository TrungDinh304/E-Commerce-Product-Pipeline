## YÊU CẦU DOANH NGHIỆP (Business Case Requirement)

### 1. Mục tiêu tổng thể

Xây dựng một hệ thống lưu trữ, xử lý và truy vấn dữ liệu crawl về **sản phẩm** và **shop** trên một số sàn thương mại điện tử nhằm phục vụ:

* Phát triển **chatbot hỗ trợ khách hàng/giải đáp sản phẩm**
* Phát triển **hệ thống gợi ý sản phẩm** dựa trên đặc trưng sản phẩm và shop

### 2. Yêu cầu chi tiết

#### 2.1. Thu thập và lưu trữ dữ liệu crawl

* Crawl dữ liệu từ website thương mại điện tử (shopee, tiki, lazada, v.v.)
* Dữ liệu bao gồm:

  * Tên sản phẩm, mô tả, giá, danh mục, đánh giá
  * Tên shop, địa điểm, số lượng sản phẩm, mức độ uy tín
* Lưu dữ liệu dạng `.csv`, `.json`, hoặc `.parquet` vào MinIO (giả lập S3)
* Phân chia theo phân vùng hợp lý (theo ngày crawl hoặc theo sàn TMĐT)

#### 2.2. Khả năng truy vấn và phân tích dữ liệu

* Sử dụng Trino để:

  * Truy vấn dữ liệu từ file trực tiếp (không cần ETL vào database)
  * Lọc theo danh mục, shop, mức giá
  * Thống kê phân bố sản phẩm theo danh mục, shop, vùng miền, v.v.

#### 2.3. Chuẩn bị dữ liệu cho mô hình AI

* Trích xuất đặc trưng của sản phẩm (mô tả, giá, rating...) để:

  * Dùng làm dữ liệu train embedding/model NLP cho chatbot
  * Xây hệ thống recommendation theo content-based
* Hệ thống cần cho phép dễ dàng tạo tập dữ liệu huấn luyện (ví dụ: `product_id`, `category`, `description_vector`, `shop_vector`, ...)

#### 2.4. Trực quan hoá dữ liệu (dashboard)

* Tạo dashboard bằng Tableau để:

  * Theo dõi số lượng sản phẩm theo thời gian
  * So sánh số lượng sản phẩm theo danh mục, theo shop
  * Kiểm tra dữ liệu đầu vào cho các mô hình

---

## 3.Kiến trúc dự kiến:



### 1. Ingestion layer – Crawl dữ liệu

| Thành phần          | Mô tả|
| ------------------- | ---|
| `Python + Selenium` | Crawl từ Lazada (cần render DOM)|
| `Python + Requests` | Crawl từ Tiki (API public)|
| `Airflow`           | Lập lịch tự động, chạy định kỳ → trigger crawler|

➡ Kết quả lưu dưới dạng file `.json` hoặc `.csv` → **MinIO**

---

### 2. Datalake – Lưu trữ dữ liệu thô

| Thành phần | Mô tả                                               |
| ---------- | --------------------------------------------------- |
| `MinIO`    | S3-compatible object store, lưu data thô từ crawler |

---

### 3. Processing & Modeling layer – Xử lý, làm sạch, vector hóa

| Thành phần             | Mô tả                                                  |
| ---------------------- | ------------------------------------------------------ |
| `PySpark`              | Làm sạch dữ liệu, chuẩn hóa schema, xử lý volume lớn   |
| `Vectorization`        | Mô tả sản phẩm → embedding (BERT, FastText, TF-IDF...) |
| `Clustering / Scoring` | Gắn label, điểm uy tín shop, vector similarity...      |

➡ Output là các bảng sạch và vector, lưu vào PostgreSQL

---

### 4. Storage layer – Data warehouse + vector DB

| Thành phần            | Vai trò                                                |
| --------------------- | ------------------------------------------------------ |
| `PostgreSQL`          | DWH (staging, curated data), join được với Tableau     |
| (Tùy chọn) `pgvector` | Lưu embedding để tìm kiếm tương đồng (semantic search) |
| (Tùy chọn) `Faiss`    | Nếu cần hiệu năng truy vấn vector cao hơn pgvector     |

---

### 5. Serving layer – API và dashboard đầu ra

| Thành phần           | Mô tả                                                |
| -------------------- | ---------------------------------------------------- |
| `FastAPI / Flask`    | API cho chatbot (semantic search + prompt + LLM)     |
| `Recommendation API` | API gợi ý sản phẩm (vector search + rule-based)      |
| `Tableau / Metabase` | Dashboard trực quan hóa dữ liệu (kết nối PostgreSQL) |

---

## 4. Quá trình làm.
### 1. Phase 1: Crawl data từ tiki và lazada.
- Khó khăn: 
  - 17/5/2025:
    - Không thể truy được api từ lazada -> crawl bằng cách parse HTML.
    - Khi crawl bằng selenium: gặp khó khắn khi liên tục xuất hiện recapcha bằng ảnh (đã research giải pháp để xử lý tự động nhưng hiện chưa tìm thấy/chưa có tool free). -> giải pháp hiện tại (20/5/2025) là: khi gặp recapcha thì pause đến khi nào giải recapcha thì cho hệ thống tiếp tục crawl.

  - 30/5/2025: Có thể là do app có cập nhật nên các css selector bị thay đổi nên phải code lại hết code craw product detail.
  - 1/6/2025: Crawl description lấy inter HTML content chuyển qua md chưa được -> tạm ngưng crawl tìm hiểu Minio concept và lưu trữ thử Bronze Landing Stage.
  - 5/6/2025: sắp bảo vệ đồ án nên tạm drop để all in vào đồ án tốt nghiệp.
  





