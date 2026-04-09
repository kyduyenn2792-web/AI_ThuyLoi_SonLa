import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from fpdf import FPDF

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Hệ thống Thủy lợi Sơn La AI", layout="wide")

# --- 2. HÀM TẠO BIÊN BẢN PDF TIẾNG VIỆT GỬI LÃNH ĐẠO ---
def tao_pdf_bien_ban(tra_loi, cau_hoi, thong_tin_ct):
    # Khởi tạo PDF với lề rộng 10mm mỗi bên để tránh lỗi không gian
    pdf = FPDF(unit='mm', format='A4')
    pdf.set_margins(15, 15, 15) 
    pdf.add_page()
    
    # Nạp font chuẩn
    font_name = "Arial"
    try:
        if os.path.exists("arial.ttf"):
            pdf.add_font("ArialVN", "", "arial.ttf")
            font_name = "ArialVN"
    except: pass

    pdf.set_font(font_name, size=12)

    # --- NỘI DUNG CHÍNH (Dùng ln=True và multi_cell 0 để an toàn) ---
    pdf.cell(0, 10, txt="CONG HOA XA HOI CHU NGHIA VIET NAM", ln=True, align='C')
    pdf.cell(0, 10, txt="Doc lap - Tu do - Hanh phuc", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font(font_name, size=14)
    pdf.cell(0, 10, txt="BIEN BAN TRA CUU NGHIEP VU THUY LOI", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font(font_name, size=11)
    # Lấy tên công trình, nếu không có thì ghi chung chung
    ten_hồ = thong_tin_ct.get('ten', 'Cong trinh Thuy loi')
    
    # Sử dụng multi_cell(0, ...) để nội dung tự xuống dòng, không bao giờ lấn lề
    pdf.multi_cell(0, 8, txt=f"Cong trinh: {ten_hồ}")
    pdf.multi_cell(0, 8, txt=f"Cau hoi: {cau_hoi}")
    pdf.ln(5)
    
    pdf.multi_cell(0, 8, txt=f"KET QUA TRA CUU:\n{tra_loi}")
    
    pdf.ln(10)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)

    # --- PHẦN KÝ TÊN (LIỆT KÊ DỌC ĐỂ CHỐNG LỖI NGANG) ---
    pdf.set_font(font_name, size=10)
    # Viết từng dòng đơn giản, không chia cột phức tạp
    cac_ben = [
        "Đại diện Chi nhánh Thủy lợi số 5: ................................",
        "Cán bộ địa bàn: ................................................",
        "Đại diện UBND phường Chiềng Cơi: ...............................",
        "Đại diện BQL bản Hôm: ...........................................",
        "Hộ gia đình vi phạm: ............................................",
        "Ngày lập biên bản: 09/04/2026"
    ]
    
    for ben in cac_ben:
        pdf.multi_cell(0, 8, txt=ben)
        pdf.ln(2)

    return pdf.output(dest='S')

# --- 3. HÀM ĐỌC DỮ LIỆU PDF (THÔNG TƯ, NGHỊ ĐỊNH) ---
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

# --- 4. KIỂM TRA KEY & DỮ LIỆU ---
if "OPENAI_API_KEY" in st.secrets:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    if "context" not in st.session_state:
        st.session_state.context = nap_du_lieu_van_ban()
else:
    st.error("Lỗi: Chưa cấu hình OPENAI_API_KEY trong Secrets!")
    st.stop()

# --- 5. GIAO DIỆN CHÍNH ---
st.title("🌊 Hệ thống Quản lý & Trợ lý AI Thủy Lợi Sơn La")

col1, col2 = st.columns([4, 6])

with col1:
    st.header("📍 Thông tin Công trình")
    try:
        # Đọc file Excel từ thư mục specs
        file_excel = [f for f in os.listdir("specs") if f.endswith(".xlsx")][0]
        df = pd.read_excel(os.path.join("specs", file_excel))
        df.columns = df.columns.str.strip() # Xóa khoảng trắng tên cột

        # Chọn công trình theo cột "ten_cong_trinh"
        ten_ct = st.selectbox("Chọn công trình cần báo cáo:", df['ten_cong_trinh'].unique())
        row = df[df['ten_cong_trinh'] == ten_ct].iloc[0]
        
        # Hiển thị thông số chuẩn theo yêu cầu
        st.success(f"🏗️ **Công trình:** {ten_ct}")
        st.info(f"💧 **Dung tích:** {row['dung_tich']} | 📍 **Vị trí:** {row['vi_tri']}")
        
        # Bản đồ 3D Vệ tinh (Google Maps 3D Layer)
        lat, lon = row['lat'], row['lon']
        map_url = f"https://www.google.com/maps/embed?pb=!1m14!1m12!1m3!1d1000!2d{lon}!3d{lat}!2m3!1f45!2f45!3f0!3m2!1i1024!2i768!4f13.1!5e1!3m2!1svi!2s!4v123456789!5m2!1svi!2s"
        st.components.v1.iframe(map_url, height=500)
        
        thong_tin_ct = {
            "ten": ten_ct,
            "dung_tich": row['dung_tich'],
            "vi_tri": row['vi_tri']
        }
    except Exception as e:
        st.warning(f"Đang đồng bộ dữ liệu Excel... (Lưu ý: Cần cột ten_cong_trinh, dung_tich, vi_tri, lat, lon)")

with col2:
    st.header("⚖️ Tra cứu Luật & Lập biên bản")
    hoi = st.text_area("Nhập nội dung cần hỏi hoặc yêu cầu lập biên bản:", height=150, 
                       placeholder="Ví dụ: Lập biên bản kiểm tra hồ đập dựa trên Thông tư 05 và Nghị định 114...")
    
    if hoi:
        with st.spinner("AI đang trích xuất dữ liệu pháp luật..."):
            try:
                # Giới hạn context để AI không bị "ngợp" dữ liệu
                prompt_context = st.session_state.context[:4000]
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": f"Bạn là trợ lý pháp luật Thủy lợi. Hãy trích xuất đúng, đủ các Thông tư, Nghị định từ dữ liệu sau để trả lời hoặc lập biên bản chuyên nghiệp: {prompt_context}"},
                        {"role": "user", "content": f"Dựa trên công trình {ten_ct}, vị trí {row['vi_tri']}, hãy giải quyết: {hoi}"}
                    ],
                    temperature=0.3
                )
                
                tra_loi = response.choices[0].message.content
                st.markdown("### 📄 Nội dung trích xuất & Dự thảo biên bản:")
                st.write(tra_loi)
                
                # --- NÚT XUẤT PDF GỬI LÃNH ĐẠO ---
                st.markdown("---")
                pdf_data = tao_pdf_bien_ban(tra_loi, hoi, thong_tin_ct)
                st.download_button(
                    label="📥 Tải Biên bản PDF (Gửi lãnh đạo)",
                    data=pdf_data,
                    file_name=f"Bien_ban_{ten_ct}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Lỗi hệ thống AI: {e}")