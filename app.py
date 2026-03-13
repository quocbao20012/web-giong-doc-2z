import streamlit as st
from streamlit_option_menu import option_menu
import asyncio
import edge_tts
import pysrt
import re
import subprocess
import os
import shutil
import tempfile
import datetime

# --- 1. CẤU HÌNH TRANG RỘNG (Giống Vbee) ---
st.set_page_config(page_title="Giọng Đọc 2z - AI Lồng Tiếng", page_icon="🎙️", layout="wide")

# --- 2. CSS TÙY CHỈNH GIAO DIỆN ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Làm đẹp nút bấm chính (Màu vàng giống Vbee) */
    div.stButton > button[kind="primary"] {
        background-color: #FFC107;
        color: black;
        border: none;
        border-radius: 25px;
        padding: 10px 30px;
        font-weight: bold;
        font-size: 16px;
        transition: 0.3s;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #FFB300;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        color: black;
    }
    
    /* Khung Toolbar Tool */
    .toolbar-container {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
    }
    
    /* Tiêu đề trang */
    .page-header {font-size: 24px; font-weight: bold; color: #333; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

# --- 3. DỮ LIỆU GIỌNG ĐỌC & HÀM CƠ BẢN ---
VOICES = {
    "🇻🇳 VN - Ngọc Huyền (Nữ)": "vi-VN-HoaiMyNeural",
    "🇻🇳 VN - Nam Minh (Nam)": "vi-VN-NamMinhNeural",
    "🇺🇸 US - Christopher (Nam)": "en-US-ChristopherNeural",
    "🇺🇸 US - Jenny (Nữ)": "en-US-JennyNeural",
}

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

# Khởi tạo Lịch sử lưu trữ tạm thời
if "history" not in st.session_state:
    st.session_state.history = []

# --- 4. THANH MENU BÊN TRÁI (SIDEBAR) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🎙️ Giọng Đọc 2z</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    selected_menu = option_menu(
        menu_title=None,
        options=["Chuyển văn bản", "Chuyển phụ đề"],
        icons=["mic-fill", "file-earmark-text-fill"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#6c757d", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"5px 0px", "color": "#495057"},
            "nav-link-selected": {"background-color": "#e9ecef", "color": "#000", "font-weight": "bold", "border-left": "4px solid #FFC107"},
        }
    )

# --- 5. GIAO DIỆN CHÍNH BÊN PHẢI ---
st.markdown(f"<div class='page-header'>{selected_menu}</div>", unsafe_allow_html=True)

