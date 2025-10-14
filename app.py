import streamlit as st
import requests
import wikipedia
import re

# ---------------------------
# Config Streamlit
# ---------------------------
st.set_page_config(page_title="IAdrix 💻", layout="wide")
st.markdown("""
<style>
body {background-color: #1E1E1E; color: #00FF00; font-family: monospace;}
.stTextInput>div>div>input {background-color: #000000; color: #00FF00; font-family: monospace;}
.stButton>button {background-color: #111111; color: #00FF00; font-family: monospace;}
div.stScrollView > div {scroll-behavior: smooth;}
.stMarkdown p {color:#00FF00;}
</style>
""", unsafe_allow_html=True)
st.title("IAdrix 💻")

# ---------------------------
# Mémoire chat
# ---------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# ---------------------------
# Fonctions utilitaires
# ---------------------------
def get_weather(city):
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1").json()
        if "results" not in geo or len(geo["results"]) == 0:
            return "Ville introuvable."
        lat, lon = geo["results"][0]["latitude"], geo["results"][0]["longitude"]
        city_name = geo["results"][0].get("name", city)
        m = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto").json()
        cw = m.get("current_weather", {})
        if not cw: return "Pas de données météo."
        return f"{city_name} — {cw['temperature']}°C, vent {cw['windspeed']} km/h"
    except:
        return "Erreur météo"

def recherche_wiki(query):
    try:
        wikipedia.set_lang("fr")
        search_hits = wikipedia.search(query, results=5)
        if not search_hits: return "Aucun résultat Wikipédia trouvé."
        try:
            title = search_hits[0]
            summary = wikipedia.summary(title, sentences=3)
            return f"Wikipedia — {title} :\n\n{summary}"
        except wikipedia.DisambiguationError as e:
            options = e.options[:5]
            return "Résultat ambigu, précise ta recherche :\n" + "\n".join(f"- {opt}" for opt in options)
        except:
            return "Problème avec Wikipédia pour ce sujet."
    except:
        return "Erreur recherche Wikipédia."

def obtenir_reponse_ia(question):
    api_key = "yzmNsxBU31PkKWs7v4EGkbUeiLZvplpU"
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    messages = [{"role": "system", "content": (
        "Tu joues le rôle d'IAdrix, un pote drôle et direct. "
        "Réponds de façon naturelle, concise et utile. "
        "Ne dis jamais que tu es un assistant. "
        "Si tu ne sais pas, dis 'Je ne sais pas' et propose 'cherche <sujet>'."
    )}]
    for msg in st.session_state.history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})
    data = {"model": "open-mixtral-8x22b", "messages": messages}

    try:
        response = requests.post(url, json=data, headers=headers, timeout=20)
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content'].strip()
            st.session_state.history.append({"role":"assistant","content":content})
            return content
        else:
            return f"Erreur API {response.status_code}"
    except Exception as e:
        return f"Erreur API: {e}"

# ---------------------------
# Input utilisateur (Entrée ou bouton)
# ---------------------------
with st.form("chat_form", clear_on_submit=True):
    texte = st.text_input("Vous :", key="input_text")
    envoyer = st.form_submit_button("Envoyer")

if envoyer and texte:
    st.session_state.history.append({"role":"user","content":texte})
    cmd = texte.lower().strip()

    if cmd.startswith("meteo "):
        res = get_weather(texte[6:].strip())
    elif cmd.startswith("cherche ") or cmd.startswith("qui est "):
        query = re.sub(r'^(cherche|qui est)\s+', '', texte, flags=re.IGNORECASE).strip()
        res = recherche_wiki(query)
    else:
        res = obtenir_reponse_ia(texte)

    st.session_state.history.append({"role":"assistant","content":res})

# ---------------------------
# Affichage historique stylé
# ---------------------------
for msg in st.session_state.history:
    if msg["role"]=="user":
        st.markdown(f"**Vous :** {msg['content']}")
    else:
        st.markdown(f"**IAdrix :** {msg['content']}")

# Scroll auto
st.markdown("<script>window.scrollTo(0, document.body.scrollHeight);</script>", unsafe_allow_html=True)
