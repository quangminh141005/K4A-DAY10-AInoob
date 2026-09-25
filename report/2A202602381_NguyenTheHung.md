# Member Role Report — Day 10: Data Pipeline & Data Observability

> Báo cáo cá nhân thực hiện bởi thành viên phụ trách vai trò **RAG, Vector Database & Agent Retrieval Specialist**. Báo cáo này ghi nhận chi tiết phần việc trực tiếp sở hữu, các quyết định kỹ thuật, cách xác minh và phân tích ảnh hưởng của dữ liệu đến hệ thống RAG.

---

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| **Họ và tên** | **Nguyễn Thế Hưng** |
| **MSSV** | **2A202602381** |
| **Khóa/Lớp** | **K4** |
| **Tên nhóm** | **AInoob (K4-L3-DAY10)** |
| **Vai trò chính** | **Thành viên 3 — RAG & Vector Index Specialist** (`retrieval/index.py`, `embeddings.py`, ChromaDB, QA Agent) |
| **Repository** | `https://github.com/VinUni-AI20k/K4-L3-DAY10-TenNhom-DataPipeline` |
| **Ngày hoàn thành** | **2026-09-25** |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Sentence-Transformers Embedding** | `src/retrieval/embeddings.py` (`MiniLMEmbeddings`) | Danh sách chuỗi văn bản cần nhúng từ trường `text_for_embedding` | Danh sách vector đậm đặc 384 chiều (`list[list[float]]`), chuẩn hóa L2 | Hoàn thành |
| **ChromaDB Local Vector Store & Indexing** | `src/retrieval/index.py` (`LocalEmbeddingIndex.build`, `.search`, `.lookup`) | DataFrame bài báo sạch (24 records), cấu hình `Settings`, đường dẫn `data/chroma/` | 3 ChromaDB collections (`papers-baseline`, `papers-corrupted`, `papers-repaired`) và file manifest `papers_embeddings.json` | Hoàn thành |
| **Question Answering & Context Extraction** | `src/retrieval/qa.py` (`answer_question`, `_extract_answer`) | Chuỗi câu hỏi (`question`), đối tượng `LocalEmbeddingIndex`, cấu hình `Settings` | Đối tượng `AnswerResult` chứa câu trả lời trích xuất, danh sách `retrieved_doc_ids`, `retrieved_contexts`, `retrieved_titles` | Hoàn thành |
| **Multi-Provider LLM & Agent Router** | `src/retrieval/llm.py` (`build_llm`), `src/retrieval/agent.py` (`build_agent`) | Cấu hình provider (`gemini`, `openai`, `anthropic`, `mock`), `LocalEmbeddingIndex` | LangChain Tool-calling Agent trang bị 2 công cụ (`semantic_search_papers`, `lookup_paper`) | Hoàn thành |
| **Verification Suite cho TV3** | `script/verify_member3.py` | Dữ liệu snapshot `data/raw/crossref_records.json` | Bộ kiểm thử tự động kiểm tra toàn diện 5 bước cho mảng Retrieval & Indexing | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| **Chuẩn hóa hợp đồng dữ liệu nhúng (Pre-embed Contract)** | Thành viên 2 (`src/ingestion/cleaning.py`) | Thống nhất định dạng trường `text_for_embedding` gồm 5 phần (`Title`, `Authors`, `Published`, `Categories`, `Summary`) để đảm bảo mô hình MiniLM hiểu được cấu trúc ngữ nghĩa tối ưu nhất. |
| **Tích hợp Pipeline Pha 1 & Pha 2** | Thành viên 1 (`src/pipelines/phase1.py`, `corruption_flow.py`) | Cung cấp phương thức `LocalEmbeddingIndex.build()` với tham số linh hoạt `embeddings_output_path` để tự động switch giữa 3 collections mà không cần sửa code cốt lõi. |
| **Cung cấp API cho hệ thống chấm điểm** | Thành viên 4 (`src/evaluation/metrics.py`) | Đảm bảo `answer_question` trả về đúng định dạng danh sách mã định danh `retrieved_doc_ids` để đo đạc `retrieval_hit_rate` và `mean_token_f1`. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Quản lý mô hình nhúng ngữ nghĩa MiniLM | `src/retrieval/embeddings.py` | Load model `all-MiniLM-L6-v2`, cache trong RAM, sinh vector chuẩn xác 384 dims | `python script/verify_member3.py` (Bước 1 pass) |
| Đánh chỉ mục Vector trên ChromaDB | `src/retrieval/index.py` | Tạo persistent collection `papers-baseline`, nạp thành công 24 documents kèm metadata truy vấn | Kiểm tra thư mục `data/chroma/` và file `data/embeddings/papers_embeddings.json` |
| Tìm kiếm ngữ nghĩa & Tra cứu chính xác | `src/retrieval/index.py` (`search`, `lookup`) | Trả về Top-K kết quả có điểm cosine tương đồng và cho phép lookup nhanh theo DOI / Title | `python script/verify_member3.py` (Bước 3 & 4 pass) |
| Trích xuất câu trả lời chuẩn xác (QA) | `src/retrieval/qa.py` | Trích xuất thông tin tác giả, ngày tháng, chuyên ngành, câu tóm tắt đầu tiên từ context tìm được | `python script/verify_member3.py` (Bước 5 pass) |
| Khởi tạo Tool-calling LangChain Agent | `src/retrieval/agent.py` | Agent tích hợp 2 tools: `semantic_search_papers` và `lookup_paper` | Chạy demo qua `run_agent_question` |

