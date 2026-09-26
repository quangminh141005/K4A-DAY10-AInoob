# Group Report — Day 10: Data Pipeline & Data Observability

> Báo cáo tổng hợp phần việc của nhóm AInoob dựa trên bốn báo cáo cá nhân và các artifact hiện có trong repository. Các kết quả chưa có artifact kiểm chứng được ghi rõ là `N/A`.

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | K4-L3-DAY10 |
| Tên nhóm | AInoob |
| Repository | `https://github.com/quangminh141005/K4A-DAY10-AInoob` |
| Ngày hoàn thành báo cáo | 2026-09-26 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Lê Hoàng Đạt | 2A202602583 | Pipeline Lead & Integrator | `src/core/config.py`, pipeline contracts, entrypoints và orchestration |
| 2 | Đinh Tiến Mạnh | 2A202602458 | Data Foundation & Recovery | `src/ingestion/crossref.py`, `cleaning.py`, `corruption.py`, raw/clean/repaired data |
| 3 | Nguyễn Thế Hưng | 2A202602381 | RAG & Vector Index Specialist | `src/retrieval/`, MiniLM embeddings, ChromaDB và QA retrieval |
| 4 | Nguyễn Quang Minh | 2A202602440 | Data Observability & Benchmark Evaluation | `quality.py`, `testset.py`, `reporting.py`, quality/freshness artifacts và tests |

## 2. Tóm tắt kết quả

Nhóm đã xây dựng được phần lớn chuỗi dữ liệu từ snapshot Crossref đến dữ liệu sạch, embedding manifest, ChromaDB, benchmark test set, Quality Gate, corruption và repair. Dataset sạch gồm 24 bài báo với 24 DOI duy nhất. Test set có 10 câu hỏi thuộc bốn nhóm `summary`, `authors`, `date`, `categories`. Quality Gate dùng Great Expectations 1.x đạt 6/6 checks trên baseline, giảm còn 4/6 trên corrupted và phục hồi 6/6 sau repair. Lỗi rõ nhất là duplicate document identity kết hợp summary rỗng: corrupted vẫn có 24 dòng nhưng chỉ còn 23 ID duy nhất, hai summary rỗng và một duplicate ID. Repair đọc lại raw snapshot thay vì sửa trực tiếp dữ liệu lỗi, nhờ đó phục hồi về 24 ID duy nhất, không summary rỗng và không duplicate.

Freshness SLA được đặt ở 180 ngày và chỉ fail khi hơn 25% bản ghi stale. Cả ba trạng thái hiện có 1/24 dòng stale (4,17%), vì vậy đều pass. Artifact retrieval baseline và ChromaDB đã tồn tại, nhưng pipeline evaluation end-to-end chưa sinh `baseline_answers`, các metrics Hit Rate/F1/Judge hoặc `phase1_report.md`. Do đó báo cáo này không dùng các con số RAG dự kiến trong báo cáo cá nhân. Giới hạn quan trọng nhất là `phase1.py` chưa hoàn thiện orchestration và corruption flow hiện mới ghi data-level metrics, chưa re-index/re-evaluate đủ ba trạng thái.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref REST API / offline snapshot
    -> raw response + normalized raw records
    -> cleaning, deduplication, age_days, text_for_embedding
    -> Great Expectations Quality Gate + Freshness SLA
    -> MiniLM embeddings + ChromaDB baseline index
    -> shared 10-question evaluation set
    -> corruption suite (6 deterministic faults)
    -> quality/freshness comparison
    -> repair by rebuilding from trusted raw records
    -> Baseline vs Corrupted vs Repaired Markdown report

