import streamlit as st
import asyncio
import edge_tts
import os

# --- KHO GIỌNG ĐỌC KHỔNG LỒ (FULL LIST) ---
VOICES = {
    "🇻🇳 Việt Nam - Nữ (Hoài My)": "vi-VN-HoaiMyNeural",
    "🇻🇳 Việt Nam - Nam (Nam Minh)": "vi-VN-NamMinhNeural",
    "🇺🇸 Anh Mỹ - Nữ (Aria)": "en-US-AriaNeural",
    "🇺🇸 Anh Mỹ - Nam (Guy)": "en-US-GuyNeural",
}

# --- GIAO DIỆN WEB ---
st.set_page_config(page_title="AI TTS Ultimate", page_icon="🎧", layout="centered")

st.title("🎧 AI TTS Ultimate - Đa Ngôn Ngữ")
st.write("Trang web chuyển đổi văn bản thành giọng nói chất lượng cao.")

text_input = st.text_area("Nhập văn bản cần đọc vào đây:", height=150)

col1, col2 = st.columns(2)
with col1:
    voice_key = st.selectbox("Ngôn ngữ & Giọng:", list(VOICES.keys()))
with col2:
    speed = st.slider("Tốc độ (Speed) | 1.0 = Chuẩn", min_value=0.5, max_value=3.0, value=1.0, step=0.1)
    pitch = st.slider("Cao độ (Pitch)", min_value=-50, max_value=50, value=0, step=1)

if st.button("🚀 Tạo Giọng Đọc", use_container_width=True):
    if not text_input.strip():
        st.warning("Vui lòng nhập văn bản trước khi tạo!")
    else:
        voice_id = VOICES[voice_key]
        speed_pct = int((speed - 1) * 100)
        rate_str = f"+{speed_pct}%" if speed_pct >= 0 else f"{speed_pct}%"
        pitch_str = f"{pitch:+d}Hz"
        output_file = "output.mp3"

        async def generate_audio():
            communicate = edge_tts.Communicate(text_input, voice_id, rate=rate_str, pitch=pitch_str)
            await communicate.save(output_file)

        with st.spinner('Đang dùng AI để tạo giọng đọc... Vui lòng đợi nhé...'):
            try:
                asyncio.run(generate_audio())
                st.success("Tạo giọng đọc thành công!")
                st.audio(output_file, format="audio/mp3")
                with open(output_file, "rb") as file:
                    st.download_button(label="💾 Tải File MP3 Xuống Máy", data=file, file_name="giong_doc_ai.mp3", mime="audio/mp3", use_container_width=True)
            except Exception as e:
                st.error(f"Có lỗi xảy ra: {str(e)}")
