import streamlit as st
import requests
import json
import re
import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

st.set_page_config(page_title="AI Video Reels Factory", layout="centered")

st.title("🎬 Faceless Reels Factory")

# API atslēgu sānjosla
with st.sidebar:
    st.header("Konfigurācija")
    gemini_key = st.text_input("Gemini API Key", type="password")
    pexels_key = st.text_input("Pexels API Key", type="password")
    st.info("Atslēgas netiek saglabātas.")

topic = st.text_input("Video tēma (piem. Motivation, Coding, Ocean):")

# --- AI & VIDEO FUNKCIJAS ---
def get_working_model(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        r = requests.get(url)
        models = r.json().get('models', [])
        for m in models:
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                return m['name'], 'v1beta'
    except:
        pass
    return None, None

def get_ai_data(topic, api_key, model_path, version):
    url = f"https://generativelanguage.googleapis.com/{version}/{model_path}:generateContent?key={api_key}"
    prompt = (
        f"Generate a short motivational quote about '{topic}' in Latvian. "
        f"Provide a 1-word English search term for a video. "
        f"Return ONLY JSON: {{\"quote\": \"...\", \"search_term\": \"...\"}}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload)
    res_data = response.json()
    full_text = res_data['candidates'][0]['content']['parts'][0]['text']
    json_match = re.search(r'\{.*\}', full_text, re.DOTALL)
    return json.loads(json_match.group())

# --- MONTĀŽAS FUNKCIJA ---
def process_video(video_url, quote):
    # 1. Lejupielādējam video
    st.write("📥 Lejupielādē fonu...")
    video_data = requests.get(video_url).content
    with open("raw_video.mp4", "wb") as f:
        f.write(video_data)
    
    # 2. Montāža ar MoviePy
    st.write("🎨 Liekam virsū tekstu...")
    clip = VideoFileClip("raw_video.mp4").subclip(0, 5) # 5 sekundes
    
    # Teksta uzlika (centrēta, balta)
    txt_clip = TextClip(
        quote, 
        fontsize=40, 
        color='white', 
        font='Arial-Bold', 
        method='caption', 
        size=(clip.w * 0.8, None)
    )
    txt_clip = txt_clip.set_position('center').set_duration(5)
    
    # Savienošana
    final = CompositeVideoClip([clip, txt_clip])
    final.write_videofile("final_reel.mp4", fps=24, codec="libx264")
    return "final_reel.mp4"

# --- INTERFEISS ---
if st.button("Sākt procesu"):
    if not gemini_key or not pexels_key or not topic:
        st.error("Aizpildi visus laukus!")
    else:
        with st.spinner("AI strādā..."):
            model_path, version = get_working_model(gemini_key)
            if model_path:
                data = get_ai_data(topic, gemini_key, model_path, version)
                st.write(f"📝 **Citāts:** {data['quote']}")
                
                # Pexels meklēšana
                px_url = f"https://api.pexels.com/videos/search?query={data['search_term']}&orientation=portrait&per_page=1"
                px_res = requests.get(px_url, headers={"Authorization": pexels_key}).json()
                
                if px_res.get('videos'):
                    video_link = px_res['videos'][0]['video_files'][0]['link']
                    
                    # Sākam montāžu
                    final_path = process_video(video_link, data['quote'])
                    
                    # Rezultāts
                    st.video(final_path)
                    
                    # Lejupielādes poga
                    with open(final_path, "rb") as file:
                        st.download_button(
                            label="📥 Lejupielādēt gatavu Video",
                            data=file,
                            file_name="mans_reels.mp4",
                            mime="video/mp4"
                        )
                else:
                    st.error("Video netika atrasts.")