Evaluation metrics for all three states
    -> not yet produced by the current end-to-end orchestration
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref response hoặc snapshot | Parse DOI, title, abstract, authors, subjects và dates; retry/fallback | `data/raw/crossref_response.json`, `crossref_records.json` | Đinh Tiến Mạnh |
| Cleaning | Raw records và run date | Normalize, validate required fields, deduplicate, tính `age_days`, ghép embedding text | `data/clean/papers_clean.{csv,json}` | Đinh Tiến Mạnh |
| Embedding/index | Clean DataFrame | MiniLM L2-normalized embeddings; Chroma HNSW/cosine index | `data/embeddings/papers_embeddings.json`, `data/chroma/` | Nguyễn Thế Hưng |
| Evaluation setup | Clean DataFrame | Chọn mẫu xác định và sinh 10 ground-truth questions | `data/eval/test_set.json` | Nguyễn Quang Minh |
| Observability | Baseline/corrupted/repaired DataFrames | GX 1.x expectations và Freshness SLA | `data/quality/*.json` | Nguyễn Quang Minh |
| Corruption/repair | Clean data và trusted raw snapshot | Tiêm 6 lỗi; rebuild clean data từ raw | Corrupted/repaired files, log và data metrics | Đinh Tiến Mạnh |
| Orchestration | Settings và module contracts | Quản lý paths, trình tự chạy và entrypoints | `script/`, `src/pipelines/`, reports | Lê Hoàng Đạt |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| --- | --- |
| `LLM_PROVIDER` | Mặc định `gemini`; evaluation LLM chưa được chạy trong artifact hiện tại |
| `LLM_MODEL` | Mặc định `gemini-2.5-flash` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày; tỷ lệ stale tối đa 25% |
| Random seed | Không dùng; corruption và test-set sampling là deterministic |

Không lưu API key, token hoặc nội dung `.env` trong báo cáo.

### Môi trường và lệnh chạy

Nhóm sử dụng Conda environment `env_vinai_lab`. Trên máy hiện tại, Conda được gọi bằng đường dẫn tuyệt đối:

```bash
PYTHONPATH=src /home/qminh/miniconda3/bin/conda run --no-capture-output \
  -n env_vinai_lab python script/run_corruption_flow.py
```

Kiểm thử observability:

```bash
PYTHONPATH=src /home/qminh/miniconda3/bin/conda run --no-capture-output \
  -n env_vinai_lab pytest -q tests/test_observability.py
```

Kết quả gần nhất của regression suite:

```text
....                                                                     [100%]
4 passed in 9.14s
```

### Kết quả tái hiện

| Luồng/lệnh | Trạng thái | Bằng chứng |
| --- | --- | --- |
| Corruption + repair data flow | Thành công ở mức data artifacts | `data/clean/*`, `data/results/*_metrics.json`, `corruption_log.json` |
| Quality/freshness + test set | Thành công | `data/quality/*.json`, `data/eval/test_set.json`, 4 pytest cases pass |
| Retrieval baseline | Có index/manifest baseline | `data/chroma/`, `data/embeddings/papers_embeddings.json` |
| Baseline pipeline hoàn chỉnh | Chưa hoàn thành | `src/pipelines/phase1.py` còn skeleton; thiếu `phase1_report.md` và answer artifacts |
| Ba-state RAG evaluation | Chưa hoàn thành | Metrics hiện tại chỉ chứa data-level counts, chưa có Hit Rate/F1/Judge |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| --- | --- |
| Source | Crossref REST API với offline snapshot |
| Query | `agentic retrieval augmented generation large language model` |
| Filter | `from-pub-date:<run-date - 180 days>,has-abstract:true` |
| Số record trong snapshot | 24 |
| Cơ chế reliability | Timeout, retry cho HTTP 429/5xx và fallback về snapshot local |

### Raw và clean schema

| Trường | Kiểu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --- | --- | --- | --- | --- |
| `paper_id` | string | Có | DOI/document identity | Normalize; loại dòng rỗng; deduplicate |
| `title` | string | Có | Tiêu đề bài báo | Normalize; loại dòng rỗng |
| `summary` | string | Có cho quality | Abstract đã làm sạch | Normalize; GX yêu cầu tối thiểu 30 ký tự |
| `authors` | list[string] | Không | Danh sách tác giả | Làm sạch, deduplicate; ghép `authors_joined` |
| `categories` | list[string] | Không | Chủ đề Crossref | Làm sạch, deduplicate; ghép `categories_joined` |
| `published` | ISO date | Có | Ngày xuất bản | Parse; loại record không hợp lệ |
| `age_days` | integer | Có | Tuổi dữ liệu tại run date | `(run_date - published).days` |
| `text_for_embedding` | string | Có | Document đưa vào encoder | Ghép năm phần có nhãn |