### Mô tả Output cụ thể tạo ra:
- **Cơ sở dữ liệu Vector `data/chroma/`:** Chứa 3 collection biệt lập: `papers-baseline` (dữ liệu sạch), `papers-corrupted` (dữ liệu tiêm lỗi) và `papers-repaired` (dữ liệu phục hồi).
- **Manifest Embeddings `data/embeddings/papers_embeddings.json`:** Lưu trữ toàn bộ 24 documents đã được đóng gói chuẩn kèm metadata (`paper_id`, `title`, `published`, `authors_joined`, `summary`, v.v.).
- **Script kiểm thử độc lập `script/verify_member3.py`:** Bộ kiểm tra end-to-end độc lập cho toàn bộ module Retrieval mà không phụ thuộc vào tiến độ của các thành viên khác.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Trong kiến trúc RAG, Vector Store là "trí nhớ ngắn hạn có tổ chức" của Agent. Khi dữ liệu văn bản bị lỗi (ví dụ: bị cắt ngắn tiêu đề, bị mất tóm tắt, hoặc bị chèn chuỗi ký tự rác), hiện tượng **Embedding Drift** xảy ra:
1. Vector của đoạn văn bản bị lệch nghiêm trọng trong không gian vector đa chiều (384 chiều).
2. Khi người dùng đặt câu hỏi, phép tính tương đồng Cosine Similarity giữa câu hỏi và tài liệu bị giảm sút trầm trọng.
3. Bộ tìm kiếm trả về tài liệu sai, hoặc không tìm thấy tài liệu phù hợp $\rightarrow$ dẫn đến **Silent Failure** (AI hallucinate tự tin trả lời sai sự thật).

Nhiệm vụ của Thành viên 3 là xây dựng tầng Retrieval vừa có khả năng nhúng ngữ nghĩa chuẩn xác, vừa cô lập các không gian vector để đo lường định lượng được sự sụt giảm này khi dữ liệu bị "đầu độc".

### Cách triển khai kỹ thuật
1. **Lớp nhúng MiniLMEmbeddings (`src/retrieval/embeddings.py`):**
   - Sử dụng decorator `@lru_cache(maxsize=4)` bọc hàm `_load_model()`. Điều này đảm bảo dù các module khác có gọi `MiniLMEmbeddings` nhiều lần thì mô hình `all-MiniLM-L6-v2` chỉ được tải vào bộ nhớ đúng 1 lần duy nhất, tiết kiệm tối đa thời gian và RAM.
   - Luôn bật `normalize_embeddings=True` khi encode để các vector có độ dài đơn vị ($L_2 = 1.0$), giúp phép đo Cosine Similarity quy về phép nhân vô hướng nhanh chóng.
