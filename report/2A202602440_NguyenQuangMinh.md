# Member Role Report — Day 10: Data Pipeline & Data Observability

> Báo cáo cá nhân thực hiện bởi thành viên phụ trách vai trò **Data Observability & Benchmark Evaluation**. Báo cáo ghi nhận phần việc trực tiếp sở hữu, các quyết định kỹ thuật, cách kiểm thử và kết quả đối chiếu giữa dữ liệu Baseline, Corrupted và Repaired.

---

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| **Họ và tên** | **Nguyễn Quang Minh** |
| **MSSV** | **2A202602440** |
| **Khóa/Lớp** | **K4** |
| **Tên nhóm** | **AInoob (K4-L3-DAY10)** |
| **Vai trò chính** | **Thành viên 4 — Data Observability & Benchmark Evaluation** (`quality.py`, `testset.py`, `reporting.py`) |
| **Repository** | `https://github.com/VinUni-AI20k/K4-L3-DAY10-TenNhom-DataPipeline` |
| **Ngày hoàn thành** | **2026-09-26** |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Great Expectations Quality Gate** | `src/observability/quality.py` (`run_data_quality_checks`) | DataFrame của từng trạng thái và cấu hình `Settings` | Báo cáo JSON chứa kết quả từng expectation và trạng thái tổng hợp | Hoàn thành |
| **Freshness SLA** | `src/observability/quality.py` (`build_freshness_report`) | Các cột `published`, `age_days`; ngưỡng 180 ngày | Số dòng stale, tỷ lệ stale, khoảng ngày xuất bản và cờ `is_fresh` | Hoàn thành |
| **Benchmark Test Set** | `src/evaluation/testset.py` (`build_test_set`) | Clean DataFrame gồm 24 bài báo | `data/eval/test_set.json` gồm 10 câu hỏi thuộc 4 nhóm nghiệp vụ | Hoàn thành |
| **Markdown Reporting** | `src/observability/reporting.py` | Source summary, evaluation metrics, quality và freshness payload | Báo cáo baseline và bảng đối chiếu Baseline–Corrupted–Repaired | Hoàn thành |
| **Regression Tests** | `tests/test_observability.py` | Dataset snapshot và thư mục tạm của pytest | 4 test kiểm tra quality gate, SLA, test set và Markdown | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| Chuẩn hóa contract báo cáo | Pipeline integration | Các hàm observability trả về dictionary JSON-serializable, có thể truyền trực tiếp vào pipeline và report generator. |
| Đối chiếu dữ liệu lỗi và phục hồi | Corruption/repair flow | Sinh artifact quality và freshness riêng cho Baseline, Corrupted, Repaired để truy vết trạng thái. |
| Cung cấp benchmark cho RAG | Retrieval & evaluation modules | Test set dùng `ground_truth_doc_ids` là DOI, cho phép tính Retrieval Hit Rate thống nhất trên ba trạng thái. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Triển khai GX 1.x bằng Fluent API | `src/observability/quality.py` | Ephemeral context, Pandas Data Source, Data Asset, whole-dataframe Batch Definition và 6 phép kiểm tra thuộc 4 loại expectation bắt buộc | Chạy pytest trong Conda environment `env_vinai_lab` |
| Kiểm tra dữ liệu sạch | `data/quality/baseline_quality_report.json` | `success=true`, 6/6 expectations thành công, 24 dòng | Đọc artifact JSON hoặc chạy lại `run_data_quality_checks` |
| Phát hiện dữ liệu lỗi | `data/quality/corrupted_quality_report.json` | `success=false`, 4/6 expectations thành công; bắt được duplicate ID và summary không đủ độ dài | So sánh với corrupted dataset |
| Xác nhận dữ liệu phục hồi | `data/quality/repaired_quality_report.json` | `success=true`, 6/6 expectations thành công | Đối chiếu với baseline report |
| Theo dõi Freshness SLA | `data/quality/freshness_report.json` | 1/24 dòng stale, tỷ lệ `0.041667`, `is_fresh=true` | So sánh `age_days > 180` với SLA tối đa 25% |
| Sinh test set có thể tái lập | `data/eval/test_set.json` | Đúng 10 câu, đủ `summary`, `authors`, `date`, `categories` | Test xác nhận số lượng, tập loại câu hỏi và ID duy nhất |
| Sinh báo cáo đối chiếu | `data/reports/corruption_report.md` | Bảng 3 cột Baseline, Corrupted, Repaired cho metrics, quality và freshness | Mở artifact Markdown và đối chiếu với các JSON nguồn |

