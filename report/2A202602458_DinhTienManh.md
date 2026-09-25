# Báo cáo cá nhân - Day 10: Data Pipeline & Data Observability

> Báo cáo này phản ánh phạm vi Data Foundation & Recovery đã triển khai trong repository. Thông tin cá nhân chưa được khai báo trong workspace cần được bổ sung trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---| 
| Họ và tên | `Đinh Tiến Mạnh` |
| MSSV | `2A202602458` |
| Khóa/Lớp | `K4-L3-DAY10` |
| Tên nhóm | `Ainoob` |
| Vai trò chính | `Data Foundation & Recovery` |
| Repository | https://github.com/quangminh141005/K4A-DAY10-AInoob |
| Ngày hoàn thành | `2026-09-25` |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Crossref ingestion | `src/ingestion/crossref.py`: `parse_crossref_payload`, `fetch_source_records`, `load_raw_records` | Crossref REST payload hoặc raw snapshot | `data/raw/crossref_response.json`, `crossref_records.json` | Hoàn thành |
| Data cleaning | `src/ingestion/cleaning.py`: `build_clean_dataframe` | `PaperRecord` hoặc records/DataFrame | Clean DataFrame, clean CSV/JSON | Hoàn thành |
| Corruption and repair | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` | Clean DataFrame và raw records | Corruption log, repaired data, comparison report | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Module được hỗ trợ | Kết quả |
|---|---|---|
| Tích hợp và chạy flow repair | `src/pipelines/corruption_flow.py` | Tạo baseline/corrupted/repaired artifacts và kiểm tra idempotent repair |

## 3. Kết quả theo vai trò

| Nhiệm vụ | File/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Thu thập và parse Crossref | `src/ingestion/crossref.py` | 24 `PaperRecord`; retry lỗi tạm thời và fallback offline | `fetch_source_records()` trả 24 records; mô phỏng lỗi mạng vẫn trả 24 |
| Bảo toàn raw lineage | `data/raw/` | `crossref_response.json` và `crossref_records.json` tồn tại, không rỗng | Kiểm tra file path và kích thước artifact |
| Làm sạch và tạo schema embedding | `src/ingestion/cleaning.py` | 24 rows, `age_days`, joined fields và `text_for_embedding` | Chạy `build_clean_dataframe()` với snapshot |
| Corruption và repair | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` | Sáu lỗi được ghi log; repaired data trở về 24 unique IDs | Chạy `python script/run_corruption_flow.py` hai lần |

Output tiêu biểu: baseline có 24 rows và 24 unique IDs; corrupted có 24 rows nhưng chỉ 23 unique IDs, 2 summary rỗng và 1 duplicate ID; repaired trở lại 24 rows, 24 unique IDs, không summary rỗng và không duplicate.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Dữ liệu Crossref cần được lấy có kiểm soát, lưu nguyên bản để có thể chạy offline, chuẩn hóa trước khi embedding, và phục hồi từ nguồn tin cậy khi một bước downstream làm hỏng dữ liệu.

### Cách triển khai

`parse_crossref_payload()` đọc `message.items`, chuẩn hóa DOI, title, abstract, authors, subjects và ngày Crossref. Summary được unescape và loại HTML/XML tag. `fetch_source_records()` dùng timeout, retry cho `429` và lỗi `5xx`; khi không lấy được dữ liệu thì đọc snapshot local. Records normalized được lưu riêng để các bước sau không phải parse lại raw response.

`build_clean_dataframe()` chuẩn hóa whitespace, loại record thiếu khóa hoặc ngày, deduplicate theo `paper_id`, tính `age_days` và tạo text embedding theo năm phần có nhãn: Title, Authors, Published, Categories, Summary.

Corruption flow tạo sáu lỗi có chủ đích. Repair không sửa trên DataFrame corrupted mà đọc lại `crossref_records.json` rồi chạy cleaning lại. Vì vậy chạy lại flow không tích lũy lỗi và có tính idempotent.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Crossref payload hoặc `data/raw/crossref_records.json`; `run_date` cho cleaning |
| Output | `PaperRecord`, cleaned DataFrame, clean/corrupted/repaired CSV/JSON |
| Module phụ thuộc | `core.config`, `core.utils`, `pandas`, `requests` |
| Module sử dụng output | Pipeline, retrieval/index và observability có thể dùng clean schema |
| Điều kiện lỗi | Network error, HTTP 429/5xx, snapshot thiếu, record thiếu DOI/title/date |

### Cách xác minh

```powershell
$env:PYTHONPATH='src'; .\\.venv\\Scripts\\python.exe script\\run_corruption_flow.py
```

