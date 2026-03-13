import streamlit as st
import asyncio
import edge_tts
import os

# --- CẤU HÌNH TRANG WEB (Phải đặt đầu tiên) ---
st.set_page_config(page_title="Giọng Đọc 2z - Chuyển văn bản thành giọng nói", page_icon="🎤", layout="centered")

# --- CSS TÙY CHỈNH (Làm đẹp giao diện giống Vbee) ---
st.markdown("""
    <style>
    /* Ẩn menu mặc định của Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Chỉnh màu nền và font chữ cho tiêu đề */
    .title-text {
        font-size: 40px;
        font-weight: 800;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 10px;
    }
    .subtitle-text {
        font-size: 18px;
        color: #4B5563;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* Làm đẹp nút bấm chính */
    .stButton>button {
        background: linear-gradient(90deg, #2563EB 0%, #1D4ED8 100%);
        color: white;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: bold;
        font-size: 16px;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #1D4ED8 0%, #1E3A8A 100%);
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
        color: white;
    }
    
    /* Làm đẹp khung nhập liệu */
    .stTextArea textarea {
        border-radius: 10px;
        border: 2px solid #E5E7EB;
        padding: 15px;
        font-size: 16px;
    }
    .stTextArea textarea:focus {
        border-color: #2563EB;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# --- KHO GIỌNG ĐỌC KHỔNG LỒ (FULL LIST) ---
VOICES = {
    # --- VIỆT NAM ---
    "🇻🇳 Việt Nam - Nữ (Hoài My)": "vi-VN-HoaiMyNeural",
    "🇻🇳 Việt Nam - Nam (Nam Minh)": "vi-VN-NamMinhNeural",

    # --- TIẾNG ANH (ENGLISH) ---
    "🇺🇸 Anh Mỹ - Nữ (Aria)": "en-US-AriaNeural",
    "🇺🇸 Anh Mỹ - Nữ (Jenny)": "en-US-JennyNeural",
    "🇺🇸 Anh Mỹ - Nam (Guy)": "en-US-GuyNeural",
    "🇺🇸 Anh Mỹ - Nam (Christopher)": "en-US-ChristopherNeural",
    "🇬🇧 Anh Anh - Nữ (Sonia)": "en-GB-SoniaNeural",
    "🇬🇧 Anh Anh - Nam (Ryan)": "en-GB-RyanNeural",
    "🇦🇺 Anh Úc - Nữ (Natasha)": "en-AU-NatashaNeural",
    "🇦🇺 Anh Úc - Nam (William)": "en-AU-WilliamNeural",

    # --- CHÂU Á (ASIA) ---
    "🇨🇳 Trung Quốc - Nữ (Xiaoxiao)": "zh-CN-XiaoxiaoNeural",
    "🇨🇳 Trung Quốc - Nam (Yunxi)": "zh-CN-YunxiNeural",
    "🇯🇵 Nhật Bản - Nữ (Nanami)": "ja-JP-NanamiNeural",
    "🇯🇵 Nhật Bản - Nam (Keita)": "ja-JP-KeitaNeural",
    "🇰🇷 Hàn Quốc - Nữ (SunHi)": "ko-KR-SunHiNeural",
    "🇰🇷 Hàn Quốc - Nam (InJoon)": "ko-KR-InJoonNeural",
}

# --- PHẦN HEADER THƯƠNG HIỆU ---
st.markdown('<div class="title-text">Giọng Đọc 2z 🎤</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Giải pháp chuyển đổi văn bản thành giọng nói AI miễn phí, tự nhiên và cảm xúc.</div>', unsafe_allow_html=True)

# --- KHUNG NHẬP LIỆU CHÍNH ---
st.markdown("### 📝 Nội dung cần đọc:")
text_input = st.text_area("Nhập văn bản của bạn vào đây (tối đa 5000 ký tự):", height=200, label_visibility="collapsed", placeholder="Xin chào, chào mừng bạn đến với Giọng Đọc 2z. Hãy nhập nội dung cần đọc vào đây...")

# --- KHUNG TÙY CHỈNH GIỌNG ---
st.markdown("### ⚙️ Tùy chỉnh giọng đọc:")
col1, col2 = st.columns([1.5, 1])

with col1:
    voice_key = st.selectbox("🌍 Chọn Ngôn ngữ & Giọng đọc:", list(VOICES.keys()))

with col2:
    speed = st.slider("⚡ Tốc độ đọc", min_value=0.5, max_value=2.0, value=1.0, step=0.1, help="1.0 là tốc độ chuẩn của người thật")

# --- NÚT TẠO AUDIO ---
st.markdown("<br>", unsafe_allow_html=True) # Tạo khoảng trống
if st.button("🚀 TẠO GIỌNG ĐỌC AI NGAY", use_container_width=True):
    if not text_input.strip():
        st.warning("⚠️ Bạn ơi, vui lòng nhập văn bản trước khi tạo giọng đọc nhé!")
    else:
        voice_id = VOICES[voice_key]
        speed_pct = int((speed - 1) * 100)
        rate_str = f"+{speed_pct}%" if speed_pct >= 0 else f"{speed_pct}%"
        output_file = "giongdoc2z_output.mp3"

        async def generate_audio():
            communicate = edge_tts.Communicate(text_input, voice_id, rate=rate_str)
            await communicate.save(output_file)

        with st.spinner('⏳ Giọng Đọc 2z đang xử lý dữ liệu AI... Vui lòng đợi trong giây lát...'):
            try:
                asyncio.run(generate_audio())
                st.success("🎉 Tạo giọng đọc thành công!")
                
                # Hiển thị trình phát nhạc và nút tải xuống trong 1 khung gọn gàng
                st.audio(output_file, format="audio/mp3")
                
                with open(output_file, "rb") as file:
                    st.download_button(
                        label="⬇️ TẢI FILE MP3 CHẤT LƯỢNG CAO",
                        data=file,
                        file_name="GiongDoc2z_Audio.mp3",
                        mime="audio/mp3",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"❌ Có lỗi xảy ra trong quá trình xử lý: {str(e)}")

# --- FOOTER ---
st.markdown("---")
st.markdown('<p style="text-align: center; color: #6B7280; font-size: 14px;">© 2026 Giọng Đọc 2z. Cung cấp bởi công nghệ AI.</p>', unsafe_allow_html=True)
