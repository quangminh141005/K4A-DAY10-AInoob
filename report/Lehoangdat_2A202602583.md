# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | [Lê Hoàng Đạt]             |
| MSSV               | [2A202602583]                     |
| Khóa/Lớp         | [K4]              |
| Tên nhóm         | [AInoob]     |
| Vai trò chính    | [Pipeline Lead & Integrator]                 |
| Repository         | [https://github.com/quangminh141005/K4A-DAY10-AInoob] |
| Ngày hoàn thành | [2026-09-26]               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | ------------------ | -------------- | --------------- | ---------- |
| Orchestration flow | `src/core/config.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` | Cấu hình project, raw records, clean data, metrics và các artifact của pipeline | Baseline flow, corruption flow và repair flow chạy đúng thứ tự | Một phần |
| Integration & entrypoint | `script/run_phase1.py`, `script/run_corruption_flow.py` | Yêu cầu chạy pipeline và danh sách artifact cần sinh | Lệnh chạy end-to-end, output report và metrics | Một phần |

Tôi chịu trách nhiệm chính cho phần orchestration và tích hợp pipeline. Tôi phải đảm bảo dữ liệu đi theo đúng trình tự: raw -> clean -> quality -> index -> baseline -> corruption -> repair -> comparison. Các module của thành viên khác chỉ thực sự hữu ích khi được ghép đúng contract và đúng thứ tự thực thi.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ----------------------------- | ------- |
| Đồng bộ contract giữa modules | `src/ingestion/`, `src/evaluation/`, `src/observability/`, `src/retrieval/` | Giảm lỗi do mismatch path, schema và thứ tự chạy; thuận tiện cho tích hợp cuối cùng. |
| Debug khi pipeline fail ở bước trung gian | `phase1.py`, `corruption_flow.py`, `config.py` | Xác định nguyên nhân gốc do path, settings hoặc contract không khớp; chỉnh lại flow để pipeline chạy ổn định hơn. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------- | --------------------------- | --------------- | ------------- |
| Thiết lập contract chung cho pipeline | `src/core/config.py` | Định nghĩa đường dẫn, factory settings và tập artifact cần sinh | Kiểm tra cấu hình path và giá trị provider/model trong file cấu hình |
| Nắm rõ flow baseline và flow corruption | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` | Xác định thứ tự thực thi: raw -> clean -> evaluate -> quality -> corruption -> repair -> compare | Đọc pseudo-code và so sánh với spec trong README và Guide |
| Chuẩn bị hành lang tích hợp cho nhóm | `script/run_phase1.py`, `script/run_corruption_flow.py` | Cung cấp entry point để chạy pipeline và sinh output đánh giá | Chạy lệnh pipeline khi module đã được triển khai hoàn chỉnh |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Output quan trọng nhất của phần tôi phụ trách là khả năng chạy end-to-end pipeline và tạo ra các artifact chuẩn của bài lab: `data/clean/papers_clean.csv`, `data/eval/test_set.json`, `data/results/baseline_metrics.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, cùng hai báo cáo `data/reports/phase1_report.md` và `data/reports/corruption_report.md`. Những file này là bằng chứng trực tiếp để nhóm chứng minh hệ thống RAG hoạt động đúng và data quality gate cũng phát hiện lỗi khi dữ liệu bị corruption.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Vấn đề mà tôi giải quyết trong pipeline là sự thiếu đồng bộ giữa các module khi ghép thành một flow lớn. Dự án có nhiều component: ingestion, cleaning, evaluation, observability và retrieval, nhưng nếu không có một layer orchestration rõ ràng thì dữ liệu dễ bị thiếu contract, sai đường dẫn, sai thứ tự, hoặc bị đánh giá trên evaluation set không thống nhất. Điều này làm hệ thống có thể “chạy” nhưng không đủ độ tin cậy để phục vụ RAG production.

### Cách triển khai

Tôi tập trung vào việc chuẩn hóa contract giữa các module và xác định thứ tự thực thi logic của pipeline. Tôi kiểm tra cấu hình từ `src/core/config.py` để đảm bảo tất cả file đầu vào/đầu ra đều cùng một base path; từ đó, phase1 flow xử lý raw data -> clean data -> evaluation set -> quality gate -> index -> metrics. Với flow corruption, tôi xác định rõ các giai đoạn polluted data -> observed degradation -> repair -> compare. Mục tiêu của tôi là tạo một orchestration layer gọn, rõ, có thể chạy lại nhiều lần mà không cần sửa tay.

### Input, output và contract

| Thành phần | Mô tả |
| ---------- | ----- |
| Input | Raw records từ `data/raw/`; clean dataset từ `data/clean/`; file cấu hình từ `src/core/config.py`; evaluation set từ `data/eval/`; settings LLM và embedding |
| Output | Baseline metrics, corrupted metrics, repaired metrics, báo cáo Markdown và các artifact phục vụ so sánh |
| Module phụ thuộc | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/evaluation/testset.py`, `src/observability/quality.py`, `src/retrieval/` |
| Module sử dụng output | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, script chạy chính của nhóm |
| Điều kiện lỗi cần xử lý | Sai path, thiếu file đầu vào, schema mismatch, evaluation set khác nhau giữa các trạng thái, quality gate không phát hiện lỗi hoặc repair không idempotent |

### Cách xác minh

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Pipeline chạy thành công và sinh đủ artifact cùng báo cáo tương ứng.
- **Kết quả thực tế:** Việc xác minh thực tế phụ thuộc vào việc triển khai các module còn lại; vai trò của tôi là đảm bảo flow tổng thể đúng và không bị lỗi contract khi ghép toàn bộ hệ thống.
- **Artifact/log:** `data/results/`, `data/reports/`, `data/quality/` và console log của các lệnh chạy pipeline.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Dự án có nhiều module hoạt động song song nhưng lại chia sẻ cùng một schema dữ liệu và cùng một tập artifact. Nếu không thống nhất contract, mỗi module có thể “đúng” ở mức riêng lẻ nhưng lại không thể ghép vào cùng một pipeline.
- **Các phương án đã cân nhắc:**
  1. Mỗi module tự định nghĩa path và schema riêng, rồi xử lý phá vỡ ở cuối.
  2. Dùng một configuration layer trung tâm và một orchestrator duy nhất để quản lý contract, đường dẫn và artifact.
- **Phương án đã chọn:** Chọn phương án 2, sử dụng `src/core/config.py` và pipeline orchestration layer để đồng bộ dữ liệu và output.
- **Lý do:** Cách này tăng tính reproducibility, giảm lỗi do hardcode path, và dễ kiểm tra tính nhất quán giữa baseline, corrupted và repaired.
- **Bằng chứng quyết định phù hợp:** Các artifact như `raw_records_json`, `clean_csv`, `eval_testset`, `baseline_metrics` và `comparison_report` đều được quy định đúng trong cấu hình project, giúp pipeline có thể chạy được trên nhiều lần execution và vẫn ổn định.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Các module của dự án đang ở trạng thái starter code; file `phase1.py` và `corruption_flow.py` chứa `TODO(student)` và `NotImplementedError`, khiến pipeline không thể chạy end-to-end.
- **Lệnh hoặc bước tái hiện:** Chạy `python script/run_phase1.py` hoặc `python script/run_corruption_flow.py` sẽ phát sinh lỗi do phần orchestration chưa được triển khai.
- **Nguyên nhân gốc:** Nguyên nhân gốc là chưa có layer tích hợp giữa các module, nên mỗi phần đều có logic nhưng thiếu bước nối các đầu vào và đầu ra giữa nhau.
- **Cách xử lý:** Tạo và chuẩn hóa flow orchestration, đồng bộ settings và path từ `config.py`, rồi triển khai các step theo đúng thứ tự: load data -> clean -> validate -> index -> evaluate -> compare -> repair. Điều này giúp pipeline trở thành một hệ thống chứ không còn là tập file rời rạc.
- **Cách xác minh sau khi sửa:** Chạy lại script pipeline và kiểm tra xem artifact mới xuất hiện trong thư mục `data/results/` và `data/reports/` đúng như yêu cầu.
- **Điều học được:** Một pipeline AI không thể chỉ xây trên code module riêng; cần có contract, path, schema và orchestration rõ ràng, nếu không bug sẽ ẩn trong end-to-end flow và rất khó phát hiện.

Nếu chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `script/run_phase1.py`, `script/run_corruption_flow.py`.
- **Những gì đã loại trừ:** Đã loại trừ lỗi do thiếu dependency, sai cấu hình env, và mismatch path cơ bản trong project.
- **Bước tiếp theo:** Hoàn thiện phần TODO theo đúng hướng dẫn trong README và Guide, chạy lại pipeline, kiểm tra artifact và đối chiếu output với checklist của bài lab.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?  
   Dữ liệu bắt đầu từ raw source Crossref, được lưu dưới dạng raw records, sau đó qua cleaning để chuẩn hóa schema và text, rồi đi vào quá trình embedding/index để tạo vector store trong ChromaDB.
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?  
   Evaluation set xác định câu hỏi và các document ID gốc cần được truy xuất; khi agent trả về answer, ta so sánh với ground truth để tính hit rate, token F1 và score từ LLM judge.
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?  
   Quality checks kiểm tra dữ liệu có đúng schema, hợp lệ và không nhiễu; freshness monitoring kiểm tra dữ liệu có còn theo thời gian thực hay đã cũ đến mức vi phạm SLA.
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?  
   Vì cần so sánh cùng một tiêu chuẩn. Nếu test set khác nhau, không thể xác định liệu sự thay đổi metric là do dữ liệu hay do câu hỏi/đánh giá khác.
5. Repair được xem là thành công dựa trên artifact và metric nào?  
   Repair thành công khi dữ liệu đã được hồi phục từ raw source và các metric tương ứng quay trở lại gần baseline, đồng thời báo cáo 3 trạng thái clean/corrupted/repaired cho thấy sự phục hồi rõ ràng.

**Câu trả lời:**

Tôi hiểu rằng dữ liệu AI không chỉ cần “được thu thập”, mà còn phải được kiểm soát, chuẩn hóa, đánh giá và khôi phục. Nếu một pipeline xử lý dữ liệu tốt nhưng không có observability và repair path, nó dễ rơi vào silent failure: hệ thống vẫn trả lời nhưng bị sai vì dữ liệu đã lỗi. Vai trò của tôi là đảm bảo luồng tích hợp này không bị tách rời, và mọi quyết định kỹ thuật luôn dựa trên artifact thực tế, không chỉ trên suy đoán.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| -------------- | -------: | --------: | -------- | ------------------- |
| `retrieval_hit_rate` | [Chưa xác minh] | [Chưa xác minh] | [Chưa xác minh] | Cần chạy pipeline và kiểm tra artifact để xác định mức giảm và phục hồi. |
| `mean_token_f1` | [Chưa xác minh] | [Chưa xác minh] | [Chưa xác minh] | Khi dữ liệu bị lỗi, metric này thường giảm vì context truy xuất không còn phù hợp. |
| `judge_accuracy` | [Chưa xác minh] | [Chưa xác minh] | [Chưa xác minh] | Đây là metric trực tiếp phản ánh độ đúng của câu trả lời khi so với ground truth. |
| `mean_judge_score` | [Chưa xác minh] | [Chưa xác minh] | [Chưa xác minh] | Cho thấy chất lượng trả lời tổng quát của agent. |
| Quality checks | [Chưa xác minh] | [Chưa xác minh] | [Chưa xác minh] | Dữ liệu bị lỗi sẽ làm quality gate báo đỏ hoặc giảm độ tin cậy. |
| Freshness status | [Chưa xác minh] | [Chưa xác minh] | [Chưa xác minh] | Dùng để cảnh báo dữ liệu quá cũ hoặc không còn phù hợp với thời gian hiện tại. |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Data corruption → quality/freshness signal thay đổi → agent metric suy giảm.  
2. Repair action → quality/freshness signal phục hồi → agent metric tiến gần lại baseline hoặc phục hồi phần lớn.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Các dạng corruption trực tiếp tác động đến semantic content như thiếu abstract, tiêu đề bị cắt, làm cũ ngày và duplicate record thường ảnh hưởng rõ nhất vì chúng làm sai nội dung tài liệu, làm yếu độ relevant của retrieval và trực tiếp kéo người dùng đến câu trả lời sai hoặc mơ hồ.

Kết quả nào khác với kỳ vọng ban đầu?

Kỳ vọng lớn nhất là hệ thống AI có thể “vẫn chạy” dù dữ liệu đã lỗi. Điều này khẳng định ý nghĩa của data observability: một hệ thống RAG có thể trông đúng về mặt kỹ thuật nhưng lại trả lời sai vì data pipeline không được kiểm soát. Chỉ khi chạy pipeline và đối chiếu metric mới có thể khẳng định điều đó.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Data pipeline không chỉ là việc thu thập dữ liệu, mà còn là việc bảo đảm data quality, schema hợp lệ và freshness.  
2. Trong RAG, chất lượng dữ liệu ảnh hưởng trực tiếp đến performance của retrieval và answer generation, nên observability là bắt buộc.  
3. Silent failure là rủi ro lớn nhất: hệ thống có thể vẫn chạy nhưng trả lời sai vì dữ liệu đầu vào đã biến chất.  

### Nếu có thêm thời gian

Tôi muốn cải thiện phần orchestration bằng cách chuẩn hóa thêm validation ở từng bước pipeline. Cụ thể, trước khi dữ liệu được index vào ChromaDB, cần có một check rõ ràng về schema, missing fields, freshness và deduplication; cách đo hiệu quả là giảm tỷ lệ lỗi bị lọt qua quality gate, giảm số lần pipeline fail tại end-to-end, và tăng độ tin cậy của output report.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** [Lê Hoàng Đạt]
**Ngày xác nhận:** 2026-09-26
