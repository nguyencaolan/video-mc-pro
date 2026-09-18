import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class SceneItem(BaseModel):
    scene_number: int = Field(description="Số thứ tự của cảnh, bắt đầu từ 1")
    voiceover: str = Field(description="Lời thoại của nhân vật bằng tiếng Việt")
    visual_prompt: str = Field(description="Mô tả hình ảnh bằng tiếng Anh cho cảnh này")

class VideoScript(BaseModel):
    total_scenes: int = Field(description="Tổng số cảnh")
    scenes: list[SceneItem] = Field(description="Danh sách chi tiết các cảnh")

def generate_video_script(user_idea: str):
    client = genai.Client()

    prompt = f"""
    Bạn là một chuyên gia sản xuất kịch bản video ngắn (TikTok, Reels, Shorts).
    Hãy dựa vào ý tưởng sau đây để viết một kịch bản video hoàn chỉnh, hấp dẫn, nhịp độ nhanh:
    Ý tưởng: "{user_idea}"
    
    Yêu cầu:
    - Chia nội dung thành từ 3 đến 5 cảnh hợp lý.
    - Lời thoại phải tự nhiên, thu hút.
    - Mô tả hình ảnh (visual prompt) phải chi tiết bằng tiếng Anh.
    """

    print(f"Đang xử lý ý tưởng: '{user_idea}'...")

    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VideoScript,
            temperature=0.7,
        ),
    )

    return response.text

if __name__ == "__main__":
    sample_idea = "Giới thiệu bộ đồ ngủ mặc nhà lụa cao cấp, thoải mái và sang trọng cho phái đẹp"
    result_json = generate_video_script(sample_idea)
    print("\n--- KẾT QUẢ KỊCH BẢN (JSON) ---")
    print(result_json)
