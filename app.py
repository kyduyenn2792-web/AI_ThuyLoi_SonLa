import streamlit as st
import pandas as pd
import os
from openai import OpenAI
import pypdf

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

# --- THANH BÊN (SIDEBAR) MỚI ---
with st.sidebar:
    st.header("🔑 Trạng thái Hệ thống")
    # Tự động lấy Key từ Secrets
    if "OPENAI_API_KEY" in st.secrets:
        st.session_state.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        if "context" not in st.session_state:
            with st.spinner("Đang nạp dữ liệu..."):
                st.session_state.context = doc_pdf_thuy_loi()
        st.session_state.ready = True
        st.success("✅ Hệ thống đang hoạt động")
    else:
        st.error("Chưa cấu hình API Key trong Secrets!")

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