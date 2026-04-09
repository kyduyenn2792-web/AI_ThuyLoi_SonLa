import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from fpdf import FPDF

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Trợ lý Thủy lợi Sơn La", layout="wide")

# --- 2. HÀM TẠO PDF TIẾNG VIỆT CHUẨN ---
def tao_pdf_unicode(tra_loi, cau_hoi, ten_ct):
    pdf = FPDF()
    pdf.add_page()
    # Nạp font Arial (Phải có file arial.ttf trên GitHub)
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
    pdf.multi_cell(0, 10, txt=f"Công trình: {ten_ct}")
    pdf.multi_cell(0, 10, txt=f"Nội dung câu hỏi: {cau_hoi}")
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"Kết quả tra cứu:\n\n{tra_loi}")
    pdf.ln(20)
    pdf.cell(0, 10, txt="Người lập: Trợ lý AI Thủy Lợi Sơn La", ln=True, align='R')
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
        # Tự động tìm file Excel trong specs
        file_excel = [f for f in os.listdir("specs") if f.endswith(".xlsx")][0]
        df = pd.read_excel(os.path.join("specs", file_excel))
        df.columns = df.columns.str.strip() # Xóa dấu cách thừa ở tên cột

        # TỰ ĐỘNG NHẬN DIỆN CỘT (Dù là 'Tên công trình' hay 'Tên hồ')
        col_name = [c for c in df.columns if any(x in c.lower() for x in ['trình', 'hồ', 'tên'])][0]
        col_cap = [c for c in df.columns if any(x in c.lower() for x in ['tích', 'dung', 'quy mô'])][0]

        ten_ct = st.selectbox("Chọn công trình thủy lợi:", df[col_name].unique())
        row = df[df[col_name] == ten_ct].iloc[0]
        
        st.success(f"📍 {ten_ct} | Thông số: {row[col_cap]}")
        
        # Bản đồ Google Maps vệ tinh
        map_url = f"https://www.google.com/maps?q={row['lat']},{row['lon']}&hl=vi&t=k&z=16&output=embed"
        st.components.v1.iframe(map_url, height=500)
    except Exception as e:
        st.warning(f"Đang kiểm tra dữ liệu kỹ thuật... ({e})")

with col2:
    st.header("💬 Hỏi đáp Trợ lý AI")
    hoi = st.text_input("Hỏi về quy trình, định mức, nghị định...")
    if hoi:
        with st.spinner("Đang tra cứu..."):
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Bạn là trợ lý chuyên sâu ngành Thủy Lợi Sơn La. Dùng dữ liệu này để trả lời ngắn gọn, chính xác: {st.session_state.context}"},
                    {"role": "user", "content": f"Câu hỏi về công trình {ten_ct}: {hoi}"}
                ]
            )
            tra_loi = res.choices[0].message.content
            st.markdown(tra_loi)
            st.markdown("---")
            try:
                pdf_data = tao_pdf_unicode(tra_loi, hoi, ten_ct)
                st.download_button("📥 Tải Biên bản PDF", data=pdf_data, file_name=f"Bao_cao_{ten_ct}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Lỗi tạo PDF: {e}")