### Các artifact cụ thể

- `data/eval/test_set.json`: 10 câu hỏi benchmark có ID `eval_001` đến `eval_010`.
- `data/quality/baseline_quality_report.json`: kết quả Quality Gate của dữ liệu sạch.
- `data/quality/corrupted_quality_report.json`: kết quả Quality Gate của dữ liệu đã tiêm lỗi.
- `data/quality/repaired_quality_report.json`: kết quả Quality Gate sau phục hồi.
- `data/quality/freshness_report.json`: báo cáo Freshness SLA của baseline.
- `data/quality/corrupted_freshness_report.json` và `repaired_freshness_report.json`: artifact freshness của hai trạng thái còn lại.
- `data/reports/corruption_report.md`: báo cáo Markdown đối chiếu ba trạng thái.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline RAG có thể vẫn chạy bình thường khi dữ liệu bị hỏng. Bản ghi trùng lặp, summary rỗng hoặc dữ liệu quá cũ không nhất thiết gây exception, nhưng có thể làm retrieval và câu trả lời suy giảm âm thầm. Vì vậy, cần một lớp quan sát dữ liệu trước khi dữ liệu được đưa vào vector store, đồng thời cần benchmark cố định để so sánh khách quan giữa các trạng thái.

### Cách triển khai kỹ thuật

1. **Quality Gate theo chuẩn Great Expectations 1.x:**
   - Khởi tạo context tạm thời bằng `gx.get_context(mode="ephemeral")`, không sinh cấu hình GX rác trong repository.
   - Tạo Pandas Data Source, Data Asset và Batch Definition bằng API 1.x:
     ```python
     data_source = context.data_sources.add_pandas(name="papers_source")
     data_asset = data_source.add_dataframe_asset(name="papers_asset")
     batch_definition = data_asset.add_batch_definition_whole_dataframe("papers_batch")
     batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
     ```
   - Chạy 4 loại expectation thiết yếu:
     - `ExpectTableRowCountToBeBetween`: số dòng từ 5 đến 5000.
     - `ExpectColumnValuesToNotBeNull`: áp dụng cho `paper_id`, `title`, `text_for_embedding`.
     - `ExpectColumnValuesToBeUnique`: `paper_id` không được trùng.
     - `ExpectColumnValueLengthsToBeBetween`: `summary` dài tối thiểu 30 ký tự.
   - Chuẩn hóa kết quả GX thành dictionary thuần để dễ ghi JSON và dùng lại trong báo cáo.

2. **Freshness SLA:**
   - Chuyển `age_days` sang numeric an toàn; giá trị thiếu hoặc không parse được được tính là stale để tránh false pass.
   - Một dòng stale khi `age_days > 180`.
   - Dataset đạt SLA khi tỷ lệ stale không vượt quá 25%. Đúng tại ranh giới 25% vẫn được xem là đạt.
   - Báo cáo gồm `latest_published`, `oldest_published`, `stale_rows`, `total_rows`, `stale_ratio`, ngưỡng và `is_fresh`.

