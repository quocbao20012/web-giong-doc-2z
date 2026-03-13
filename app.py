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

# --- CSS LÀM ĐẸP GIAO DIỆN ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .title-text {font-size: 38px; font-weight: 800; color: #1E3A8A; text-align: center; margin-bottom: 5px;}
    .subtitle-text {font-size: 16px; color: #6B7280; text-align: center; margin-bottom: 25px;}
    .stTabs [data-baseweb="tab-list"] {gap: 20px;}
    .stTabs [data-baseweb="tab"] {padding: 10px 20px; font-size: 18px; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# --- DANH SÁCH GIỌNG ---
VOICES = {
    "🇻🇳 VN - Hoài My (Nữ - Nhẹ nhàng)": "vi-VN-HoaiMyNeural",
    "🇻🇳 VN - Nam Minh (Nam - Truyền cảm)": "vi-VN-NamMinhNeural",
    "🇺🇸 US - Christopher (Nam - Mỹ)": "en-US-ChristopherNeural",
    "🇺🇸 US - Jenny (Nữ - Mỹ)": "en-US-JennyNeural",
}

st.markdown('<div class="title-text">Giọng Đọc 2z 🎤</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Giải pháp chuyển văn bản và lồng tiếng phụ đề tự động</div>', unsafe_allow_html=True)

# --- CÁC HÀM XỬ LÝ LÕI FFMPEG ---
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

# ==========================================
# CHIA GIAO DIỆN THÀNH 2 THẺ (TABS)
# ==========================================
tab_text, tab_srt = st.tabs(["📝 Đọc Văn Bản", "📁 Lồng Tiếng SRT"])

# ------------------------------------------
# THẺ 1: ĐỌC VĂN BẢN THÔNG THƯỜNG
# ------------------------------------------
with tab_text:
    st.markdown("### Nhập nội dung cần đọc:")
    text_input = st.text_area("Văn bản (tối đa 5000 ký tự):", height=150, label_visibility="collapsed")
    
    col1, col2 = st.columns([1.5, 1])
    with col1:
        voice_key_text = st.selectbox("🌍 Chọn Giọng đọc:", list(VOICES.keys()), key="voice_text")
    with col2:
        speed_text = st.slider("⚡ Tốc độ", min_value=0.5, max_value=2.0, value=1.0, step=0.1, key="speed_text")
        
    if st.button("🚀 TẠO GIỌNG ĐỌC VĂN BẢN", use_container_width=True, key="btn_text"):
        if not text_input.strip():
            st.warning("⚠️ Vui lòng nhập văn bản trước!")
        else:
            voice_id_text = VOICES[voice_key_text]
            speed_pct = int((speed_text - 1) * 100)
            rate_str = f"+{speed_pct}%" if speed_pct >= 0 else f"{speed_pct}%"
            out_audio_text = "GiongDoc2z_Text.mp3"

            async def generate_text_audio():
                communicate = edge_tts.Communicate(text_input, voice_id_text, rate=rate_str)
                await communicate.save(out_audio_text)

            with st.spinner('⏳ Đang xử lý âm thanh...'):
                try:
                    asyncio.run(generate_text_audio())
                    st.success("🎉 Tạo thành công!")
                    st.audio(out_audio_text, format="audio/mp3")
                    with open(out_audio_text, "rb") as file:
                        st.download_button("⬇️ TẢI FILE MP3", data=file, file_name="GiongDoc2z_Audio.mp3", mime="audio/mp3", use_container_width=True, key="dl_text")
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")

# ------------------------------------------
# THẺ 2: LỒNG TIẾNG FILE SRT (Khớp Timeline)
# ------------------------------------------
with tab_srt:
    st.info("💡 Tải file .srt lên. Hệ thống tự động dùng AI để ép xung, chèn khoảng lặng khớp với từng dòng thời gian.")
    uploaded_srt = st.file_uploader("Chọn file SRT nguồn:", type=['srt'])

    col3, col4 = st.columns([1.5, 1])
    with col3:
        voice_key_srt = st.selectbox("🌍 Chọn Giọng đọc:", list(VOICES.keys()), key="voice_srt")
    with col4:
        base_speed_srt = st.slider("⚡ Tốc độ nền", min_value=1.0, max_value=2.5, value=1.2, step=0.1, key="speed_srt")

    if st.button("🚀 BẮT ĐẦU LỒNG TIẾNG SRT", use_container_width=True, key="btn_srt"):
        if uploaded_srt is None:
            st.warning("⚠️ Bạn chưa tải file SRT lên!")
        else:
            voice_id_srt = VOICES[voice_key_srt]
            
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
                output_file_srt = "GiongDoc2z_Dubbed.mp3"
                temp_dir = "temp_web_dubbing"
                if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
                os.makedirs(temp_dir)

                concat_list = os.path.join(temp_dir, "list.txt")
                f_list = open(concat_list, "w", encoding="utf-8")
                
                current_timeline = [0]
                progress_bar = st.progress(0)
                status_text = st.empty()

                async def process_subtitles():
                    for i, sub in enumerate(subs):
                        status_text.text(f"⏳ Đang xử lý dòng {i+1}/{len(subs)}...")
                        progress_bar.progress((i + 1) / len(subs))
                        
                        text = lam_sach_text(sub.text)
                        if not text: continue
                        
                        start_srt = sub.start.ordinal
                        end_srt = sub.end.ordinal
                        allowed_duration = end_srt - start_srt
                        if allowed_duration < 500: allowed_duration = 500

                        gap = start_srt - current_timeline[0]
                        if gap > 100:
                            safe_gap = gap - 100 
                            if safe_gap > 0:
                                sil_file = os.path.join(temp_dir, f"sil_{i}.mp3")
                                sec = safe_gap / 1000.0
                                subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(sec), "-q:a", "9", sil_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                f_list.write(f"file 'sil_{i}.mp3'\n")
                                current_timeline[0] += safe_gap

                        raw = os.path.join(temp_dir, f"raw_{i}.mp3")
                        proc = os.path.join(temp_dir, f"proc_{i}.mp3")
                        rate_str_srt = f"{int((base_speed_srt - 1) * 100):+d}%"
                        
                        await edge_tts.Communicate(text, voice_id_srt, rate=rate_str_srt).save(raw)
                        
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
                        current_timeline[0] += final_dur

                    f_list.close()
                    status_text.text("⚙️ Đang đóng gói file cuối cùng...")
                    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", output_file_srt], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                asyncio.run(process_subtitles())
                
                try: shutil.rmtree(temp_dir)
                except: pass
                
                status_text.text("✅ Hoàn tất lồng tiếng khớp thời gian!")
                st.success("Tạo file lồng tiếng thành công! Nghe thử hoặc tải về bên dưới:")
                st.audio(output_file_srt, format="audio/mp3")
                with open(output_file_srt, "rb") as file:
                    st.download_button(label="⬇️ TẢI FILE AUDIO CHUẨN TIMELINE", data=file, file_name="GiongDoc2z_Dubbed.mp3", mime="audio/mp3", use_container_width=True, key="dl_srt")