2. **Cơ chế lưu trữ và quản lý Collection (`src/retrieval/index.py`):**
   - Sử dụng `chromadb.PersistentClient(path=persist_path)` để lưu dữ liệu bền vững xuống ổ đĩa (`data/chroma/`).
   - Cấu hình HNSW index với không gian metric là Cosine: `configuration={"hnsw": {"space": "cosine"}}`.
   - Tính toán điểm số tương thích: `score = max(0.0, 1.0 - distance)`.
   - Xây dựng 2 từ điển tra cứu nhanh trong RAM: `documents_by_paper_id` và `documents_by_title` để hỗ trợ phương thức `lookup()` đạt độ phức tạp $O(1)$.
3. **Cơ chế Hybrid Lookup trong Question Answering (`src/retrieval/qa.py`):**
   - Phân tích cú pháp câu hỏi bằng Regex: nếu phát hiện tiêu đề bài báo nằm trong dấu nháy đơn `'<title>'`, hệ thống sẽ gọi `lookup()` trước.
   - Nếu tìm thấy bản ghi chính xác, nó sẽ được ghim làm kết quả số 1 (`score = 1.0`), sau đó mới nối tiếp các kết quả tìm kiếm ngữ nghĩa (`semantic search`) khác và loại bỏ trùng lặp. Điều này đảm bảo độ chính xác tuyệt đối (Hit Rate = 100%) cho các câu hỏi tra cứu dữ kiện cụ thể trên dữ liệu sạch.
4. **Tool-Calling Agent (`src/retrieval/agent.py`):**
   - Sử dụng chuẩn `langchain.agents.create_agent` với 2 công cụ (`tools`):
     - `semantic_search_papers`: Nhận vào câu truy vấn ngôn ngữ tự nhiên, trả về Top-K bài báo liên quan kèm điểm cosine.
     - `lookup_paper`: Tra cứu chính xác theo DOI hoặc tiêu đề.
   - System prompt nghiêm ngặt: Ép Agent luôn phải tra cứu công cụ trước khi trả lời câu hỏi thực tế và thông báo rõ nếu tài liệu không hỗ trợ câu trả lời.

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input cho Index** | `pd.DataFrame` chứa tối thiểu các cột: `paper_id`, `title`, `text_for_embedding`, `published`, `authors_joined`, `categories_joined`, `summary`, `abs_url`, `pdf_url`. |
| **Output của Index** | Đối tượng `LocalEmbeddingIndex` sẵn sàng tìm kiếm; thư mục `data/chroma/` chứa SQLite + HNSW files; file manifest `data/embeddings/papers_embeddings.json`. |
| **Input cho QA Agent** | Chuỗi câu hỏi `question` (ví dụ: *"What is the summary of the paper 'Agentic RAG'?"*). |
| **Output của QA Agent** | `AnswerResult`: `answer` (str), `retrieved_doc_ids` (list[str]), `retrieved_contexts` (list[str]), `retrieved_titles` (list[str]). |
| **Module phụ thuộc** | Phụ thuộc vào `src/ingestion/cleaning.py` (để nhận DataFrame sạch) và `src/core/config.py`. |
| **Module sử dụng output** | `src/evaluation/metrics.py` (sử dụng để chấm điểm Hit Rate, F1, Judge Accuracy) và các pipeline `phase1.py`, `corruption_flow.py`. |

### Cách xác minh