3. **Benchmark Test Set:**
   - Kiểm tra schema đầu vào và yêu cầu tối thiểu 4 documents.
   - Sắp xếp theo `paper_id`, chọn 10 vị trí trải đều toàn bộ corpus để kết quả có tính xác định và đại diện hơn việc chỉ lấy 10 dòng đầu.
   - Phân bố câu hỏi: 3 `summary`, 3 `authors`, 2 `date`, 2 `categories`.
   - Mỗi item có đủ `id`, `question_type`, `question`, `ground_truth`, `ground_truth_doc_ids`.
   - Ground truth của summary dùng câu đầu; authors/categories dùng trường joined với fallback về list gốc; date được chuẩn hóa ISO.

4. **Markdown Reporting:**
   - Báo cáo baseline tổng hợp nguồn dữ liệu, evaluation metrics, Quality Gate và Freshness SLA.
   - Báo cáo corruption trình bày một bảng ba cột để nhìn rõ quá trình sạch → lỗi → phục hồi.
   - Các helper định dạng xử lý boolean thành `PASS/FAIL`, float với bốn chữ số thập phân và escape ký tự Markdown.

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input Quality Gate** | `pd.DataFrame`, `Settings`, tên báo cáo. DataFrame cần các cột `paper_id`, `title`, `text_for_embedding`, `summary`. |
| **Output Quality Gate** | Dictionary có `success`, số expectations đạt/không đạt và chi tiết từng check; đồng thời ghi JSON vào `data/quality/`. |
| **Input Freshness** | DataFrame có `age_days`, `published`; ngưỡng từ `settings.freshness_threshold_days`. |
| **Output Freshness** | JSON-compatible dictionary chứa thống kê stale và trạng thái SLA. |
| **Input Test Set** | Clean DataFrame tối thiểu 4 documents với `paper_id`, `title`, `summary`, `published`. |
| **Output Test Set** | Danh sách đúng 10 câu hỏi và file JSON tại đường dẫn cấu hình. |
| **Input Reporting** | Các dictionary source, metrics, quality và freshness. |
| **Output Reporting** | File Markdown baseline hoặc comparison, tự tạo thư mục cha nếu cần. |

### Cách xác minh

Chạy bộ regression test bằng Conda environment của dự án:

```bash
PYTHONPATH=src /home/qminh/miniconda3/bin/conda run --no-capture-output \
  -n env_vinai_lab pytest -q tests/test_observability.py
```

Kết quả thực tế:

```text
....                                                                     [100%]
4 passed in 9.14s
```

Bộ test xác minh bốn hành vi:

1. Clean dataset đạt Quality Gate; dữ liệu có duplicate ID và summary rỗng bị từ chối.
2. Freshness SLA xử lý đúng ranh giới 25% và xem `age_days` bị thiếu là stale.
3. Test set có đúng 10 câu, đủ 4 loại và 10 ID duy nhất.
4. Báo cáo Markdown có đủ bảng đối chiếu Baseline–Corrupted–Repaired.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Great Expectations có thể được dùng theo workflow đầy đủ gồm Suite, Validation Definition và Checkpoint, hoặc dùng Batch trực tiếp để kiểm tra từng expectation.
- **Các phương án đã cân nhắc:**
  - *Phương án 1:* Lưu GX project, expectation suite và checkpoint cố định trên filesystem.
  - *Phương án 2:* Dùng ephemeral context và gọi `batch.validate(expectation)` cho từng phép kiểm tra, sau đó tự chuẩn hóa kết quả thành JSON artifact.
- **Phương án đã chọn:** **Phương án 2**.
- **Lý do:**
  1. Phù hợp yêu cầu lab dùng GX 1.x nhưng không tạo thêm thư mục cấu hình tạm.
  2. Mỗi expectation có kết quả độc lập, giúp nhìn chính xác hàng rào nào thất bại.
  3. Payload đầu ra đơn giản, không làm các module pipeline/reporting phụ thuộc vào class nội bộ của GX.
  4. Dễ kiểm thử trên cả clean và corrupted DataFrame trong cùng một process.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng:** Khi chạy kiểm thử bằng shell mặc định, lệnh `python` và `conda` không tồn tại trong `PATH`; Python hệ thống cũng chưa cài `pandas` và `great_expectations`.
