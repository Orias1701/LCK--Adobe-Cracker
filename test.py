import g4f
import json
import os
from docx import Document

# Đảm bảo thư mục har_and_cookies tồn tại để G4F không lỗi
har_dir = os.path.join(os.path.dirname(os.path.abspath(_file_)), 'har_and_cookies')
if not os.path.exists(har_dir):
    os.makedirs(har_dir, exist_ok=True)


def _parse_qa_blocks(text):
    """Parse Q&A pairs from model text response."""
    qa_pairs = []
    if not text:
        return qa_pairs

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    q, a = None, None

    for line in lines:
        if line.lower().startswith('q:'):
            if q and a:
                qa_pairs.append((q, a))
            q = line.split(':', 1)[1].strip()
            a = None
        elif line.lower().startswith('câu hỏi'):
            if q and a:
                qa_pairs.append((q, a))
            q = line.split(':', 1)[1].strip() if ':' in line else line
            a = None
        elif line.lower().startswith('a:') or line.lower().startswith('trả lời'):
            a = line.split(':', 1)[1].strip() if ':' in line else line
        elif a is not None:
            a = a + ' ' + line

    if q and a:
        qa_pairs.append((q, a))

    return qa_pairs


def generate_qa(prompt_template, input_file, output_file, repeat=1, selected_category=None):
    all_qa = []
    existing_questions = set()
    idx = 1
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            try:
                old_data = json.load(f)
                if isinstance(old_data, list):
                    all_qa = old_data
                    existing_questions = set(item["question"].strip().lower() for item in all_qa if "question" in item)
                    if all_qa:
                        idx = max(item.get("id", 0) for item in all_qa) + 1
            except Exception:
                pass

    doc = Document(input_file)
    all_paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]

    categories = [
        "Đăng ký học tập – tín chỉ – học kỳ",
        "Điều kiện học lại – cải thiện điểm – thi lại",
        "Đánh giá, chấm điểm, xếp loại học lực",
        "Cảnh báo học tập – buộc thôi học",
        "Đồ án, khóa luận, học phần thay thế",
        "Nghỉ học tạm thời – bảo lưu – thôi học",
        "Công nhận tín chỉ – miễn học – chứng chỉ ngoại ngữ & tin học",
        "Chuyển ngành, chuyển trường, học song ngành",
        "Điều kiện tốt nghiệp & xếp hạng bằng"
    ]

    if selected_category is None:
        print("\nChọn category để sinh Q&A:")
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat}")
        while True:
            user_input = input("Nhập số thứ tự hoặc tên category: ").strip()
            if user_input.isdigit() and 1 <= int(user_input) <= len(categories):
                selected_category = categories[int(user_input)-1]
                break
            elif user_input in categories:
                selected_category = user_input
                break
            else:
                print("Không hợp lệ, vui lòng nhập lại.")

    for i in range(repeat):
        print(f"\n--- Category: {selected_category} | Lần sinh Q&A thứ {i+1}/{repeat} ---")
        prompt = prompt_template.format(category=selected_category)
        cat_keywords = [w.strip().lower() for w in selected_category.replace('–', '-').split('-') if w.strip()]
        filtered_paragraphs = []
        for p in all_paragraphs:
            p_lower = p.lower()
            if any(kw in p_lower for kw in cat_keywords):
                filtered_paragraphs.append(p)
        if filtered_paragraphs:
            regulation_text = "\n".join(filtered_paragraphs)
        else:
            regulation_text = "\n".join(all_paragraphs[:20])
        full_prompt = f"""
{prompt}

DỮ LIỆU QUY CHẾ (rút gọn):
{regulation_text}
"""
        # Gọi G4F để sinh Q&A
        try:
            raw_response = g4f.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": full_prompt}]
            )

            # Chuẩn hóa response sang chuỗi
            if isinstance(raw_response, str):
                response_text = raw_response
            elif isinstance(raw_response, dict):
                # Thử lấy nội dung theo cấu trúc ChatCompletion
                response_text = (
                    raw_response.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
            else:
                try:
                    response_text = str(raw_response)
                except Exception:
                    response_text = ""

            print("\n--- RESPONSE THÔ TỪ AI ---\n", response_text, "\n--- HẾT RESPONSE ---\n")

            qa_extracted = _parse_qa_blocks(response_text)
            for q_text, a_text in qa_extracted:
                if q_text.strip().lower() in existing_questions:
                    continue
                all_qa.append({
                    "id": idx,
                    "category": selected_category,
                    "question": q_text,
                    "answer": a_text
                })
                existing_questions.add(q_text.strip().lower())
                idx += 1

            if not qa_extracted:
                print("⚠️  Không trích xuất được Q&A từ phản hồi, bỏ qua lần này.")

        except Exception as e:
            print(f"Lỗi G4F: {e}")

    print(f"\nĐang lưu dữ liệu ra file {output_file} ...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_qa, f, ensure_ascii=False, indent=2)
    print(f"Đã lưu xong! Tổng số cặp Q&A: {len(all_qa)}")

if _name_ == "_main_":
    input_file = "hnmu.docx"
    output_file = "qa_dataset.json"
    repeat = int(input("Nhập số lần lặp lại sinh Q&A: "))
    prompt_template = '''Bạn là chuyên gia học vụ đại học và trợ lý pháp lý giáo dục.

NHIỆM VỤ:
- Đọc và hiểu toàn bộ nội dung tệp dữ liệu: "Quy chế đào tạo trình độ đại học tại Trường Đại học Thủ đô Hà Nội".
- Sinh DUY NHẤT 01 cặp CÂU HỎI – CÂU TRẢ LỜI (Q&A).
- Nội dung Q&A phải dựa DUY NHẤT trên văn bản trong tệp.
- TUYỆT ĐỐI KHÔNG suy diễn, KHÔNG dùng kiến thức bên ngoài, KHÔNG trả lời chung chung.

PHẠM VI:
- CHỈ sinh câu hỏi và câu trả lời cho CATEGORY sau:
    {category}

YÊU CẦU VỀ CÂU HỎI:
- Mang tính THỰC TẾ, giống cách sinh viên thường hỏi trên:
    + Diễn đàn sinh viên
    + Nhóm Facebook
    + Phòng Quản lý đào tạo
- Có thể là:
    + Câu hỏi tình huống cụ thể
    + Câu hỏi dạng "em có được không?"
    + Câu hỏi dạng "nếu … thì sao?"
    + Một nhầm lẫn phổ biến của sinh viên
- Không hỏi theo kiểu máy móc, không nêu trực tiếp "Điều X quy định gì?"
- Không trùng ý với các câu hỏi phổ biến quá chung chung.

YÊU CẦU VỀ CÂU TRẢ LỜI:
- Trả lời ĐÚNG theo quy chế
- Diễn đạt rõ ràng, dễ hiểu, đúng ngôn ngữ học vụ
- Có thể diễn giải lại nhưng KHÔNG làm sai ý văn bản gốc
- Nếu cần, có thể nêu căn cứ Điều/Khoản trong quy chế (không bắt buộc)

ĐỊNH DẠNG OUTPUT (BẮT BUỘC – KHÔNG SINH THÊM NỘI DUNG KHÁC):

Q: <Câu hỏi>
A: <Câu trả lời>

NGÔN NGỮ:
- Tiếng Việt
- Văn phong sinh viên – học vụ – rõ ràng – chính xác

MỤC TIÊU:
- Kết quả dùng trực tiếp cho:
    + Chatbot tư vấn quy chế đào tạo
    + Fine-tune mô hình ngôn ngữ
    + RAG hỏi đáp học vụ
'''
    generate_qa(prompt_template, input_file, output_file, repeat)