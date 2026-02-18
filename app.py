import streamlit as st
import requests
import json
import re

st.set_page_config(page_title="AI Video Diagnostika", layout="centered")

st.title("🎥 AI Video Sistēma")

with st.sidebar:
    st.header("Iestatījumi")
    gemini_key = st.text_input("Gemini API Key", type="password")
    pexels_key = st.text_input("Pexels API Key", type="password")

topic = st.text_input("Ievadi video tēmu:")

def get_working_model(api_key):
    """Pajautā Google, kurš modelis ir pieejams šai atslēgai."""
    versions = ['v1beta', 'v1']
    for v in versions:
        url = f"https://generativelanguage.googleapis.com/{v}/models?key={api_key}"
        try:
            r = requests.get(url)
            models = r.json().get('models', [])
            for m in models:
                # Meklējam modeli, kas atbalsta teksta ģenerēšanu
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    return m['name'], v # Atgriež modeļa pilno ceļu un versiju
        except:
            continue
    return None, None

def get_ai_data(topic, api_key, model_path, version):
    url = f"https://generativelanguage.googleapis.com/{version}/{model_path}:generateContent?key={api_key}"
    prompt = (
        f"Generate a short motivational quote about '{topic}' in Latvian. "
        f"Provide a 1-2 word English search term for a background video. "
        f"Return ONLY JSON: {{\"quote\": \"...\", \"search_term\": \"...\"}}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    response = requests.post(url, json=payload)
    res_data = response.json()
    
    if 'error' in res_data:
        return None, res_data['error']['message']
        
    full_text = res_data['candidates'][0]['content']['parts'][0]['text']
    json_match = re.search(r'\{.*\}', full_text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group()), None
    return None, "Neizdevās nolasīt AI atbildi."

if st.button("Ģenerēt Video"):
    if not gemini_key or not pexels_key:
        st.error("Ievadi API atslēgas!")
    else:
        with st.spinner("Meklējam piemērotu AI modeli..."):
            model_path, version = get_working_model(gemini_key)
            
            if not model_path:
                st.error("Tavai API atslēgai nav pieejams neviens modelis. Pārbaudi atslēgu Google AI Studio!")
            else:
                st.info(f"Izmantojam: {model_path} ({version})")
                data, err = get_ai_data(topic, gemini_key, model_path, version)
                
                if err:
                    st.error(f"AI Kļūda: {err}")
                else:
                    st.subheader(f"📝 {data['quote']}")
                    
                    # Pexels daļa
                    px_url = f"https://api.pexels.com/videos/search?query={data['search_term']}&orientation=portrait&per_page=1"
                    px_res = requests.get(px_url, headers={"Authorization": pexels_key}).json()
                    
                    if px_res.get('videos'):
                        st.video(px_res['videos'][0]['video_files'][0]['link'])
                        st.success("Video atrasts!")
                    else:
                        st.warning("Video netika atrasts.")