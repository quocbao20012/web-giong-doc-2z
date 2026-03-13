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
import streamlit as st
import asyncio
import edge_tts
import pysrt
import re
import subprocess
import os
import shutil
import tempfile

st.set_page_config(page_title="Giọng Đọc 2z - AI Lồng Tiếng", page_icon="🎤", layout="centered")

# --- DANH SÁCH GIỌNG ---
VOICES = {
    "🇻🇳 VN - Nam Minh (Nam - Truyền cảm)": "vi-VN-NamMinhNeural",
    "🇻🇳 VN - Hoài My (Nữ - Nhẹ nhàng)": "vi-VN-HoaiMyNeural",
    "🇺🇸 US - Christopher (Nam - Mỹ)": "en-US-ChristopherNeural",
    "🇺🇸 US - Jenny (Nữ - Mỹ)": "en-US-JennyNeural",
}

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Giọng Đọc 2z 🎤</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Hệ thống lồng tiếng AI tự động khớp thời gian phụ đề (Khớp Lipsync)</p>", unsafe_allow_html=True)

# --- CÁC HÀM XỬ LÝ LÕI TỪ BỘ V40 CỦA BẠN ---
def get_audio_duration(file_path):
    try:
        cmd = ["ffmpeg", "-i", file_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)", result.stderr)
        if match:
            h, m, s = match.groups()
            return (int(h) * 3600 + int(m) * 60 + float(s)) * 1000
    except: pass
    return 0

def get_atempo_filter(speed):
    if speed < 0.5: speed = 0.5
    filters = []
    while speed > 2.0:
        filters.append("atempo=2.0")
        speed /= 2.0
    filters.append(f"atempo={speed}")
    return ",".join(filters)

def lam_sach_text(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\d{1,2}:\d{1,2}:\d{1,2}[,.]\d{1,3}', '', text)
    text = text.replace('-->', '')
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    return text.strip()

# --- GIAO DIỆN CHÍNH ---
st.info("📁 Vui lòng tải file phụ đề (.srt) của bạn lên để bắt đầu lồng tiếng.")
uploaded_srt = st.file_uploader("Chọn file SRT nguồn:", type=['srt'])

col1, col2 = st.columns([1.5, 1])
with col1:
    voice_key = st.selectbox("🌍 Chọn Giọng đọc:", list(VOICES.keys()))
with col2:
    base_speed = st.slider("⚡ Tốc độ nền", min_value=1.0, max_value=2.5, value=1.2, step=0.1)

if st.button("🚀 BẮT ĐẦU XỬ LÝ AUDIO", use_container_width=True):
    if uploaded_srt is None:
        st.warning("⚠️ Bạn chưa tải file SRT lên!")
    else:
        voice_id = VOICES[voice_key]
        
        # Lưu file SRT tạm thời để pysrt đọc
        with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as tmp_srt:
            tmp_srt.write(uploaded_srt.getvalue())
            srt_path = tmp_srt.name

        subs = None
        for enc in ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']:
            try:
                subs = pysrt.open(srt_path, encoding=enc)
                if len(subs) > 0: break
            except: pass
            
        if not subs:
            st.error("❌ Lỗi: Không đọc được nội dung file SRT.")
        else:
            output_file = "GiongDoc2z_Dubbed.mp3"
            temp_dir = "temp_web_dubbing"
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)

            concat_list = os.path.join(temp_dir, "list.txt")
            f_list = open(concat_list, "w", encoding="utf-8")
            current_timeline = 0

            progress_bar = st.progress(0)
            status_text = st.empty()

            async def process_subtitles():
                nonlocal current_timeline
                for i, sub in enumerate(subs):
                    status_text.text(f"⏳ Đang xử lý dòng {i+1}/{len(subs)}...")
                    progress_bar.progress((i + 1) / len(subs))
                    
                    text = lam_sach_text(sub.text)
                    if not text: continue
                    
                    start_srt = sub.start.ordinal
                    end_srt = sub.end.ordinal
                    allowed_duration = end_srt - start_srt
                    if allowed_duration < 500: allowed_duration = 500

                    # 1. Chèn khoảng lặng
                    gap = start_srt - current_timeline
                    if gap > 100:
                        safe_gap = gap - 100 
                        if safe_gap > 0:
                            sil_file = os.path.join(temp_dir, f"sil_{i}.mp3")
                            sec = safe_gap / 1000.0
                            # Xóa startupinfo vì Linux không dùng cái này
                            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(sec), "-q:a", "9", sil_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            f_list.write(f"file 'sil_{i}.mp3'\n")
                            current_timeline += safe_gap

                    # 2. Tạo Audio
                    raw = os.path.join(temp_dir, f"raw_{i}.mp3")
                    proc = os.path.join(temp_dir, f"proc_{i}.mp3")
                    rate_str = f"{int((base_speed - 1) * 100):+d}%"
                    
                    await edge_tts.Communicate(text, voice_id, rate=rate_str).save(raw)
                    
                    dur = get_audio_duration(raw)
                    final_dur = dur
                    
                    if dur > 0:
                        ratio = dur / allowed_duration
                        if ratio > 1.05:
                            af = get_atempo_filter(ratio)
                            subprocess.run(["ffmpeg", "-y", "-i", raw, "-filter:a", af, "-vn", proc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            final_dur = allowed_duration
                        else:
                            shutil.copy(raw, proc)
                    else:
                        shutil.copy(raw, proc)
                        
                    f_list.write(f"file 'proc_{i}.mp3'\n")
                    current_timeline += final_dur

                f_list.close()
                status_text.text("⚙️ Đang đóng gói file cuối cùng...")
                
                # Nối file
                subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", output_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Chạy logic
            asyncio.run(process_subtitles())
            
            # Xóa rác
            try: shutil.rmtree(temp_dir)
            except: pass
            
            status_text.text("✅ Hoàn tất lồng tiếng khớp thời gian!")
            
            # Hiển thị kết quả
            st.success("Tạo file lồng tiếng thành công! Bạn có thể nghe thử hoặc tải về bên dưới:")
            st.audio(output_file, format="audio/mp3")
            with open(output_file, "rb") as file:
                st.download_button(label="⬇️ TẢI FILE AUDIO CHUẨN TIMELINE", data=file, file_name="GiongDoc2z_Dubbed.mp3", mime="audio/mp3", use_container_width=True)