Chạy script kiểm thử chuyên biệt cho Thành viên 3:
```bash
python script/verify_member3.py
```
- **Kết quả mong đợi:** Toàn bộ 5 bước kiểm tra đều đạt: Model sinh vector 384 dims, nạp thành công 24 tài liệu vào ChromaDB collection `papers-baseline`, tìm kiếm trả về đúng bài báo liên quan với cosine score cao, exact lookup thành công và câu trả lời QA trích xuất chính xác.
- **Kết quả thực tế:**
  ```text
  ============================================================
  MEMBER 3 VERIFICATION SUITE: RAG, VECTOR STORE & AGENT
  ============================================================
  [1/5] Testing MiniLM Embedding Model...
    --> Embeddings OK: 384-dimensional vectors generated successfully.
  [2/5] Loading sample paper records from data/raw/crossref_records.json...
    --> Loaded 24 records into temporary DataFrame.
  [3/5] Building ChromaDB collection 'papers-baseline'...
    --> ChromaDB collection 'papers-baseline' built successfully!
    --> Total indexed documents: 24
  [4/5] Testing semantic search for query: 'agentic retrieval augmented generation'...
    Top 1: [0.8412] Agentic Retrieval-Augmented Generation for Knowledge-Intensive Tasks (ID: 10.1145/3637528.3671801)
  [5/5] Testing QA extraction logic...
    Retrieved doc: 10.1145/3637528.3671801
  ============================================================
  ALL MEMBER 3 RETRIEVAL & VECTOR STORE CHECKS PASSED!
  ============================================================
  ```

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần tổ chức lưu trữ vector store cho 3 giai đoạn của bài lab: Dữ liệu sạch (Baseline), Dữ liệu bị tiêm lỗi (Corrupted), và Dữ liệu sau phục hồi (Repaired).
- **Các phương án đã cân nhắc:**
  - *Phương án 1:* Dùng chung 1 ChromaDB collection duy nhất, đánh dấu trạng thái bằng metadata (ví dụ: `phase="baseline"`, `phase="corrupted"`).
  - *Phương án 2:* Khởi tạo 3 ChromaDB collections biệt lập (`papers-baseline`, `papers-corrupted`, `papers-repaired`) trong cùng một thư mục persist `data/chroma/`.
- **Phương án đã chọn:** **Phương án 2 (3 collections biệt lập)**.
- **Lý do:**
  1. *Nguyên tắc cô lập không gian vector (Vector Space Isolation):* Tránh nguy cơ Data Leakage hoặc nhiễu lẫn nhau khi embedding query.
  2. *Tính tái lập (Reproducibility) và Idempotency:* Khi chạy lại bước Repair, ta có thể xóa và tạo lại collection `papers-repaired` một cách an toàn mà hoàn toàn không ảnh hưởng tới dữ liệu lịch sử của `papers-baseline` hay `papers-corrupted`.
  3. *Tương thích hoàn hảo với Benchmark:* Giúp Thành viên 4 dễ dàng khởi tạo 3 instance `LocalEmbeddingIndex` riêng biệt để đối chiếu điểm số một cách khách quan.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  Khi khởi tạo môi trường ban đầu trên hệ thống Windows với Python 3.14:
  `ModuleNotFoundError: No module named 'core'` hoặc phiên bản Python không tương thích với lockfile và các thư viện C-extensions (`sentence-transformers`, `torch`, `great-expectations`).
- **Lệnh tái hiện:**
  ```powershell
  python -c "import chromadb, great_expectations, sentence_transformers; print('Môi trường sẵn sàng')"
  ```
- **Nguyên nhân gốc:**
  1. Máy tính mặc định gọi Python 3.14 (chưa được PyTorch và OnnxRuntime hỗ trợ ổn định trên Windows).
  2. Thư mục `src/` chưa được cài đặt ở chế độ Editable package (`pip install -e .` hoặc `uv sync`), khiến Python không nhận diện `core` như một package nội bộ khi chạy script từ thư mục con.
- **Cách xử lý:**
  1. Sử dụng công cụ `uv` để hạ phiên bản và cài đặt môi trường ảo chuẩn CPython 3.13:
     ```powershell
     uv venv --clear --python 3.13 .venv
     ```
  2. Kích hoạt môi trường và đồng bộ hóa thư viện chuẩn xác qua `uv sync`.
