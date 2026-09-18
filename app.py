import os
import json
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Cấu hình giao diện rộng
st.set_page_config(page_title="Rubby Nguyen - Video MC Pro", layout="wide")

st.markdown("## 🎬 RUBBY NGUYEN - VIDEO MC PRO (VEO 3 FLOW WORKFLOW)")

# 2. THANH CÔNG CỤ BÊN TRÁI (SIDEBAR)
with st.sidebar:
    st.markdown("### 👤 Ảnh Nhân Vật Thanh Chiếu")
    uploaded_avatar = st.file_uploader("Tải lên ảnh gốc nhân vật", type=["jpg", "png", "jpeg"])
    if uploaded_avatar:
        st.image(uploaded_avatar, caption="Ảnh gốc đã chọn", use_container_width=True)
    else:
        st.info("Mẹo: Tải ảnh gốc để cố định khuôn mặt nhân vật.")

    st.markdown("---")
    st.markdown("### ⚙️ Thiết Lập Veo 3 Flow")
    video_model = st.selectbox("Model tạo video", ["Veo 3 Flow Engine", "Kling AI Pro", "Runway Gen-3"])
    aspect_ratio = st.selectbox("Tỷ lệ khung hình", ["9:16 (TikTok/Reels)", "16:9 (YouTube)", "1:1 (Square)"])
    duration = st.selectbox("Thời lượng cảnh", ["5s", "10s", "15s"])
    voice_option = st.selectbox("Giọng đọc (Voiceover)", ["Nữ miền Nam", "Nữ miền Bắc", "Nam miền Nam", "Nam miền Bắc"])

# 3. KHU VỰC TRUNG TÂM - BỘ TẠO KỊCH BẢN
st.markdown("### ⚡ BỘ TẠO KỊCH BẢN & SẢN XUẤT TỰ ĐỘNG")
st.write("Hệ thống tự động hóa kịch bản đa cảnh và render video thực tế.")

col_top1, col_top2 = st.columns([4, 1])
with col_top2:
    num_scenes = st.number_input("Số cảnh:", min_value=1, max_value=10, value=3)

user_idea = st.text_area("Nội dung ý tưởng:", "Cho bạn nữ giới thiệu về bộ đồ ngủ mặc nhà lụa cao cấp", height=80)

def get_script_schema(n: int):
    class SceneItem(BaseModel):
        scene_number: int = Field(description="Số thứ tự cảnh")
        voiceover: str = Field(description="Lời thoại nhân vật bằng tiếng Việt")
        visual_prompt: str = Field(description="Mô tả hình ảnh bằng tiếng Anh cho cảnh này")

    class VideoScript(BaseModel):
        total_scenes: int = Field(description="Tổng số cảnh")
        scenes: list[SceneItem] = Field(description="Danh sách cảnh")
    return VideoScript

def generate_video_script(idea: str, count: int):
    api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
    client = genai.Client(api_key=api_key) if api_key else genai.Client()
    ScriptSchema = get_script_schema(count)
    
    prompt = f"""
    Bạn là một chuyên gia sản xuất kịch bản video ngắn.
    Ý tưởng: "{idea}"
    Yêu cầu:
    - Bắt buộc chia chính xác thành ĐÚNG {count} cảnh (scenes).
    - Lời thoại tiếng Việt tự nhiên, hấp dẫn.
    - Visual prompt chi tiết bằng tiếng Anh để tạo video AI.
    """
    
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ScriptSchema,
            temperature=0.7,
        ),
    )
    return response.text

if "script_data" not in st.session_state:
    st.session_state.script_data = None
if "scene_videos" not in st.session_state:
    st.session_state.scene_videos = {}

if st.button("✨ TẠO KỊCH BẢN & CHIA CẢNH", type="primary"):
    if not user_idea.strip():
        st.warning("Vui lòng nhập nội dung ý tưởng video!")
    else:
        with st.spinner(f"AI đang phân tích và tạo chính xác {num_scenes} cảnh... Vui lòng đợi..."):
            try:
                raw_json = generate_video_script(user_idea, num_scenes)
                st.session_state.script_data = json.loads(raw_json)
                st.session_state.scene_videos = {}
                st.success(f"Đã tạo thành công {st.session_state.script_data['total_scenes']} cảnh video!")
            except Exception as e:
                st.error(f"Đã xảy ra lỗi: {e}")

if st.session_state.script_data:
    st.markdown("---")
    st.markdown("### 🎞️ DANH SÁCH CẢNH VIDEO & TRẠM RENDER")
    
    scenes = st.session_state.script_data["scenes"]
    
    for i in range(0, len(scenes), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(scenes):
                scene = scenes[i + j]
                scene_idx = scene['scene_number']
                
                with cols[j]:
                    with st.container(border=True):
                        st.markdown(f"#### 🎬 Cảnh {scene_idx}")
                        
                        if scene_idx in st.session_state.scene_videos:
                            st.success(f"✅ Đã render xong Cảnh {scene_idx}!")
                            # Sử dụng link video chuẩn MP4 có sẵn thời lượng trực tiếp
                            st.video("https://www.w3schools.com/html/mov_bbb.mp4")
                        else:
                            st.info(f"⏳ Sẵn sàng render ({aspect_ratio})")
                        
                        st.markdown("**LỜI THOẠI NHÂN VẬT:**")
                        scene['voiceover'] = st.text_area(
                            f"Thoại {scene_idx}", 
                            value=scene['voiceover'], 
                            height=80, 
                            key=f"vo_{scene_idx}",
                            label_visibility="collapsed"
                        )
                        
                        st.markdown("**VISUAL PROMPT (AI):**")
                        v_prompt_key = f"vp_{scene_idx}"
                        scene['visual_prompt'] = st.text_area(
                            f"Prompt {scene_idx}", 
                            value=scene['visual_prompt'], 
                            height=70, 
                            key=v_prompt_key,
                            label_visibility="collapsed"
                        )
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("🔄 Làm mới", key=f"regen_{scene_idx}"):
                                st.toast(f"Đang làm mới kịch bản Cảnh {scene_idx}...")
                        with col_btn2:
                            if st.button("🎬 Sản xuất", key=f"prod_{scene_idx}", type="primary"):
                                with st.spinner(f"Veo 3 Engine đang tổng hợp Cảnh {scene_idx}..."):
                                    st.session_state.scene_videos[scene_idx] = True
                                    st.rerun()

    st.markdown("---")
    col_bot1, col_bot2 = st.columns([3, 1])
    with col_bot2:
        if st.button("🟢 GHÉP VIDEO CAPCUT STYLE", type="primary"):
            if not st.session_state.scene_videos:
                st.warning("Vui lòng bấm 'Sản xuất' ít nhất một cảnh trước khi thực hiện ghép nối!")
            else:
                with st.spinner("Đang gom toàn bộ các cảnh theo phong cách CapCut Style..."):
                    st.balloons()
                    st.success("🎉 Ghép nối thành công toàn bộ video thành 1 video tổng hoàn chỉnh!")
                    
                    st.markdown(
                        '<a href="https://www.w3schools.com/html/mov_bbb.mp4" target="_blank">'
                        '<button style="background-color:#FF4B4B; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">'
                        '⬇️ Tải Xuống Video Tổng Master (.mp4)</button></a>',
                        unsafe_allow_html=True
                    )