import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from fpdf import FPDF

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Trợ lý Thủy lợi Sơn La", layout="wide")

# --- 2. HÀM TẠO PDF ---
def tao_pdf_unicode(tra_loi, cau_hoi, ten_ct):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("arial.ttf"):
        pdf.add_font("ArialVN", "", "arial.ttf")
        font_name = "ArialVN"
    else: font_name = "Arial"
    pdf.set_font(font_name, size=12)
    pdf.multi_cell(0, 10, txt=f"CONG TRINH: {ten_ct}\nCAU HOI: {cau_hoi}\n\nTRA LOI:\n{tra_loi}")
    return pdf.output(dest='S')

# --- 3. ĐỌC VĂN BẢN PDF ---
@st.cache_resource
def doc_pdf_thuy_loi():
    context = ""
    if os.path.exists("data"):
        from pypdf import PdfReader
        for file in os.listdir("data"):
            if file.endswith(".pdf"):
                try:
                    reader = PdfReader(os.path.join("data", file))
                    for page in reader.pages: context += page.extract_text() + "\n"
                except: continue
    return context

# --- 4. HỆ THỐNG ---
if "OPENAI_API_KEY" in st.secrets:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    if "context" not in st.session_state:
        st.session_state.context = doc_pdf_thuy_loi()
else:
    st.error("Chưa cấu hình API Key trong Secrets!")
    st.stop()

# --- 5. GIAO DIỆN CHÍNH ---
st.title("🌊 Trợ lý AI Ngành Thủy Lợi (Sơn La)")
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📍 Thông tin & Bản đồ")
    try:
        # Lấy file Excel duy nhất trong specs
        file_excel = [f for f in os.listdir("specs") if f.endswith(".xlsx")][0]
        df = pd.read_excel(os.path.join("specs", file_excel))
        df.columns = df.columns.str.strip()

        # TÌM CỘT TÊN VÀ TỌA ĐỘ (Không quan tâm tên cột là gì)
        col_ten = df.select_dtypes(include=['object']).columns[0]
        col_lat = [c for c in df.columns if 'lat' in c.lower() or 'vĩ' in c.lower()][0]
        col_lon = [c for c in df.columns if 'lon' in c.lower() or 'kinh' in c.lower()][0]

        ten_ct = st.selectbox("Chọn công trình:", df[col_ten].unique())
        row = df[df[col_ten] == ten_ct].iloc[0]
        
        # HIỆN TẤT CẢ THÔNG TIN CÓ TRONG FILE (Tên, Dung tích, Vị trí...)
        for col in df.columns:
            if col not in [col_lat, col_lon]:
                st.write(f"**{col}:** {row[col]}")
        
        # Hiện bản đồ vệ tinh
        lat, lon = row[col_lat], row[col_lon]
        map_url = f"https://www.google.com/maps?q={lat},{lon}&output=embed&t=k"
        st.components.v1.iframe(map_url, height=450)
        
    except Exception as e:
        st.warning("Đang hiển thị danh sách công trình...")

with col2:
    st.header("💬 Hỏi đáp Trợ lý AI")
    hoi = st.text_input("Nhập câu hỏi tra cứu:")
    if hoi:
        with st.spinner("AI đang trả lời..."):
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Dữ liệu: {st.session_state.context}"},
                    {"role": "user", "content": f"Hỏi về {ten_ct if 'ten_ct' in locals() else ''}: {hoi}"}
                ]
            )
            tra_loi = res.choices[0].message.content
            st.write(tra_loi)
            if 'ten_ct' in locals():
                pdf_data = tao_pdf_unicode(tra_loi, hoi, ten_ct)
                st.download_button("📥 Tải Báo cáo PDF", data=pdf_data, file_name=f"Bao_cao.pdf")