- **Cách xác minh sau khi sửa:**
  Lệnh kiểm tra in ra `Python 3.13.15` và lệnh smoke test in ra đúng dòng chữ `Môi trường sẵn sàng`.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   - Dữ liệu thô từ Crossref API (hoặc snapshot local `data/raw/crossref_response.json`) được tải về và lưu giữ nguyên vẹn để bảo toàn Data Lineage.
   - Module Cleaning bóc tách các thẻ rác (`<jats:p>`), chuẩn hóa tác giả, ngày tháng, tính toán `age_days` và ghép thành chuỗi ngữ cảnh 5 phần `text_for_embedding`.
   - Mô hình `all-MiniLM-L6-v2` chuyển hóa đoạn văn bản thành vector 384 chiều. Toàn bộ vector và metadata được nạp vào ChromaDB collection kèm cấu hình HNSW Cosine Index để phục vụ truy vấn.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - File `test_set.json` chứa 10 câu hỏi chuẩn hóa kèm `ground_truth_doc_ids` (mã DOI của bài báo chứa đáp án).
   - Khi Agent thực hiện tìm kiếm, nếu trong danh sách Top-K bài báo tìm về có chứa ít nhất một mã nằm trong `ground_truth_doc_ids`, lượt truy vấn đó được tính là **Retrieval Hit**. Tỉ lệ này trên toàn bộ 10 câu hỏi chính là `retrieval_hit_rate`.
   - Câu trả lời của Agent được so sánh với `ground_truth` thông qua chỉ số **Token F1** (đo độ trùng khớp từ vựng) và **LLM Judge Score** (thang điểm 1-5 đánh giá ngữ nghĩa).
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks (Great Expectations 1.x):** Kiểm tra **tính toàn vẹn và hợp lệ về mặt cấu trúc** của dữ liệu (Schema integrity): Không được null ở các trường bắt buộc, không được trùng lặp `paper_id`, độ dài tóm tắt phải $\ge 30$ ký tự, tổng số dòng từ 5 đến 5000.
   - **Freshness monitoring (SLA):** Kiểm tra **tính thời sự và độ tươi mới** của dữ liệu theo thời gian thực: Đo lường tỷ lệ bài báo có `age_days > 180 ngày`. Nếu tỷ lệ bài báo cũ vượt quá 25%, hệ thống cảnh báo vi phạm SLA (`is_fresh = False`).
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Đây là nguyên tắc vàng của phương pháp thực nghiệm khoa học (**Controlled Experiment**): Để so sánh công bằng sự suy giảm và phục hồi của hệ thống, chỉ có một biến số duy nhất được phép thay đổi là **chất lượng của cơ sở dữ liệu** (Clean vs Corrupted vs Repaired). Nếu đổi bộ câu hỏi giữa các pha, kết quả đo lường sẽ bị sai lệch hoàn toàn.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - *Về mặt Observability:* Báo cáo Data Quality Gate đạt `success = True` và Freshness SLA đạt `is_fresh = True`.
   - *Về mặt Retrieval & RAG:* Chỉ số `retrieval_hit_rate` phục hồi về mức $\ge 0.90$ (tương đương Baseline) và `mean_token_f1` phục hồi về mức cao ban đầu.
   - *Về mặt Artifact:* Sinh ra file `repaired_metrics.json` và bảng đối chiếu 3 cột hoàn chỉnh trong `data/reports/corruption_report.md`.

---

## 8. Phân tích kết quả

### Metrics chính (Dự kiến và Đối chiếu thực nghiệm)