# Khung Toolbar (Giống thanh chọn giọng của Vbee)
with st.container():
    st.markdown("<div class='toolbar-container'>", unsafe_allow_html=True)
    t_col1, t_col2, t_col3 = st.columns([2, 2, 6])
    with t_col1:
        voice_choice = st.selectbox("Chọn giọng:", list(VOICES.keys()), label_visibility="collapsed")
    with t_col2:
        speed_choice = st.slider("Tốc độ", 0.5, 2.0, 1.0, 0.1, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

voice_id = VOICES[voice_choice]
speed_pct = int((speed_choice - 1) * 100)
rate_str = f"+{speed_pct}%" if speed_pct >= 0 else f"{speed_pct}%"

# ----------------------------------------
# TRANG 1: CHUYỂN VĂN BẢN
# ----------------------------------------
if selected_menu == "Chuyển văn bản":
    text_input = st.text_area("Nhập văn bản", height=250, label_visibility="collapsed", placeholder="Nhập, copy văn bản vào đây để chuyển thành giọng nói cảm xúc...")
    
    col_btn1, col_btn2 = st.columns([8, 2])
    with col_btn2:
        if st.button("🎙️ Tạo audio", type="primary", use_container_width=True):
            if not text_input.strip():
                st.warning("Vui lòng nhập văn bản!")
            else:
                out_file = f"Audio_{datetime.datetime.now().strftime('%H%M%S')}.mp3"
                async def gen_text():
                    communicate = edge_tts.Communicate(text_input, voice_id, rate=rate_str)
                    await communicate.save(out_file)
                
                with st.spinner('Đang tạo audio...'):
                    asyncio.run(gen_text())
                    # Lưu vào lịch sử
                    with open(out_file, "rb") as f:
                        audio_bytes = f.read()
                    st.session_state.history.append({"time": datetime.datetime.now().strftime('%d/%m/%Y - %H:%M'), "type": "Văn bản", "voice": voice_choice, "data": audio_bytes, "name": out_file})
                    st.success("Xong!")

# ----------------------------------------
# TRANG 2: CHUYỂN PHỤ ĐỀ SRT
# ----------------------------------------
elif selected_menu == "Chuyển phụ đề":
    st.info("Kéo thả file .srt vào đây hoặc nhấn để tải lên")
    uploaded_srt = st.file_uploader("", type=['srt'], label_visibility="collapsed")
    
    col_btn1, col_btn2 = st.columns([8, 2])
    with col_btn2:
        if st.button("🎬 Dự án SRT", type="primary", use_container_width=True):
            if uploaded_srt is None:
                st.warning("Vui lòng tải file SRT lên!")
            else:
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
                    st.error("Lỗi đọc file SRT.")
                else:
                    out_file = f"Dubbed_{datetime.datetime.now().strftime('%H%M%S')}.mp3"
                    temp_dir = "temp_dub"
                    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
                    os.makedirs(temp_dir)
                    concat_list = os.path.join(temp_dir, "list.txt")
                    f_list = open(concat_list, "w", encoding="utf-8")
                    
                    current_timeline = [0]
                    prog = st.progress(0)
                    stat = st.empty()

                    async def gen_srt():
                        for i, sub in enumerate(subs):
                            stat.text(f"Đang xử lý dòng {i+1}/{len(subs)}...")
                            prog.progress((i + 1) / len(subs))
                            text = lam_sach_text(sub.text)
                            if not text: continue
                            start_srt, end_srt = sub.start.ordinal, sub.end.ordinal
                            allowed_dur = max(end_srt - start_srt, 500)

                            gap = start_srt - current_timeline[0]
                            if gap > 100:
                                safe_gap = gap - 100 
                                if safe_gap > 0:
                                    sil_file = os.path.join(temp_dir, f"sil_{i}.mp3")
                                    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(safe_gap / 1000.0), "-q:a", "9", sil_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    f_list.write(f"file 'sil_{i}.mp3'\n")
                                    current_timeline[0] += safe_gap

                            raw, proc = os.path.join(temp_dir, f"raw_{i}.mp3"), os.path.join(temp_dir, f"proc_{i}.mp3")
                            await edge_tts.Communicate(text, voice_id, rate=rate_str).save(raw)
                            
                            dur = get_audio_duration(raw)
                            final_dur = dur
                            if dur > 0:
                                ratio = dur / allowed_dur
                                if ratio > 1.05:
                                    subprocess.run(["ffmpeg", "-y", "-i", raw, "-filter:a", get_atempo_filter(ratio), "-vn", proc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    final_dur = allowed_dur
                                else: shutil.copy(raw, proc)
                            else: shutil.copy(raw, proc)
                                
                            f_list.write(f"file 'proc_{i}.mp3'\n")
                            current_timeline[0] += final_dur

                        f_list.close()
                        stat.text("Đang ghép nối audio...")
                        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", out_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                    with st.spinner('Đang lồng tiếng FFMPEG...'):
                        asyncio.run(gen_srt())
                        try: shutil.rmtree(temp_dir)
                        except: pass
                        stat.empty()
                        prog.empty()
                        
                        # Lưu vào lịch sử
                        with open(out_file, "rb") as f:
                            audio_bytes = f.read()
                        st.session_state.history.append({"time": datetime.datetime.now().strftime('%d/%m/%Y - %H:%M'), "type": "SRT", "voice": voice_choice, "data": audio_bytes, "name": out_file})
                        st.success("Hoàn tất lồng tiếng khớp Timeline!")

# --- 6. DANH SÁCH LỊCH SỬ (Giống mục "Danh sách yêu cầu" của Vbee) ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📋 Danh sách chuyển đổi")

if len(st.session_state.history) == 0:
    st.info("Chưa có bản thu âm nào. Hãy tạo một bản thu mới!")
else:
    # Hiển thị lịch sử từ mới nhất đến cũ nhất
    for item in reversed(st.session_state.history):
        with st.container():
            h_col1, h_col2, h_col3 = st.columns([4, 6, 2])
            with h_col1:
                st.write(f"**{item['type']}**")
                st.caption(f"{item['time']} • {item['voice']}")
            with h_col2:
                st.audio(item['data'], format="audio/mp3")
            with h_col3:
                st.download_button("⬇️ Tải về", data=item['data'], file_name=item['name'], mime="audio/mp3", key=item['name'])
        st.markdown("---")
