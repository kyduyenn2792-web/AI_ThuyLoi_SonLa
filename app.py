import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from fpdf import FPDF

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Hệ thống Thủy lợi Sơn La AI", layout="wide")

# --- 2. HÀM TẠO BIÊN BẢN PDF TIẾNG VIỆT GỬI LÃNH ĐẠO ---
def tao_pdf_bien_ban(tra_loi, cau_hoi, thong_tin_ct):
    pdf = FPDF()
    pdf.add_page()
    
    # Cố gắng nạp font Arial để viết tiếng Việt
    font_name = "Arial"
    try:
        if os.path.exists("arial.ttf"):
            pdf.add_font("ArialVN", "", "arial.ttf")
            font_name = "ArialVN"
    except Exception as e:
        pass # Nếu font lỗi, tự dùng font mặc định để app không bị sập

    # --- QUỐC HIỆU ---
    pdf.set_font(font_name, size=12, style='B')
    pdf.cell(0, 7, txt="CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", ln=True, align='C')
    pdf.set_font(font_name, size=11, style='U')
    pdf.cell(0, 7, txt="Độc lập - Tự do - Hạnh phúc", ln=True, align='C')
    pdf.ln(10)
    
    # --- TIÊU ĐỀ ---
    pdf.set_font(font_name, size=14, style='B')
    pdf.cell(0, 10, txt="BIÊN BẢN TRA CỨU & BÁO CÁO NGHIỆP VỤ", ln=True, align='C')
    pdf.ln(5)
    
    # --- THÔNG TIN CÔNG TRÌNH ---
    pdf.set_font(font_name, size=11)
    # Lấy tên công trình từ dictionary thong_tin_ct
    ten = thong_tin_ct.get('ten', 'N/A')
    pdf.multi_cell(0, 7, txt=f"Tên công trình: {ten}")
    pdf.multi_cell(0, 7, txt=f"Nội dung tra cứu: {cau_hoi}")
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Kẻ đường ngang
    pdf.ln(5)
    
    # --- KẾT QUẢ ---
    pdf.set_font(font_name, size=11, style='B')
    pdf.cell(0, 7, txt="Kết quả từ hệ thống Trợ lý AI:", ln=True)
    pdf.set_font(font_name, size=11)
    pdf.multi_cell(0, 7, txt=tra_loi)
    
    pdf.ln(15)
    
    # --- PHẦN KÝ TÊN (CHIA 2 CỘT) ---
    y_truoc_ky = pdf.get_y()
    pdf.set_font(font_name, size=10, style='B')
    
    # Cột trái
    pdf.set_x(15)
    pdf.multi_cell(80, 5, txt="Đại diện Chi nhánh Thủy lợi\n(Ký, ghi rõ họ tên)", align='C')
    
    # Cột phải (UBND Phường)
    pdf.set_y(y_truoc_ky)
    pdf.set_x(110)
    pdf.multi_cell(80, 5, txt="Đại diện UBND Phường/Bản\n(Ký, ghi rõ họ tên)", align='C')
    
    pdf.ln(15)
    
    # Dòng cuối
    pdf.set_font(font_name, size=10, style='I')
    pdf.cell(0, 10, txt="Ngày ..... tháng ..... năm 2026", ln=True, align='R')
    pdf.set_font(font_name, size=10, style='B')
    pdf.cell(0, 5, txt="Người lập biên bản: .......................................", ln=True, align='R')
    
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