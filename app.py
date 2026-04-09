import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from fpdf import FPDF

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Trợ lý Thủy lợi Sơn La", layout="wide")

# --- HÀM TẠO PDF TIẾNG VIỆT ---
def tao_pdf_unicode(tra_loi, cau_hoi):
    pdf = FPDF()
    pdf.add_page()
    
    # Kiểm tra file font arial.ttf (Phải có file này trên GitHub mới hiện tiếng Việt chuẩn)
    if os.path.exists("arial.ttf"):
        pdf.add_font("ArialVN", "", "arial.ttf")
        font_name = "ArialVN"
    else:
        font_name = "Arial"

    # Quốc hiệu
    pdf.set_font(font_name, size=14)
    pdf.cell(0, 10, txt="CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", ln=True, align='C')
    pdf.set_font(font_name, size=12)
    pdf.cell(0, 10, txt="Độc lập - Tự do - Hạnh phúc", ln=True, align='C')
    pdf.ln(10)
    
    # Tiêu đề biên bản
    pdf.set_font(font_name, size=16)
    pdf.cell(0, 10, txt="BIÊN BẢN TRA CỨU NGHIỆP VỤ THỦY LỢI", ln=True, align='C')
    pdf.ln(10)
    
    # Nội dung câu hỏi
    pdf.set_font(font_name, size=12)
    pdf.multi_cell(0, 10, txt=f"Nội dung câu hỏi: {cau_hoi}")
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Kết quả AI
    pdf.multi_cell(0, 10, txt=f"Kết quả tra cứu từ hệ thống AI:\n\n{tra_loi}")
    
    pdf.ln(20)
    pdf.cell(0, 10, txt="Người lập: Trợ lý AI Thủy Lợi Sơn La", ln=True, align='R')
    
    return pdf.output(dest='S')

# --- HÀM ĐỌC DỮ LIỆU PDF ---
def doc_pdf_thuy_loi():
    context = ""
    data_path = "data"
    if os.path.exists(data_path):
        from pypdf import PdfReader
        for file in os.listdir(data_path):
            if file.endswith(".pdf"):
                reader = PdfReader(os.path.join(data_path, file))
                for page in reader.pages:
                    context += page.extract_text() + "\n"
    return context

# --- GIAO DIỆN THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.header("🔑 Hệ Thống")
    # Lấy Key tự động từ Streamlit Cloud Secrets
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.session_state.client = OpenAI(api_key=api_key)
        st.success("Hệ thống đã sẵn sàng")
        
        if "context" not in st.session_state:
            with st.spinner("Đang nạp dữ liệu PDF..."):
                st.session_state.context = doc_pdf_thuy_loi()
    else:
        st.error("Thiếu API Key trong Secrets!")
        st.stop()

# --- GIAO DIỆN CHÍNH ---
st.title("🌊 Trợ lý AI Ngành Thủy Lợi (Sơn La)")

col1, col2 = st.columns([1, 1])

with col1:
    st.header("📍 Bản đồ Vệ tinh & Địa hình")
    try:
        df = pd.read_excel("specs/thong_so_ky_thuat.xlsx")
        ten_ho = st.selectbox("Chọn hồ chứa/công trình:", df['Tên hồ'].unique())
        row = df[df['Tên hồ'] == ten_ho].iloc[0]
        
        st.info(f"📍 {ten_ho} | Dung tích: {row['Dung tích']} m3")
        
        lat, lon = row['lat'], row['lon']
        map_url = f"https://www.google.com/maps?q={lat},{lon}&hl=vi&t=k&z=15&output=embed"
        st.components.v1.iframe(map_url, height=500)
    except:
        st.warning("Đang tải dữ liệu bản đồ...")

with col2:
    st.header("💬 Hỏi đáp Trợ lý AI")
    hoi = st.text_input("Bạn cần hỏi gì về quy trình, nghị định...?")
    
    if hoi:
        with st.spinner("AI đang tra cứu văn bản..."):
            response = st.session_state.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Bạn là chuyên gia thủy lợi Sơn La. Hãy dùng dữ liệu sau để trả lời: {st.session_state.context}"},
                    {"role": "user", "content": hoi}
                ]
            )
            tra_loi = response.choices[0].message.content
            st.markdown("### 🤖 Trả lời:")
            st.write(tra_loi)
            
            st.markdown("---")
            # Nút xuất PDF
            try:
                pdf_bytes = tao_pdf_unicode(tra_loi, hoi)
                st.download_button(
                    label="📥 Tải Biên bản Báo cáo (PDF)",
                    data=pdf_bytes,
                    file_name=f"Bao_cao_{ten_ho}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error("Lỗi tạo PDF: Đảm bảo bạn đã upload file arial.ttf lên GitHub")