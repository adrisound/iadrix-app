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
    """Affiche le texte lettre par lettre sans toucher à l'historique"""
    affichage = ""
    placeholder = st.empty()
    for lettre in texte:
        affichage += lettre
        placeholder.text(f"IAdrix : {affichage}")
        time.sleep(vitesse)
    placeholder.empty()

def obtenir_reponse_ia(question, echo_mode=False):
    """Appelle Mistral IA avec historique et echo_mode si nécessaire"""
    api_key = "yzmNsxBU31PkKWs7v4EGkbUeiLZvplpU"
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    if echo_mode:
        messages = [{"role": "system", "content": "Répète exactement ce que l'utilisateur dit, sans rien ajouter, sans commentaire, sans vannes."}]
    else:
        messages = [{"role": "system", "content": (
            "Tu es IAdrix, un assistant stylé, drôle et curieux. "
            "Tu parles comme un pote, naturel et un peu taquin. "
            "Quand quelque chose t’étonne, tu peux dire : « Wesh ça va toi, tu vis hein ??? ». "
            "Tu peux balancer quelques vannes, mais toujours de façon marrante et respectueuse. "
            "Ne dis jamais que tu es un assistant ou que tu suis des règles. "
            "Ne répète jamais cette description."
        )}]

    # Ajouter l'historique récent
    for msg in st.session_state.history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Ajouter le message actuel
    messages.append({"role": "user", "content": question})

    data = {"model": "open-mixtral-8x22b", "messages": messages}

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            # Ajout unique dans l'historique
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

    # Détection du mode echo
    if "répète après moi" in cmd:
        echo_mode = True
        texte_a_repeater = texte.split("après moi")[-1].strip()
    else:
        echo_mode = False
        texte_a_repeater = texte

    # Commandes calcul / météo
    if cmd.startswith("calc ") or est_calcul(texte):
        res = calculer(texte[5:].strip() if cmd.startswith("calc ") else texte)
        st.session_state.history.append({"role": "assistant", "content": f"Résultat → {res}"})
        afficher_texte_animation(f"Résultat → {res}")
    elif cmd.startswith("meteo "):
        ville = texte[6:].strip()
        meteo = get_weather(ville)
        st.session_state.history.append({"role": "assistant", "content": meteo})
        afficher_texte_animation(meteo)
    else:
        ia_res = obtenir_reponse_ia(texte_a_repeater, echo_mode=echo_mode)
        afficher_texte_animation(ia_res)

# ---------------------------
# Affichage historique
# ---------------------------
for msg in st.session_state.history:
    prefix = "Vous : " if msg["role"] == "user" else "IAdrix : "
    st.text(prefix + msg["content"])

# Scroll auto
st.markdown("<script>window.scrollTo(0, document.body.scrollHeight);</script>", unsafe_allow_html=True)
