import streamlit as st
import requests
import json
import re
import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings

# ImageMagick konfigurācija
if os.path.exists("/usr/bin/convert"):
    change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

st.set_page_config(page_title="AI Video Reels Factory", layout="centered")
st.title("🎬 Faceless Reels Factory")

with st.sidebar:
    st.header("Konfigurācija")
    gemini_key = st.text_input("Gemini API Key", type="password")
    pexels_key = st.text_input("Pexels API Key", type="password")

topic = st.text_input("Video tēma (piem. Motivation, Ocean):")

def get_ai_data(topic, api_key):
    # Mēs mēģināsim divus populārākos modeļus pēc kārtas
    models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash-exp", "gemini-pro"]
    
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        prompt = (
            f"Generate a short motivational quote about '{topic}' in Latvian. "
            f"Provide a 1-word English search term for a video. "
            f"Return ONLY JSON: {{\"quote\": \"...\", \"search_term\": \"...\"}}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            res_data = response.json()
            if 'candidates' in res_data:
                full_text = res_data['candidates'][0]['content']['parts'][0]['text']
                json_match = re.search(r'\{.*\}', full_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group()), model
        except:
            continue
    return None, None

def process_video(video_url, quote):
    temp_raw = "raw_video.mp4"
    output_file = "final_reel.mp4"
    
    try:
        video_data = requests.get(video_url).content
        with open(temp_raw, "wb") as f:
            f.write(video_data)
        
        with VideoFileClip(temp_raw) as clip:
            clip = clip.subclip(0, 5)
            # Izmantojam metodi 'label', kas ir vienkāršāka par 'caption'
            txt_clip = TextClip(
                quote, 
                fontsize=40, 
                color='white', 
                font='Liberation-Sans',
                method='caption',
                size=(clip.w * 0.8, None)
            ).set_duration(5).set_position('center')
            
            final = CompositeVideoClip([clip, txt_clip])
            final.write_videofile(output_file, fps=24, codec="libx264", audio=False, logger=None)
            
            txt_clip.close()
            final.close()
        return output_file
    except Exception as e:
        st.error(f"Montāžas kļūda: {e}")
        return None

if st.button("Sākt procesu"):
    if not gemini_key or not pexels_key or not topic:
        st.error("Aizpildi visus laukus!")
    else:
        with st.spinner("Sistēma meklē labāko AI modeli un ģenerē saturu..."):
            data, used_model = get_ai_data(topic, gemini_key)
            
            if data:
                st.info(f"Izmantotais modelis: {used_model}")
                st.write(f"📝 **Citāts:** {data['quote']}")
                
                px_url = f"https://api.pexels.com/videos/search?query={data['search_term']}&orientation=portrait&per_page=1"
                px_res = requests.get(px_url, headers={"Authorization": pexels_key}).json()
                
                if px_res.get('videos'):
                    video_link = px_res['videos'][0]['video_files'][0]['link']
                    final_path = process_video(video_link, data['quote'])
                    
                    if final_path:
                        st.video(final_path)
                        with open(final_path, "rb") as file:
                            st.download_button("📥 Lejupielādēt", file, "reels.mp4", "video/mp4")
                        st.balloons()
                else:
                    st.error("Video netika atrasts.")
            else:
                st.error("Neizdevās pieslēgties nevienam Google AI modelim. Pārbaudi API atslēgu!")
