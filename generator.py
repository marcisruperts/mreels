import requests
import json
import re

# --- KONFIGURĀCIJA ---
GEMINI_API_KEY = "AIzaSyDyx8B-daWY64dnvuEMIiHpQMKc9ec9xVo"
PEXELS_API_KEY = "QCUuUAuUUWGoXvqQYLU8vSfhnbxSn1XBBgDE759PBiH79pmf67ttXtpS"

def get_available_model():
    """Pārbauda, kuri modeļi ir pieejami tavai API atslēgai."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        response = requests.get(url)
        models = response.json().get('models', [])
        # Meklējam jebkuru modeli, kas atbalsta satura ģenerēšanu
        for m in models:
            if 'generateContent' in m['supportedGenerationMethods']:
                return m['name'] # Atgriež piemēram 'models/gemini-1.5-flash'
    except:
        pass
    return "models/gemini-1.5-flash" # Rezerves variants

def get_ai_content(topic, model_name):
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    prompt = (
        f"Generate a short motivational quote about '{topic}' in Latvian. "
        f"Provide a 1-2 word English search term for a background video. "
        f"Return ONLY JSON: {{\"quote\": \"...\", \"search_term\": \"...\"}}"
    )
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload)
        res_data = response.json()
        
        if 'error' in res_data:
            return None, res_data['error']['message']
            
        full_text = res_data['candidates'][0]['content']['parts'][0]['text']
        json_match = re.search(r'\{.*\}', full_text, re.DOTALL)
        return json.loads(json_match.group()), None
    except Exception as e:
        return None, str(e)

def get_pexels_video(search_term):
    url = f"https://api.pexels.com/videos/search?query={search_term}&orientation=portrait&per_page=1"
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        return data['videos'][0]['video_files'][0]['link'] if data.get('videos') else None
    except:
        return None

# --- IZPILDE ---
print("🔍 Meklējam tev pieejamos modeļus...")
best_model = get_available_model()
print(f"✅ Izmantosim modeli: {best_model}")

data, err = get_ai_content("hard work", best_model)

if data:
    print(f"📝 Citāts: {data['quote']}")
    video_link = get_pexels_video(data['search_term'])
    if video_link:
        print(f"\n🏆 VIDEO SAITE: {video_link}")
    else:
        print("❌ Video netika atrasts.")
else:
    print(f"❌ Kļūda: {err}")