- **Kết quả mong đợi:** Flow tạo baseline, corrupted và repaired artifacts; repaired khôi phục các invariant của baseline.
- **Kết quả thực tế:** `baseline 24/24`, `corrupted 24/23`, `repaired 24/24`; sáu corruption types được ghi log.
- **Artifact/log:** `data/results/corruption_log.json`, `data/results/*_metrics.json`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Repair cần khôi phục dữ liệu mà không phụ thuộc vào bản đã bị corruption.
- **Các phương án:** Sửa trực tiếp các dòng lỗi trong corrupted DataFrame; hoặc đọc lại raw snapshot và chạy lại cleaning.
- **Phương án đã chọn:** Đọc lại `data/raw/crossref_records.json` và gọi `build_clean_dataframe()`.
- **Lý do:** Cách này bảo toàn lineage, tránh lan truyền lỗi, dễ tái lập và chứng minh idempotency; đổi lại cần raw artifact luôn tồn tại.
- **Bằng chứng:** Sau hai lần chạy flow, repaired vẫn có 24 rows, 24 unique IDs, 0 missing summaries và 0 duplicate IDs.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng:** `pytest` ban đầu không chạy vì môi trường chưa có module `pytest`; các module ingestion ban đầu còn `NotImplementedError`.
- **Bước tái hiện:** `$env:PYTHONPATH='src'; .\\.venv\\Scripts\\python.exe -m pytest -q`.
- **Nguyên nhân gốc:** Pytest chưa được cài và các skeleton ingestion/corruption/repair chưa có implementation.
- **Cách xử lý:** Cài `pytest`, triển khai parser/fallback/cleaning, sau đó triển khai corruption flow và repair từ raw snapshot.
- **Xác minh sau khi sửa:** `py_compile`, diagnostics không lỗi, `script/run_corruption_flow.py` chạy exit code 0 và chạy lặp lại thành công.
- **Điều học được:** Cần kiểm tra cả source implementation và artifact contract; một pipeline chỉ đáng tin khi có thể dựng lại output từ raw lineage.

## 7. Hiểu biết về luồng end-to-end

1. Crossref response được lưu vào raw response, parse thành `PaperRecord`, làm sạch thành DataFrame, sau đó `text_for_embedding` được dùng làm document cho embedding/vector index.
2. Evaluation set chứa câu hỏi và ground-truth document IDs; các trạng thái baseline, corrupted và repaired phải dùng cùng set để so sánh retrieval/answer quality công bằng. Trong phạm vi này, evaluation module chưa được triển khai nên chưa có retrieval metrics để báo cáo.
3. Quality checks kiểm tra tính hợp lệ schema và giá trị dữ liệu tại một thời điểm; freshness monitoring đo độ cũ của dữ liệu qua `age_days` và SLA.
4. Dùng cùng test set giúp thay đổi metric phản ánh chất lượng dữ liệu, không phản ánh việc đổi câu hỏi hoặc ground truth.
5. Repair thành công khi repaired artifacts được dựng lại từ raw và các invariant trở về baseline: 24 rows, 24 unique IDs, không summary rỗng và không duplicate IDs. Retrieval/LLM metric phục hồi chưa được kiểm chứng vì evaluation pipeline còn thiếu.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
|---|---:|---:|---:|---|
| Rows | 24 | 24 | 24 | Số dòng corrupted được giữ cùng quy mô để dễ quan sát lỗi nội dung/identity. |
| Unique IDs | 24 | 23 | 24 | Duplicate ID xuất hiện khi corruption và biến mất sau repair. |
| Missing summaries | 0 | 2 | 0 | Summary rỗng là tín hiệu chất lượng rõ ràng. |
| Duplicate IDs | 0 | 1 | 0 | Repair khôi phục uniqueness từ raw. |
| `retrieval_hit_rate` | Chưa có | Chưa có | Chưa có | Evaluation module chưa sinh metric này. |
| `mean_token_f1` | Chưa có | Chưa có | Chưa có | Chưa có evaluation artifact. |
| Quality checks | Chưa có | Chưa có | Chưa có | `quality.py` chưa được triển khai trong phạm vi hiện tại. |
| Freshness status | Chưa có | Chưa có | Chưa có | Chưa có freshness report được sinh bởi observability flow. |

### Kết luận từ số liệu

1. Corruption gồm duplicate, missing summary và thay đổi ngày/title -> unique IDs giảm từ 24 xuống 23, missing summaries tăng từ 0 lên 2 -> ảnh hưởng retrieval/answer chưa thể lượng hóa vì chưa có evaluation metrics.
2. Repair đọc lại raw snapshot -> rows/unique IDs/missing summaries/duplicate IDs trở về `24/24/0/0` -> dữ liệu đã phục hồi; agent metrics chưa được kiểm chứng.

Corruption rõ nhất ở cấp dữ liệu là duplicate ID vì nó trực tiếp phá vỡ document identity: corrupted có 1 duplicate ID trong khi baseline và repaired đều bằng 0.

Kết quả cần lưu ý là corrupted vẫn có 24 rows dù đã drop record, vì bước duplicate bù lại số dòng. Do đó chỉ nhìn row count sẽ bỏ sót lỗi; cần xem đồng thời unique IDs và các trường bắt buộc.

## 9. Điều học được và hướng cải thiện

1. Raw snapshot là nguồn lineage và recovery quan trọng, không nên chỉ lưu dữ liệu đã cleaning.
2. Data quality cần kiểm tra nhiều invariant cùng lúc; row count đơn lẻ không đủ phát hiện duplicate hoặc missing fields.
3. Một lỗi nhỏ trong identity hoặc summary có thể ảnh hưởng vector retrieval dù pipeline vẫn chạy không báo exception.

Nếu có thêm thời gian, cần hoàn thiện `src/observability/quality.py`, `src/evaluation/testset.py` và `src/pipelines/phase1.py`, rồi chạy cùng evaluation set qua baseline/corrupted/repaired để bổ sung hit rate, Token F1, quality và freshness artifacts.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu đã kiểm chứng.
- [x] Có thể giải thích luồng end-to-end ở mức contract và giới hạn hiện tại.
- [x] Kết luận dữ liệu đều đối chiếu với artifact hoặc output chạy thực tế.
- [x] Không ghi nhận thành công cho retrieval/evaluation/observability khi chưa có bằng chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo không sao chép nguyên văn báo cáo nhóm.

**Họ và tên:** `[Bổ sung họ và tên]`
**Ngày xác nhận:** `2026-09-25`