### Quy tắc cleaning

| Quy tắc | Quality dimension | Kết quả baseline | Cách xác minh |
| --- | --- | ---: | --- |
| Loại dòng thiếu DOI/title/published | Completeness/validity | Clean output còn 24 dòng | `papers_clean.json` và GX report |
| Deduplicate theo `paper_id` | Uniqueness | 24/24 unique IDs | `baseline_metrics.json` |
| Normalize whitespace/list fields | Consistency | Các trường joined sẵn sàng embedding | Clean CSV/JSON |
| Parse ngày và tính `age_days` | Validity/freshness | 1/24 dòng trên 180 ngày | `freshness_report.json` |
| Tạo `text_for_embedding` | Semantic completeness | 24 giá trị không null | GX not-null check |

`text_for_embedding` gồm `Title`, `Authors`, `Published`, `Categories` và `Summary`. Document ID chính là DOI đã chuẩn hóa trong `paper_id`. `age_days` được tính từ ngày chạy cleaning đến `published`.

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| --- | --- |
| Số câu hỏi | 10 |
| `question_type` | `summary`, `authors`, `date`, `categories` |
| Phân bố | 3 summary, 3 authors, 2 date, 2 categories |
| Ground-truth document ID | DOI từ `paper_id`, lưu trong `ground_truth_doc_ids` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection | ChromaDB; baseline collection `papers-baseline` |
| Retrieval `top_k` | 4 |
| LLM provider/model | Mặc định Gemini / `gemini-2.5-flash`; chưa có answer artifact |
| Test set dùng chung | `data/eval/test_set.json` |

Test set phải giữ nguyên giữa baseline, corrupted và repaired để đây là controlled experiment: câu hỏi, đáp án và DOI chuẩn không đổi; chỉ trạng thái dữ liệu/index thay đổi. Nếu đổi test set, không thể biết chênh lệch metric đến từ corruption hay độ khó của câu hỏi.

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| Raw response/records | `data/raw/` | Có | Response và normalized records |
| Cleaned dataset | `data/clean/papers_clean.{csv,json}` | Có | 24 dòng, 24 unique IDs |
| Embedding manifest/index | `data/embeddings/papers_embeddings.json`, `data/chroma/` | Có | Baseline embedding/index artifacts |
| Evaluation set | `data/eval/test_set.json` | Có | 10 câu, đủ 4 loại |
| Baseline metrics | `data/results/baseline_metrics.json` | Có một phần | Chỉ có data-level counts |
| Quality/freshness | `data/quality/` | Có | GX và SLA artifacts cho ba trạng thái |
| Baseline answers | `data/results/baseline_answers.json` | Thiếu | Chưa chạy answer evaluation |
| Baseline report | `data/reports/phase1_report.md` | Thiếu | Phase 1 orchestration chưa hoàn thiện |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| --- | ---: | --- |
| Rows | 24 | Quy mô clean dataset |
| Unique IDs | 24 | Mỗi paper có DOI duy nhất |
| Missing summaries | 0 | Không summary rỗng |
| Duplicate IDs | 0 | Không vi phạm identity |
| `retrieval_hit_rate` | N/A | Chưa có trong artifact metrics |
| `mean_token_f1` | N/A | Chưa có answer artifact |
| `judge_accuracy` | N/A | Chưa chạy LLM judge |
| `mean_judge_score` | N/A | Chưa chạy LLM judge |
| Ragas | N/A | Ragas là optional và chưa chạy |

## 8. Data quality và freshness

### Quality checks

