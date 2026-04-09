import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from docx import Document
import io

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Thủy lợi Sơn La", layout="wide")

# Hàm tạo file Word (Chạy ngầm)
def tao_file_word(tra_loi, cau_hoi, ten_ct):
    doc = Document()
    doc.add_heading('BIÊN BẢN NGHIỆP VỤ THỦY LỢI', 0)
    doc.add_paragraph(f"Công trình: {ten_ct}")
    doc.add_paragraph(f"Nội dung: {cau_hoi}")
    doc.add_paragraph("-" * 30)
    doc.add_paragraph(tra_loi)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 2. TIÊU ĐỀ DUY NHẤT ---
st.title("🌊 Hệ thống Trợ lý Thủy lợi Sơn La")
st.markdown("---")

# --- 3. XỬ LÝ DỮ LIỆU ---
try:
    file_excel = [f for f in os.listdir("specs") if f.endswith(".xlsx")][0]
    df = pd.read_excel(os.path.join("specs", file_excel))
    df.columns = df.columns.str.strip()
    col_ten = df.select_dtypes(include=['object']).columns[0]
    
    ten_ct = st.selectbox("📍 Chọn công trình/hồ chứa:", df[col_ten].unique())
    row = df[df[col_ten] == ten_ct].iloc[0]
except:
    st.error("Lỗi: Không tìm thấy file Excel trong thư mục 'specs'!")
    st.stop()

# --- 4. CHIA CỘT GIAO DIỆN ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📌 Bản đồ & Thông số")
    for c in df.columns:
        if c.lower() not in ['lat', 'lon']:
            st.write(f"**{c}:** {row[c]}")
    
    lat, lon = row.get('lat'), row.get('lon')
    map_url = f"https://www.google.com/maps?q={lat},{lon}&output=embed&t=k"
    st.components.v1.iframe(map_url, height=450)

with col2:
    st.subheader("💬 Hỏi đáp & Lập báo cáo")
    hoi = st.text_area("Nhập nội dung cần xử lý:", height=150)
    
    if st.button("🚀 Bắt đầu xử lý"):
        if hoi:
            with st.spinner("AI đang soạn thảo..."):
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": f"Về {ten_ct}: {hoi}"}]
                )
                tra_loi = res.choices[0].message.content
                
                st.markdown("### 📝 Kết quả:")
                st.info(tra_loi)
                
                # NÚT TẢI FILE - FIX LỖI CHIA SẺ TRÊN ĐIỆN THOẠI
                st.divider()
                word_data = tao_file_word(tra_loi, hoi, ten_ct)
                st.download_button(
                    label="📥 Tải Biên bản (Gửi qua Zalo)",
                    data=word_data,
                    file_name=f"Bien_ban_{ten_ct}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                # --- PHẦN CHIA SẺ THÔNG MINH ---
                st.divider()
                word_data = tao_file_word(tra_loi, hoi, ten_ct)
                
                # 1. Nút tải truyền thống (để dự phòng)
                st.download_button(
                    label="💾 1. Tải file về máy",
                    data=word_data,
                    file_name=f"Bien_ban_{ten_ct}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

                # 2. Mẹo "Chia sẻ nhanh" (Dùng link Zalo)
                st.markdown(f"""
                    <a href="https://zalo.me/share?url=https://aithuyloisonla.streamlit.app/&title=Biên bản {ten_ct}" 
                       target="_blank" 
                       style="text-decoration: none;">
                        <div style="background-color: #0068ff; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;">
                            📲 2. Gửi nhanh qua Zalo (Link)
                        </div>
                    </a>
                """, unsafe_allow_code=True)
                
                st.caption("⚠️ Lưu ý: Do bảo mật điện thoại, để gửi FILE, ông hãy chọn nút 'Tải về' -> Mở file -> Chọn 'Chia sẻ' -> Chọn Zalo.")