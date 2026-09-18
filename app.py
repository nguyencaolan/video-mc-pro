import os
import json
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import requests

# 1. Cấu hình giao diện rộng
st.set_page_config(page_title="Rubby Nguyen - Video MC Pro", layout="wide")

st.markdown("## 🎬 RUBBY NGUYEN - VIDEO MC PRO (AUTO VIDEO API)")

# 2. THANH CÔNG CỤ BÊN TRÁI (SIDEBAR)
with st.sidebar:
    st.markdown("### 👤 Ảnh Nhân Vật Thanh Chiếu")
    uploaded_avatar = st.file_uploader("Tải lên ảnh gốc nhân vật", type=["jpg", "png", "jpeg"])
    if uploaded_avatar:
        st.image(uploaded_avatar, caption="Ảnh gốc đã chọn", use_container_width=True)
    else:
        st.info("Mẹo: Tải ảnh gốc để cố định khuôn mặt nhân vật.")

    st.markdown("---")
    st.markdown("### ⚙️ Thiết Lập AI Video")
    video_model = st.selectbox("Model tạo video", ["Luma Dream Machine", "Stable Video", "Kling/Runway via API"])
    aspect_ratio = st.selectbox("Tỷ lệ khung hình", ["9:16 (TikTok/Reels)", "16:9 (YouTube)"])
    duration = st.selectbox("Thời lượng cảnh", ["5s", "10s"])

# 3. KHU VỰC TRUNG TÂM - BỘ TẠO KỊCH BẢN
st.markdown("### ⚡ BỘ TẠO KỊCH BẢN & AUTO GENERATE VIDEO")
num_scenes = st.number_input("Số cảnh:", min_value=1, max_value=5, value=2)
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
    Yêu cầu: Bắt buộc chia chính xác thành ĐÚNG {count} cảnh. Lời thoại tiếng Việt, Visual prompt tiếng Anh chi tiết.
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
        st.warning("Vui lòng nhập nội dung ý tưởng!")
    else:
        with st.spinner("AI đang phân tích và tạo kịch bản..."):
            try:
                raw_json = generate_video_script(user_idea, num_scenes)
                st.session_state.script_data = json.loads(raw_json)
                st.session_state.scene_videos = {}
                st.success("Tạo kịch bản thành công!")
            except Exception as e:
                st.error(f"Lỗi: {e}")

if st.session_state.script_data:
    st.markdown("---")
    st.markdown("### 🎞️ DANH SÁCH CẢNH & AUTO RENDER")
    
    scenes = st.session_state.script_data["scenes"]
    
    for scene in scenes:
        scene_idx = scene['scene_number']
        with st.container(border=True):
            st.markdown(f"#### 🎬 Cảnh {scene_idx}")
            
            # Kiểm tra nếu cảnh đã có video thật được trả về từ API
            if scene_idx in st.session_state.scene_videos:
                st.success(f"✅ Đã render xong Cảnh {scene_idx} từ AI!")
                st.video(st.session_state.scene_videos[scene_idx])
            else:
                st.info("⏳ Chưa render - Nhấn 'Sản xuất' để gọi AI sinh video.")
            
            scene['voiceover'] = st.text_area(f"Thoại {scene_idx}", value=scene['voiceover'], height=70, key=f"vo_{scene_idx}")
            scene['visual_prompt'] = st.text_area(f"Prompt {scene_idx}", value=scene['visual_prompt'], height=60, key=f"vp_{scene_idx}")
            
            if st.button("🎬 Sản xuất (Auto Generate)", key=f"prod_{scene_idx}", type="primary"):
                with st.spinner(f"Hệ thống đang gọi API tạo video cho Cảnh {scene_idx} (quá trình này mất khoảng 30s-1 phút)..."):
                    try:
                        # Lấy Fal Key từ Streamlit Secrets
                        fal_key = st.secrets.get("FAL_KEY", "")
                        if not fal_key:
                            st.error("Chưa cấu hình FAL_KEY trong Streamlit Secrets!")
                        else:
                            # Endpoint mẫu gọi mô hình tạo video trên Fal.ai (ví dụ Luma/Stable Video)
                            url = "https://fal.run/fal-ai/luma-dream-machine/v1/generate" # (Hoặc endpoint model khác)
                            headers = {
                                "Authorization": f"Key {fal_key}",
                                "Content-Type": "application/json"
                            }
                            payload = {
                                "prompt": scene['visual_prompt']
                            }
                            
                            # Gửi request gọi sinh video
                            res = requests.post(url, json=payload, headers=headers)
                            if res.status_code == 200:
                                res_data = res.json()
                                # Lấy đường dẫn video trả về từ API
                                video_url = res_data.get("video", {}).get("url") or res_data.get("output", "")
                                if video_url:
                                    st.session_state.scene_videos[scene_idx] = video_url
                                    st.success(f"Sinh video cảnh {scene_idx} thành công!")
                                    st.rerun()
                                else:
                                    st.error("API không trả về đường dẫn video hợp lệ.")
                            else:
                                st.error(f"Lỗi từ API Server: {res.text}")
                    except Exception as ex:
                        st.error(f"Lỗi kết nối: {ex}")