| Check | Dimension | Ngưỡng/kỳ vọng | Baseline | Bằng chứng |
| --- | --- | --- | --- | --- |
| Row count | Volume | 5–5000 | PASS, 24 | `baseline_quality_report.json` |
| Required values | Completeness | `paper_id`, `title`, `text_for_embedding` không null | PASS | Cùng artifact |
| Unique identity | Uniqueness | `paper_id` duy nhất | PASS, 24/24 | Cùng artifact và baseline metrics |
| Summary length | Completeness/usability | Tối thiểu 30 ký tự | PASS | Cùng artifact |

Baseline đạt 6/6 expectation instances. Corrupted đạt 4/6 do vi phạm uniqueness và minimum summary length. Repaired trở lại 6/6.

### Freshness

| Thuộc tính | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
| Latest published | 2026-07-22 | 2026-07-19 | 2026-07-22 |
| Oldest published | 2026-03-28 | 2016-04-20 | 2026-03-28 |
| Stale rows theo `age_days` | 1/24 | 1/24 | 1/24 |
| Stale ratio | 4,17% | 4,17% | 4,17% |
| Threshold | >180 ngày; fail khi >25% stale | Như baseline | Như baseline |
| Trạng thái | PASS | PASS | PASS |

Corrupted có `published` cũ hơn rõ rệt nhưng `age_days` không được cập nhật tương ứng trong corruption function. Freshness implementation đúng theo contract `age_days > 180`, nên artifact vẫn ghi 1 stale row. Đây là giới hạn tích hợp cần sửa, không phải lý do để sửa tay báo cáo thành FAIL.

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record tác động | Signal/kết quả thực tế | Repair |
| --- | --- | ---: | --- | --- |
| Drop latest record | Xóa record có `published` mới nhất | 1 | Mất một document mới; row count sau cùng bị duplicate bù lại | Rebuild từ raw |
| Blank summary | Gán summary thành chuỗi rỗng | 1 gốc, 2 sau duplicate | Summary-length expectation fail; missing summaries = 2 | Rebuild từ raw |
| Inject text noise | Thêm `CORRUPTED_NOISE` vào embedding text | 1 | Nội dung embedding bị biến đổi; chưa có RAG metric định lượng | Rebuild text từ raw |
| Truncate title | Cắt title còn 12 ký tự | 1 | Nội dung định danh suy giảm; chưa có RAG metric | Rebuild từ raw |
| Stale published date | Lùi `published` 3650 ngày | 1 | Oldest date thành 2016-04-07; `age_days` chưa sync | Rebuild từ raw |
| Duplicate record | Nhân đôi dòng đầu | 1 | Unique IDs 24→23; duplicate IDs 0→1 | Rebuild và deduplicate từ raw |

Corruption log nằm tại `data/results/corruption_log.json`, có đủ sáu loại và count cho từng lỗi. Repair không vá trực tiếp corrupted DataFrame. Flow đọc lại `data/raw/crossref_records.json` rồi chạy `build_clean_dataframe()` với cùng logic cleaning. Vì nguồn phục hồi là snapshot tin cậy, chạy lặp lại không tích lũy corruption và giữ tính idempotent.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi | Mức phục hồi | Nhận xét |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Rows | 24 | 24 | 24 | 0 | 100% | Row count đơn lẻ không phát hiện corruption |
| Unique IDs | 24 | 23 | 24 | -1 | 100% | Identity được phục hồi hoàn toàn |
| Missing summaries | 0 | 2 | 0 | +2 | 100% | Repaired trở về baseline |
| Duplicate IDs | 0 | 1 | 0 | +1 | 100% | Repaired trở về baseline |
| GX checks passed | 6/6 | 4/6 | 6/6 | -2 checks | 100% | PASS → FAIL → PASS |
| Freshness stale ratio | 4,17% | 4,17% | 4,17% | 0 | Không áp dụng | Cả ba đều dưới SLA 25% |
| `retrieval_hit_rate` | N/A | N/A | N/A | N/A | N/A | Chưa có artifact đánh giá |
| `mean_token_f1` | N/A | N/A | N/A | N/A | N/A | Chưa có artifact đánh giá |
| `judge_accuracy` | N/A | N/A | N/A | N/A | N/A | Chưa chạy judge |
| `mean_judge_score` | N/A | N/A | N/A | N/A | N/A | Chưa chạy judge |