- **Lệnh tái hiện:**
  ```bash
  conda run -n env_vinai_lab python -c "import pandas, great_expectations"
  ```
  trả về `conda: command not found`.
- **Nguyên nhân gốc:** Conda đã được cài tại `/home/qminh/miniconda3`, nhưng shell không nạp script khởi tạo Conda nên binary không nằm trong `PATH`.
- **Cách xử lý:** Gọi Conda bằng đường dẫn tuyệt đối:
  ```bash
  /home/qminh/miniconda3/bin/conda run -n env_vinai_lab python -c \
    "import pandas, great_expectations as gx; print(pandas.__version__, gx.__version__)"
  ```
- **Kết quả xác minh:** Environment chạy Python 3.11.16, pandas 3.0.6 và Great Expectations 1.23.1. Sau đó toàn bộ 4 regression tests đều pass.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến Quality Gate như thế nào?**
   - Snapshot Crossref được lưu tại `data/raw/` để giữ lineage.
   - Cleaning chuẩn hóa schema, loại duplicate ban đầu, tính `age_days`, tạo `summary_chars` và `text_for_embedding`.
   - Clean DataFrame đi qua GX Quality Gate và Freshness SLA trước khi được dùng để xây vector index.

2. **Evaluation set và ground-truth IDs dùng để đo chất lượng như thế nào?**
   - Mỗi câu hỏi có một `ground_truth` và danh sách DOI trong `ground_truth_doc_ids`.
   - Nếu Top-K retrieval chứa DOI đúng, truy vấn được tính là retrieval hit.
   - Câu trả lời được so với ground truth bằng Token F1 và có thể được đánh giá thêm bằng LLM Judge/Ragas.

3. **Quality checks khác Freshness monitoring ở điểm nào?**
   - Quality Gate kiểm tra tính hợp lệ tại cấp schema và giá trị: row count, null, uniqueness, độ dài nội dung.
   - Freshness SLA đo độ cũ theo thời gian. Một dataset có thể fail quality nhưng vẫn pass freshness, hoặc ngược lại.

4. **Vì sao phải dùng cùng một test set cho ba trạng thái?**
   - Giữ biến kiểm soát cố định. Chỉ dữ liệu/index thay đổi, nhờ đó chênh lệch metric phản ánh ảnh hưởng của corruption và repair thay vì độ khó khác nhau của câu hỏi.

5. **Repair được xem là thành công dựa trên artifact nào?**
   - Quality Gate của repaired trở lại `success=true` và 6/6 expectations pass.
   - Freshness SLA vẫn đạt.
   - Các thống kê rows, unique IDs, missing summaries và duplicate IDs trở lại bằng baseline.
   - Khi pipeline evaluation đầy đủ được chạy, retrieval/answer metrics cũng cần trở lại gần baseline.

---

## 8. Phân tích kết quả

### Kết quả thực nghiệm đã xác minh

| Metric/signal | Baseline (Sạch) | Corrupted (Lỗi) | Repaired (Phục hồi) | Nhận xét cá nhân |
| :--- | :---: | :---: | :---: | :--- |
| Số dòng | 24 | 24 | 24 | Corruption xóa một dòng mới nhất rồi thêm một dòng duplicate nên tổng số dòng không đổi. |
| Unique IDs | 24 | 23 | 24 | Quality Gate phát hiện duplicate `paper_id`; repair khôi phục tính duy nhất. |
| Missing summaries | 0 | 2 | 0 | Summary rỗng nằm trên bản ghi được nhân đôi nên có hai dòng thiếu nội dung. |
| Duplicate IDs | 0 | 1 | 0 | Corrupted fail expectation uniqueness; repaired pass trở lại. |
| GX expectations pass | **6/6** | **4/6** | **6/6** | Hai expectation thất bại ở corrupted là uniqueness và độ dài summary. |
| Data Quality Gate | **PASS** | **FAIL** | **PASS** | Quality Gate thể hiện đúng quá trình phát hiện và phục hồi. |
| Freshness stale rows | 1/24 | 1/24 | 1/24 | Cả ba dataset đều có tỷ lệ stale 4.17%. |
| Freshness SLA | **PASS** | **PASS** | **PASS** | 4.17% thấp hơn ngưỡng tối đa 25%; không được ghi sai thành FAIL chỉ vì có một dòng stale. |
| Regression tests | **4/4 pass** | Đã kiểm tra failure path | **4/4 pass** | Kiểm thử chạy thật bằng GX 1.23.1 trong `env_vinai_lab`. |

