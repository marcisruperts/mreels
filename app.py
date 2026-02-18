def get_ai_data(topic, api_key):
    # Modeļu saraksts prioritātes secībā
    # Dažreiz v1beta prasa 'gemini-1.5-flash', dažreiz 'models/gemini-1.5-flash'
    models_to_try = [
        "gemini-2.0-flash-exp", 
        "gemini-1.5-flash", 
        "gemini-1.5-flash-8b",
        "gemini-pro"
    ]
    
    for model_name in models_to_try:
        # Mēģinām abus variantus: ar un bez 'models/' prefiksa
        for full_name in [model_name, f"models/{model_name}"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/{full_name}:generateContent?key={api_key}"
            
            payload = {
                "contents": [{"parts": [{"text": f"Generate a short motivational quote about '{topic}' in Latvian. Return ONLY JSON: {{\"quote\": \"...\", \"search_term\": \"1-2 words for pexels search\"}}"}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
            
            try:
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    res_data = response.json()
                    content_text = res_data['candidates'][0]['content']['parts'][0]['text']
                    return json.loads(content_text), full_name
            except:
                continue
                
    return None, None
