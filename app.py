import streamlit as st
import pandas as pd
import os
from openai import OpenAI
from fpdf import FPDF

# --- HÀM TẠO FILE PDF TIẾNG VIỆT CHUẨN ---
def tao_pdf_unicode(tra_loi, cau_hoi):
    pdf = FPDF()
    pdf.add_page()
    
    # Nạp font Arial để viết được tiếng Việt có dấu
    # Đảm bảo bạn đã upload file arial.ttf lên GitHub cùng cấp với app.py
    if os.path.exists("arial.ttf"):
        pdf.add_font("ArialVN", "", "arial.ttf")
        font_name = "ArialVN"
    else:
        font_name = "Arial" # Dự phòng nếu quên chưa up font

    # Tiêu đề báo cáo
    pdf.set_font(font_name, size=16)
    pdf.cell(0, 10, txt="CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", ln=True, align='C')
    pdf.set_font(font_name, size=12)
    pdf.cell(0, 10, txt="Độc lập - Tự do - Hạnh phúc", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font(font_name, size=15)
    pdf.cell(0, 10, txt="BIÊN BẢN TRA CỨU NGHIỆP VỤ THỦY LỢI", ln=True, align='C')
    pdf.ln(10)
    
    # Nội dung câu hỏi
    pdf.set_font(font_name, size=12)
    pdf.multi_cell(0, 10, txt=f"Nội dung câu hỏi: {cau_hoi}")
    pdf.ln(5)
    
    # Nội dung trả lời từ AI
    pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Kẻ đường ngang phân cách
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"Kết quả trả cứu từ hệ thống AI:\n\n{tra_loi}")
    
    # Chân trang
    pdf.ln(20)
    pdf.cell(0, 10, txt="Người lập báo cáo: Trợ lý AI Thủy Lợi Sơn La", ln=True, align='R')
    
    # Xuất file dạng bytes để Streamlit có thể tải về
    return pdf.output(dest='S')

# --- TRONG PHẦN HIỂN THỊ CÂU TRẢ LỜI ---
if "ready" in st.session_state:
    # ... (Sau khi AI trả lời xong và gán vào biến 'tra_loi') ...
    st.markdown("### 🤖 Trả lời từ ChatGPT:")
    st.write(tra_loi)
    
    # NÚT XUẤT FILE PDF XỊN
    try:
        pdf_data = tao_pdf_unicode(tra_loi, hoi)
        st.download_button(
            label="📥 Tải Biên bản Tiếng Việt (PDF)",
            data=pdf_data,
            file_name="bien_ban_thuy_loi.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Lỗi xuất PDF: {e}")

st.set_page_config(page_title="AI Thủy Lợi - ChatGPT Pro", layout="wide")
st.title("🌊 Trợ lý AI Ngành Thủy Lợi (Phiên bản ChatGPT)")

# --- HÀM ĐỌC PDF (Xử lý thông minh) ---
def doc_pdf_thuy_loi():
    context = ""
    folder = './data/'
    if os.path.exists(folder):
        files = [f for f in os.listdir(folder) if f.endswith('.pdf')]
        if not files: return "Chưa có tài liệu PDF nào trong thư mục data."
        for file in files:
            try:
                reader = pypdf.PdfReader(os.path.join(folder, file))
                # Đọc tối đa 15 trang đầu của mỗi file để đảm bảo tốc độ
                for page in reader.pages[:15]:
                    text = page.extract_text()
                    if text: context += f"--- Tài liệu {file} ---\n{text}\n"
            except: continue
    return context

# --- THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.header("🔑 Cấu hình OpenAI")
    key = st.text_input("Dán mã sk-... vào đây:", type="password")
    if st.button("Kích hoạt Trợ lý"):
        if key.startswith("sk-"):
            try:
                st.session_state.client = OpenAI(api_key=key)
                with st.spinner("Đang nạp dữ liệu thủy lợi..."):
                    st.session_state.context = doc_pdf_thuy_loi()
                st.session_state.ready = True
                st.success("✅ ChatGPT đã sẵn sàng phục vụ!")
            except Exception as e:
                st.error(f"Lỗi: {e}")
        else:
            st.error("Vui lòng dán đúng mã API Key bắt đầu bằng 'sk-'")

# --- GIAO DIỆN CHÍNH ---
c1, c2 = st.columns([1, 1])

with c1:
    st.header("📍 Bản đồ Vệ tinh & Địa hình")
    p = "specs/thong_so_ky_thuat.xlsx"
    if os.path.exists(p):
        df = pd.read_excel(p)
        chon = st.selectbox("Chọn hồ chứa/công trình:", df.iloc[:, 0].tolist())
        row = df[df.iloc[:, 0] == chon].iloc[0]
        st.warning(f"📌 {chon} | 💧 Dung tích: {row.get('dung_tich', 'N/A')} m3")
        
        # Link nhúng vệ tinh ép kiểu 3D (t=k)
        lat, lon = row['lat'], row['lon']
        map_url = f"https://www.google.com/maps?q={lat},{lon}&hl=vi&t=k&z=16&output=embed"
        st.components.v1.iframe(map_url, height=500)
    else:
        st.error("Không tìm thấy file Excel trong thư mục specs!")

with c2:
    st.header("💬 Hỏi đáp Trợ lý AI")
    hoi = st.text_input("Bạn cần hỏi gì về quy trình, nghị định...?")
    if hoi:
        if "ready" in st.session_state:
            with st.spinner("AI đang tra cứu văn bản..."):
                try:
                    # Sử dụng model gpt-4o-mini (Rẻ nhất, nhanh nhất và rất thông minh)
                    response = st.session_state.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Bạn là chuyên gia thủy lợi tại Sơn La. Trả lời dựa trên tài liệu được cung cấp. Nếu không có trong tài liệu, hãy dùng kiến thức chuyên môn để tư vấn."},
                            {"role": "user", "content": f"Tài liệu tham khảo:\n{st.session_state.context}\n\nCâu hỏi: {hoi}"}
                        ]
                    )
                    st.markdown("---")
                    st.markdown("### 🤖 Trả lời từ ChatGPT:")
                    st.write(response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Lỗi khi gọi ChatGPT: {e}")
        else:
            st.info("Hãy nhập API Key và nhấn 'Kích hoạt' ở bên trái.")