### Kết luận từ số liệu

1. **Chuỗi nguyên nhân – bằng chứng corruption:**
   Corruption tạo một `paper_id` trùng và hai summary rỗng → expectation uniqueness và minimum length thất bại → Quality Gate chuyển từ PASS xuống FAIL dù pipeline vẫn có thể đọc DataFrame.
2. **Chuỗi nguyên nhân – bằng chứng repair:**
   Rebuild từ raw snapshot → unique IDs trở lại 24, missing summaries và duplicate IDs trở về 0 → toàn bộ 6 expectations pass như baseline.
3. **Diễn giải Freshness chính xác:**
   Dataset có một dòng stale nhưng SLA được định nghĩa trên tỷ lệ. `1/24 = 4.17%`, nhỏ hơn 25%, nên cả ba trạng thái vẫn PASS. Kết quả này cho thấy cần phân biệt “có dữ liệu stale” với “vi phạm SLA”.
4. **Giới hạn metric hiện tại:**
   Các artifact metrics hiện có ghi thống kê dữ liệu (`rows`, `unique_ids`, `missing_summaries`, `duplicate_ids`), chưa chứa kết quả Retrieval Hit Rate hoặc Token F1 từ pipeline RAG hoàn chỉnh. Vì vậy báo cáo không khẳng định các giá trị retrieval chưa được chạy và xác minh.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Đúng phiên bản API là một phần của chất lượng:** Cú pháp GX cũ có thể làm pipeline crash dù logic expectation đúng; Fluent API của GX 1.x cần được xác minh trong chính environment dự án.
2. **Quality và freshness là hai tín hiệu độc lập:** Dữ liệu corrupted trong lần chạy này fail quality nhưng vẫn pass freshness. Report cần phản ánh đúng số liệu, không suy diễn trạng thái mong đợi.
3. **Artifact và regression test làm observability đáng tin cậy:** JSON giúp audit chi tiết; Markdown giúp con người đọc nhanh; pytest giúp đảm bảo các ngưỡng và contract không bị thay đổi ngoài ý muốn.

### Hướng cải thiện nếu có thêm thời gian

- Tích hợp trực tiếp quality, freshness, test-set generation và reporting vào `phase1.py`/`corruption_flow.py` để một lệnh sinh toàn bộ artifact.
- Thêm Data Docs hoặc Validation Definition/Checkpoint nếu chuyển từ lab sang production và cần lưu lịch sử validation dài hạn.
- Bổ sung trend monitoring theo nhiều lần chạy thay vì chỉ snapshot hiện tại.
- Đồng bộ lại `age_days` khi corruption thay đổi `published`, hoặc tiêm lỗi stale cho hơn 25% bản ghi nếu mục tiêu demo là làm Freshness SLA chuyển sang FAIL.
- Chạy evaluation pipeline đầy đủ để bổ sung Retrieval Hit Rate, Token F1, Judge Accuracy và Ragas cho cả ba trạng thái.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc test output để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho metric chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này sử dụng cùng cấu trúc mẫu nhưng nội dung phản ánh phần việc cá nhân của tôi.

**Họ và tên:** Nguyễn Quang Minh  
**Ngày xác nhận:** 2026-09-26  
