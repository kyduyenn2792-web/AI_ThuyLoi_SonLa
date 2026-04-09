import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from fpdf import FPDF

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Trợ lý Thủy lợi Sơn La", layout="wide")

# --- 2. HÀM TẠO PDF TIẾNG VIỆT ---
def tao_pdf_unicode(tra_loi, cau_hoi):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("arial.ttf"):
        pdf.add_font("ArialVN", "", "arial.ttf")
        font_name = "ArialVN"
    else:
        font_name = "Arial"

    pdf.set_font(font_name, size=14)
    pdf.cell(0, 10, txt="CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", ln=True, align='C')
    pdf.set_font(font_name, size=12)
    pdf.cell(0, 10, txt="Độc lập - Tự do - Hạnh phúc", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font(font_name, size=16)
    pdf.cell(0, 10, txt="BIÊN BẢN TRA CỨU NGHIỆP VỤ THỦY LỢI", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font(font_name, size=12)
    pdf.multi_cell(0, 10, txt=f"Nội dung câu hỏi: {cau_hoi}")
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"Kết quả tra cứu:\n\n{tra_loi}")
    pdf.ln(20)
    pdf.cell(0, 10, txt="Người lập: Trợ lý AI Thủy Lợi Sơn La", ln=True, align='R')
    return pdf.output(dest='S')

# --- 3. HÀM ĐỌC PDF ---
def doc_pdf_thuy_loi():
    context = ""
    if os.path.exists("data"):
        from pypdf import PdfReader
        for file in os.listdir("data"):
            if file.endswith(".pdf"):
                reader = PdfReader(os.path.join("data", file))
                for page in reader.pages:
                    context += page.extract_text() + "\n"
    return context

# --- 4. HỆ THỐNG & API KEY ---
if "OPENAI_API_KEY" in st.secrets:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    if "context" not in st.session_state:
        with st.spinner("Đang nạp dữ liệu..."):
            st.session_state.context = doc_pdf_thuy_loi()
else:
    st.error("Lỗi: Chưa dán API Key vào mục Secrets của Streamlit!")
    st.stop()

# --- 5. GIAO DIỆN CHÍNH ---
st.title("🌊 Trợ lý AI Ngành Thủy Lợi (Sơn La)")
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📍 Bản đồ Vệ tinh")
    try:
        df = pd.read_excel("specs/thong_so_ky_thuat.xlsx")
        ten_ho = st.selectbox("Chọn hồ chứa:", df['Tên hồ'].unique())
        row = df[df['Tên hồ'] == ten_ho].iloc[0]
        st.info(f"Dung tích: {row['Dung tích']} m3")
        map_url = f"https://www.google.com/maps?q={row['lat']},{row['lon']}&hl=vi&t=k&z=15&output=embed"
        st.components.v1.iframe(map_url, height=500)
    except:
        st.warning("Đang tải dữ liệu...")

with col2:
    st.header("💬 Hỏi đáp AI")
    hoi = st.text_input("Nhập câu hỏi tại đây:")
    if hoi:
        with st.spinner("AI đang trả lời..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Bạn là chuyên gia thủy lợi. Dùng dữ liệu này: {st.session_state.context}"},
                    {"role": "user", "content": hoi}
                ]
            )
            tra_loi = response.choices[0].message.content
            st.markdown(tra_loi)
            st.markdown("---")
            try:
                pdf_data = tao_pdf_unicode(tra_loi, hoi)
                st.download_button("📥 Tải Biên bản PDF", data=pdf_data, file_name=f"Bao_cao_{ten_ho}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Lỗi tạo PDF: {e}")