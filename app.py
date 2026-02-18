import streamlit as st
import requests
import json
import re
import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings

# KONFIGURĀCIJA STREAMLIT MĀKONIM
# Linux vidē ImageMagick parasti atrodas šajā ceļā:
if os.path.exists("/usr/bin/convert"):
    change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

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
                # Atgriežam tikai nosaukumu, bez 'models/' prefiksa, ja nepieciešams, 
                # bet mūsu funkcija apstrādā pilnu ceļu
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
    
    if 'candidates' not in res_data:
        st.error(f"API Atbilde: {res_data}")
        return None
        
    full_text = res_data['candidates'][0]['content']['parts'][0]['text']
    json_match = re.search(r'\{.*\}', full_text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return None

# --- MONTĀŽAS FUNKCIJA ---
def process_video(video_url, quote):
    temp_raw = "raw_video.mp4"
    output_file = "final_reel.mp4"
    
    st.write("📥 Lejupielādē fonu...")
    video_data = requests.get(video_url).content
    with open(temp_raw, "wb") as f:
        f.write(video_data)
    
    st.write("🎨 Notiek montāža (tas var aizņemt minūti)...")
    
    try:
        # Izmantojam 'with' konstrukciju, lai resursi tiktu atbrīvoti
        with VideoFileClip(temp_raw) as clip:
            # Saīsinām līdz 5 sekundēm un pielāgojam izmēru, ja nepieciešams
            clip = clip.subclip(0, 5)
            
            # Izveidojam tekstu
            # Font 'Liberation-Sans' parasti ir pieejams Linux serveros
            txt_clip = TextClip(
                quote, 
                fontsize=40, 
                color='white', 
                font='Liberation-Sans', 
                method='caption', 
                size=(clip.w * 0.8, None),
                align='center'
            ).set_duration(5).set_position('center')
            
            # Apvienojam
            final = CompositeVideoClip([clip, txt_clip])
            
            # Saglabājam
            final.write_videofile(
                output_file, 
                fps=24, 
                codec="libx264", 
                audio=False,
                logger=None # Noņem lieko tekstu no ekrāna
            )
            
            # Aizveram apakšklipus
            txt_clip.close()
            final.close()
            
        return output_file
    except Exception as e:
        st.error(f"Montāžas kļūda: {str(e)}")
        return None

# --- INTERFEISS ---
if st.button("Sākt procesu"):
    if not gemini_key or not pexels_key or not topic:
        st.error("Aizpildi visus laukus!")
    else:
        with st.spinner("Sistēma strādā..."):
            # 1. Atrodam modeli
            model_path, version = get_working_model(gemini_key)
            
            if model_path:
                # 2. Iegūstam AI saturu
                data = get_ai_data(topic, gemini_key, model_path, version)
                
                if data:
                    st.write(f"📝 **Citāts:** {data['quote']}")
                    
                    # 3. Pexels meklēšana
                    px_url = f"https://api.pexels.com/videos/search?query={data['search_term']}&orientation=portrait&per_page=1"
                    px_headers = {"Authorization": pexels_key}
                    px_res = requests.get(px_url, headers=px_headers).json()
                    
                    if px_res.get('videos'):
                        video_link = px_res['videos'][0]['video_files'][0]['link']
                        
                        # 4. Sākam montāžu
                        final_path = process_video(video_link, data['quote'])
                        
                        if final_path and os.path.exists(final_path):
                            st.video(final_path)
                            
                            # 5. Lejupielādes poga
                            with open(final_path, "rb") as file:
                                st.download_button(
                                    label="📥 Lejupielādēt gatavu Video",
                                    data=file,
                                    file_name="mans_reels.mp4",
                                    mime="video/mp4"
                                )
                            st.balloons()
                    else:
                        st.error("Video netika atrasts Pexels datubāzē.")
                else:
                    st.error("Neizdevās iegūt datus no AI.")
            else:
                st.error("Neizdevās atrast strādājošu AI modeli.")

# Sakopjam failus pēc sesijas (pēc izvēles)
if os.path.exists("raw_video.mp4"):
    try: os.remove("raw_video.mp4")
    except: pass
