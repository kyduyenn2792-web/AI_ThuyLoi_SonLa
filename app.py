import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from fpdf import FPDF

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Trợ lý Thủy lợi Sơn La", layout="wide")

# --- 2. HÀM TẠO PDF TIẾNG VIỆT ---
def tao_pdf_unicode(tra_loi, cau_hoi, ten_ct):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("arial.ttf"):
        pdf.add_font("ArialVN", "", "arial.ttf")
        font_name = "ArialVN"
    else:
        font_name = "Arial"

    pdf.set_font(font_name, size=14)
    pdf.cell(0, 10, txt="CONG HOA XA HOI CHU NGHIA VIET NAM", ln=True, align='C')
    pdf.set_font(font_name, size=12)
    pdf.cell(0, 10, txt="Doc lap - Tu do - Hanh phuc", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font(font_name, size=16)
    pdf.cell(0, 10, txt="BIEN BAN TRA CUU NGHIEP VU THUY LOI", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font(font_name, size=12)
    pdf.multi_cell(0, 10, txt=f"Cong trinh: {ten_ct}")
    pdf.multi_cell(0, 10, txt=f"Noi dung cau hoi: {cau_hoi}")
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"Ket qua tra cuu:\n\n{tra_loi}")
    return pdf.output(dest='S')

# --- 3. HÀM ĐỌC PDF DỮ LIỆU ---
@st.cache_resource
def doc_pdf_thuy_loi():
    context = ""
    if os.path.exists("data"):
        from pypdf import PdfReader
        for file in os.listdir("data"):
            if file.endswith(".pdf"):
                try:
                    reader = PdfReader(os.path.join("data", file))
                    for page in reader.pages:
                        context += page.extract_text() + "\n"
                except: continue
    return context

# --- 4. HỆ THỐNG & API KEY ---
if "OPENAI_API_KEY" in st.secrets:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    if "context" not in st.session_state:
        st.session_state.context = doc_pdf_thuy_loi()
else:
    st.error("Lỗi: Hãy cấu hình API Key trong mục Secrets!")
    st.stop()

# --- 5. GIAO DIỆN CHÍNH ---
st.title("🌊 Trợ lý AI Ngành Thủy Lợi (Sơn La)")
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📍 Bản đồ Vệ tinh")
    try:
        # Tìm file Excel
        file_excel = [f for f in os.listdir("specs") if f.endswith(".xlsx")][0]
        df = pd.read_excel(os.path.join("specs", file_excel))
        df.columns = df.columns.str.strip()

        # KHỚP CỘT THEO FILE BẠN GỬI
        ten_ct = st.selectbox("Chọn công trình thủy lợi:", df['Tên công trình'].unique())
        row = df[df['Tên công trình'] == ten_ct].iloc[0]
        
        st.success(f"📍 {ten_ct} | Cấp: {row['Cấp công trình']} | Địa điểm: {row['Địa điểm']}")
        
        # Chuyển đổi tọa độ (Vì file của bạn dùng Vĩ độ/Kinh độ tiếng Việt)
        vi_do = row['Vĩ độ']
        kinh_do = row['Kinh độ']
        
        # Nhúng bản đồ
        map_url = f"https://www.google.com/maps?q={vi_do},{kinh_do}&hl=vi&t=k&z=16&output=embed"
        st.components.v1.iframe(map_url, height=500)
    except Exception as e:
        st.warning(f"Đang kiểm tra dữ liệu file Excel... (Lỗi: {e})")

with col2:
    st.header("💬 Hỏi đáp Trợ lý AI")
    hoi = st.text_input("Hỏi về quy trình, định mức, nghị định...")
    if hoi:
        with st.spinner("Đang tra cứu..."):
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Bạn là trợ lý chuyên sâu ngành Thủy Lợi. Dùng dữ liệu này: {st.session_state.context}"},
                    {"role": "user", "content": f"Câu hỏi về {ten_ct}: {hoi}"}
                ]
            )
            tra_loi = res.choices[0].message.content
            st.write(tra_loi)
            st.markdown("---")
            try:
                pdf_data = tao_pdf_unicode(tra_loi, hoi, ten_ct)
                st.download_button("📥 Tải Biên bản PDF", data=pdf_data, file_name=f"Bao_cao_{ten_ct}.pdf", mime="application/pdf")
            except:
                st.info("Nút xuất PDF sẽ sẵn sàng khi bạn up file arial.ttf")