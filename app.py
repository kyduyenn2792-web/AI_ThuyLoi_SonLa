import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from fpdf import FPDF

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Hệ thống Thủy lợi Sơn La", layout="wide")

# --- 2. HÀM TẠO PDF (BẢN FIX LỖI CHIỀU NGANG) ---
def tao_pdf_bien_ban(tra_loi, cau_hoi, ten_ct):
    # Khởi tạo PDF, tắt chế độ tự động ngắt trang thông minh (thứ gây lỗi không gian)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Nạp font chuẩn
    font_name = "Arial"
    if os.path.exists("arial.ttf"):
        try:
            pdf.add_font("ArialVN", "", "arial.ttf")
            font_name = "ArialVN"
        except: pass
    
    pdf.set_font(font_name, size=12)

    # --- NỘI DUNG BIÊN BẢN ---
    pdf.cell(0, 10, txt="CONG HOA XA HOI CHU NGHIA VIET NAM", ln=True, align='C')
    pdf.cell(0, 10, txt="Doc lap - Tu do - Hanh phuc", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font(font_name, size=14)
    pdf.cell(0, 10, txt="BIEN BAN TRA CUU NGHIEP VU", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font(font_name, size=11)
    
    # SỬ DỤNG LỆNH WRITE THAY CHO MULTI_CELL ĐỂ CHỐNG LỖI HORIZONTAL SPACE
    pdf.write(8, f"Tên công trình: {ten_ct}\n")
    pdf.write(8, f"Câu hỏi tra cứu: {cau_hoi}\n")
    pdf.ln(5)
    
    pdf.write(8, "KẾT QUẢ TRA CỨU TỪ HỆ THỐNG AI:\n")
    pdf.write(8, f"{tra_loi}\n")
    
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # --- PHẦN KÝ TÊN ---
    pdf.write(8, "- Đại diện Chi nhánh Thủy lợi số 5 (Ký, ghi rõ họ tên)\n\n")
    pdf.write(8, "- Đại diện UBND phường/bản (Ký, ghi rõ họ tên)\n\n")
    pdf.write(8, "- Hộ gia đình vi phạm (Ký, ghi rõ họ tên)\n\n")
    pdf.write(8, "- Cán bộ địa bàn (Ký, ghi rõ họ tên)\n\n")
    
    pdf.ln(5)
    pdf.cell(0, 10, txt="Người lập biên bản: ...............................", ln=True, align='R')
    pdf.cell(0, 10, txt="Ngày ..... tháng ..... năm 2026", ln=True, align='R')
    
    # Trả về dữ liệu PDF dưới dạng byte
    return pdf.output(dest='S')

# --- 3. HÀM NẠP DỮ LIỆU (FIX LỖI NAMEERROR) ---
@st.cache_resource
def nap_du_lieu_van_ban():
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

# --- 4. KẾT NỐI HỆ THỐNG ---
if "OPENAI_API_KEY" in st.secrets:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    if "context" not in st.session_state:
        st.session_state.context = nap_du_lieu_van_ban()
else:
    st.error("Chưa có API Key!")
    st.stop()

# --- 5. GIAO DIỆN ---
st.title("🌊 Trợ lý AI Ngành Thủy Lợi (Sơn La)")
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📍 Bản đồ & Thông số")
    try:
        file_excel = [f for f in os.listdir("specs") if f.endswith(".xlsx")][0]
        df = pd.read_excel(os.path.join("specs", file_excel))
        df.columns = df.columns.str.strip()

        col_ten = df.select_dtypes(include=['object']).columns[0]
        col_lat = [c for c in df.columns if 'lat' in c.lower() or 'vĩ' in c.lower()][0]
        col_lon = [c for c in df.columns if 'lon' in c.lower() or 'kinh' in c.lower()][0]

        ten_ct = st.selectbox("Chọn công trình:", df[col_ten].unique())
        row = df[df[col_ten] == ten_ct].iloc[0]
        
        # Hiện mọi thông số trong Excel
        for c in df.columns:
            if c not in [col_lat, col_lon]:
                st.write(f"**{c}:** {row[c]}")
        
        map_url = f"https://www.google.com/maps?q={row[col_lat]},{row[col_lon]}&output=embed&t=k"
        st.components.v1.iframe(map_url, height=400)
    except: st.warning("Đang tải dữ liệu...")

with col2:
    st.header("💬 Hỏi đáp Trợ lý AI")
    hoi = st.text_input("Nhập câu hỏi:")
    if hoi:
        with st.spinner("AI đang trả lời..."):
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Dữ liệu: {st.session_state.context[:3000]}"},
                    {"role": "user", "content": hoi}
                ]
            )
            tra_loi = res.choices[0].message.content
            st.write(tra_loi)
            
            # HIỆN NÚT TẢI PDF
            st.markdown("---")
            pdf_data = tao_pdf_bien_ban(tra_loi, hoi, ten_ct)
            st.download_button("📥 Tải Biên bản PDF", data=pdf_data, file_name="Bien_ban.pdf", mime="application/pdf")