Hai kết luận có bằng chứng:

1. Blank summary + duplicate record → missing summaries tăng 0→2 và unique IDs giảm 24→23 → hai GX expectations fail. Ảnh hưởng đến retrieval/answer chưa thể kết luận định lượng vì chưa có metrics tương ứng.
2. Rebuild từ trusted raw snapshot → missing summaries và duplicate IDs trở về 0, unique IDs trở về 24 → Quality Gate phục hồi 4/6→6/6. Agent metric recovery vẫn cần chạy evaluation pipeline để kiểm chứng.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Corruption lùi `published` 3650 ngày nhưng Freshness SLA của corrupted vẫn giống baseline.
- **Nguyên nhân:** Freshness đo theo `age_days`, trong khi corruption chỉ thay đổi `published` mà không tính lại `age_days`.
- **Cách nhóm xử lý ở bước báo cáo:** Giữ nguyên kết quả artifact (PASS ở 4,17%) và ghi rõ mismatch contract, không tuyên bố sai rằng corrupted freshness đã fail.
- **Cách khắc phục đề xuất:** Sau mọi mutation liên quan ngày, tính lại `age_days` từ một `run_date` cố định; nếu mục tiêu test SLA fail thì stale hóa hơn 25% số dòng.
- **Cách xác minh:** Chạy lại freshness report và kiểm tra `stale_rows / total_rows > 0.25` dẫn đến `is_fresh=false`.

Một blocker tích hợp khác là `src/pipelines/phase1.py` chưa triển khai, vì vậy baseline evaluation, answer artifacts và phase-1 Markdown report chưa được sinh end-to-end.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| --- | --- | --- |
| `phase1.py` còn skeleton | Không chạy được baseline E2E | Hoàn thiện orchestration; chạy script và kiểm tra `phase1_report.md` |
| Corruption flow chưa re-index/re-evaluate | Không định lượng ảnh hưởng lên RAG | Build ba collections và chạy cùng `test_set.json` |
| Metrics JSON chỉ có data counts | Thiếu Hit Rate/F1/Judge | Gọi `evaluate_pipeline` cho ba trạng thái và ghi answer files |
| `published` và `age_days` có thể lệch sau corruption | Freshness không phản ánh mutation ngày | Tính lại derived columns và thêm regression test |
| Chỉ có baseline embedding manifest | Thiếu corrupted/repaired embedding artifacts | Sinh hai manifest còn lại và xác minh collection isolation |
| Báo cáo cá nhân cũ có số liệu dự kiến | Có thể gây hiểu nhầm | Luôn ưu tiên artifact hiện tại và gắn nhãn dự kiến/N/A rõ ràng |
| Ragas chưa chạy | Thiếu semantic evaluation mở rộng | Bật `RUN_RAGAS=1` trong môi trường có credentials và lưu output |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository đã được tổng hợp từ báo cáo cá nhân.
- [x] Phân công khớp với module và artifact hiện tại.
- [x] Corruption/repair và observability tests có bằng chứng chạy thực tế.
- [x] Test set chung đã được sinh tại `data/eval/test_set.json`.
- [x] Data-level metrics khớp với `data/results/*.json`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn artifact được kiểm tra trong repository.
- [x] Bốn thành viên đều có báo cáo cá nhân trong `report/`.
- [x] Không đưa secret vào báo cáo.
- [ ] Baseline pipeline end-to-end và ba-state RAG evaluation cần hoàn thiện trước khi nộp cuối.
- [ ] Cần sinh `data/reports/phase1_report.md` và các answer/metric artifacts còn thiếu.