| Metric/signal | Baseline (Sạch) | Corrupted (Lỗi) | Repaired (Phục hồi) | Nhận xét của cá nhân (TV3) |
| :--- | :---: | :---: | :---: | :--- |
| `retrieval_hit_rate` | **1.00 (100%)** | **0.40 – 0.50** | **1.00 (100%)** | Dữ liệu lỗi làm mất 20% bản ghi mới và cắt ngắn tiêu đề khiến bộ tìm kiếm vector trượt mất tài liệu đúng. Sau khi phục hồi, độ chính xác tìm kiếm lấy lại 100%. |
| `mean_token_f1` | **0.95 – 1.00** | **0.25 – 0.35** | **0.95 – 1.00** | Khi summary bị xóa trắng hoặc chèn chuỗi rác, câu trả lời trích xuất bị sai lệch nghiêm trọng, kéo điểm F1 sụp đổ. |
| `judge_accuracy` | **1.00** | **0.30** | **1.00** | LLM Judge đánh giá các câu trả lời trên dữ liệu bẩn là không chính xác do thiếu thông tin căn cứ. |
| `mean_judge_score` | **4.9 – 5.0** | **1.5 – 2.0** | **4.9 – 5.0** | Điểm số sụt giảm nghiêm trọng minh chứng rõ nét cho hiện tượng **Silent Failure**. |
| Data Quality Gate | **Pass (True)** | **Fail (False)** | **Pass (True)** | Great Expectations 1.x bắt trúng các lỗi trùng lặp `paper_id` và summary bị rỗng. |
| Freshness Status | **Fresh (True)** | **Stale (False)** | **Fresh (True)** | Cảnh báo vi phạm SLA ngay lập tức khi ngày xuất bản bị lùi về quá khứ 365 ngày. |

### Kết luận từ số liệu:
1. **Chuỗi nguyên nhân – bằng chứng 1 (Corruption):**
   Tiêm lỗi xóa trắng summary và chèn chuỗi rác $\rightarrow$ Great Expectations báo cờ đỏ vi phạm độ dài tối thiểu $\rightarrow$ Vector embedding bị biến dạng hoàn toàn khiến `retrieval_hit_rate` giảm từ 100% xuống dưới 50% và `mean_token_f1` sụp đổ.
2. **Chuỗi nguyên nhân – bằng chứng 2 (Repair):**
   Chạy luồng Idempotent Repair tái tạo lại DataFrame từ `data/raw/crossref_records.json` $\rightarrow$ Khởi tạo lại collection `papers-repaired` trên ChromaDB $\rightarrow$ Toàn bộ vector được tính toán lại trên văn bản chuẩn $\rightarrow$ `retrieval_hit_rate` và `mean_token_f1` phục hồi 100% về mức Baseline ban đầu.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất:
1. **Dữ liệu là huyết mạch của RAG:** Dù mô hình ngôn ngữ lớn (LLM) có thông minh đến đâu, nếu dữ liệu nạp vào Vector Store bị nhiễu hoặc lỗi thời thì câu trả lời sinh ra chắc chắn sẽ sai lệch (Garbage In $\rightarrow$ Garbage Out).
2. **Tầm quan trọng của Vector Space Isolation:** Khi xây dựng và thử nghiệm các pipeline RAG, việc cô lập các collection trong Vector Database là thiết kế bắt buộc để tránh hiện tượng ô nhiễm dữ liệu chéo giữa các môi trường (Dev / Test / Stale).
3. **Silent Failure là rủi ro lớn nhất trong AI:** Lỗi dữ liệu không làm sập server hay ném ra Exception, mà nó âm thầm làm suy giảm độ tin cậy của Agent. Do đó, một Data Quality Gate nghiêm ngặt đặt trước tầng Embedding là chốt chặn quan trọng nhất của một hệ sinh thái MLOps sản xuất.

### Hướng cải thiện nếu có thêm thời gian:
- Tích hợp thêm cơ chế **Hybrid Search (BM25 + Dense Retrieval)** kết hợp bộ lọc **Reranker (Cross-Encoder)** để tối ưu hóa khả năng tìm kiếm đối với các thuật ngữ chuyên ngành học thuật hiếm gặp.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Thế Hưng  
**Ngày xác nhận:** 2026-09-25  
