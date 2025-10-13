import streamlit as st
import requests
from sympy import sympify
import time

# ---------------------------
# Config Streamlit
# ---------------------------
st.set_page_config(page_title="IAdrix 💻", layout="wide")
st.markdown("""
<style>
body {background-color: white; color: #00AA00; font-family: monospace;}
.stTextInput>div>div>input {background-color: white; color: #00AA00; font-family: monospace;}
.stButton>button {background-color: #111; color: #00AA00; font-family: monospace;}
div.stScrollView > div {scroll-behavior: smooth;}
</style>
""", unsafe_allow_html=True)
st.title("IAdrix 💻")

# ---------------------------
# Session state
# ---------------------------
if "history" not in st.session_state:
    st.session_state.history = []  # format : [{"role": "user"/"assistant", "content": "..."}]

# ---------------------------
# Fonctions utilitaires
# ---------------------------
def calculer(expr):
    try:
        return str(sympify(expr).evalf())
    except:
        return "Erreur dans le calcul"

def est_calcul(expr):
    return all(c in "0123456789+-*/(). " for c in expr)

def get_weather(city):
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1").json()
        if "results" not in geo or len(geo["results"]) == 0:
            return "Ville introuvable."
        lat, lon = geo["results"][0]["latitude"], geo["results"][0]["longitude"]
        city_name = geo["results"][0].get("name", city)
        m = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto").json()
        cw = m.get("current_weather", {})
        if not cw:
            return "Pas de données météo."
        return f"{city_name} — {cw['temperature']}°C, vent {cw['windspeed']} km/h"
    except:
        return "Erreur météo"

def afficher_texte_animation(texte, vitesse=0.02):
    """Affiche le texte de l'assistant lettre par lettre sans toucher à l'historique"""
    affichage = ""
    placeholder = st.empty()
    for lettre in texte:
        affichage += lettre
        placeholder.text(f"IAdrix : {affichage}")
        time.sleep(vitesse)
    placeholder.empty()

def obtenir_reponse_ia(question):
    """Appelle l'IA Mistral avec historique complet et renvoie la réponse"""
    api_key = "yzmNsxBU31PkKWs7v4EGkbUeiLZvplpU"
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Messages formatés pour Mistral
    messages = [{"role": "system", "content": (
        "Tu es IAdrix, un assistant drôle, curieux et enthousiaste. "
        "Tu parles comme un pote, naturel. "
        "Mais sois sérieux si on te demande une explication ou un service. "
        "Ne répète jamais tes qualités, sois fluide et cohérent."
        "tu dois etre sympa tu peux clasher l'utilisateur si nécessaire pour rigoler"
    )}]

    # Ajout de l'historique récent
    for msg in st.session_state.history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Ajout du message actuel
    messages.append({"role": "user", "content": question})

    data = {"model": "open-mixtral-8x22b", "messages": messages}

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            # Ajout dans l'historique
            st.session_state.history.append({"role": "assistant", "content": content})
            return content
        else:
            return f"Erreur API {response.status_code}"
    except Exception as e:
        return f"Erreur API: {e}"

# ---------------------------
# Input utilisateur
# ---------------------------
texte = st.text_input("Vous :", value="", key="input_text")
envoyer = st.button("Envoyer")

# ---------------------------
# Logique principale
# ---------------------------
if envoyer and texte:
    st.session_state.history.append({"role": "user", "content": texte})
    cmd = texte.lower().strip()

    if cmd.startswith("calc ") or est_calcul(texte):
        res = calculer(texte[5:].strip() if cmd.startswith("calc ") else texte)
        afficher_texte_animation(f"Résultat → {res}")
        st.session_state.history.append({"role": "assistant", "content": f"Résultat → {res}"})
    elif cmd.startswith("meteo "):
        ville = texte[6:].strip()
        meteo = get_weather(ville)
        afficher_texte_animation(meteo)
        st.session_state.history.append({"role": "assistant", "content": meteo})
    else:
        ia_res = obtenir_reponse_ia(texte)
        afficher_texte_animation(ia_res)

# ---------------------------
# Affichage historique
# ---------------------------
for msg in st.session_state.history:
    prefix = "Vous : " if msg["role"] == "user" else "IAdrix : "
    st.text(prefix + msg["content"])

# Scroll auto
st.markdown("<script>window.scrollTo(0, document.body.scrollHeight);</script>", unsafe_allow_html=True)
