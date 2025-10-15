import streamlit as st
import requests
import wikipedia
import json

# --- CONFIG DE LA PAGE ---
st.set_page_config(page_title="IAdrix 💻", page_icon="💻", layout="wide")

# --- STYLE ---
st.markdown("""
    <style>
        body {background-color: #0e1117;}
        .stTextInput > div > div > input {
            border: 1px solid #00FFFF;
            background-color: #1e2228;
            color: white;
        }
        .stButton>button {
            background-color: #00FFFF;
            color: black;
            font-weight: bold;
            border-radius: 8px;
        }
        .chat-container {
            background-color: #1e2228;
            border-radius: 12px;
            padding: 15px;
            color: white;
            margin-bottom: 10px;
        }
        .user {color: #00FFFF; font-weight: bold;}
        .iadrix {color: #00FF7F; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# --- MÉMOIRE DE DISCUSSION ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- FONCTION MISTRAL ---
def mistral_chat(prompt, api_key):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [{"role": "system", "content": "Tu es IAdrix, une IA stylée, drôle, et familière, mais toujours claire. Tu réponds naturellement, sans exagérer. Si tu ne connais pas une réponse, tu le dis simplement."}]
    for msg in st.session_state.chat_history[-6:]:
        messages.append({"role": "user", "content": msg["user"]})
        messages.append({"role": "assistant", "content": msg["bot"]})
    messages.append({"role": "user", "content": prompt})

    data = {"model": "mistral-large-latest", "messages": messages}

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return "Erreur API Mistral 🤖"

# --- FONCTION WIKIPEDIA ---
def rechercher_wikipedia(query):
    try:
        wikipedia.set_lang("fr")
        return wikipedia.summary(query, sentences=2)
    except:
        return "Je n'ai rien trouvé sur Wikipédia à ce sujet 🤔"

# --- INTERFACE ---
st.title("💻 IAdrix – Chat IA Multifonction")

api_key = st.text_input("🔑 Entre ta clé API Mistral (commence par 'mistral-...') :", type="password")

# Entrée utilisateur
user_input = st.text_input("💬 Écris ton message :", key="input", placeholder="Parle à IAdrix ici...", label_visibility="collapsed")

# Envoi via Entrée ou bouton
if st.session_state.get("input") and (st.session_state.get("send_button") or st.session_state.get("enter_pressed", False)):
    if not api_key:
        bot_reply = "Il me faut ta clé API Mistral pour répondre 🤖"
    else:
        bot_reply = mistral_chat(user_input, api_key)
        if "je ne sais pas" in bot_reply.lower() or "aucune idée" in bot_reply.lower():
            bot_reply = rechercher_wikipedia(user_input)

    st.session_state.chat_history.append({"user": user_input, "bot": bot_reply})
    st.session_state.input = ""
    st.session_state.enter_pressed = False

# Bouton envoyer
if st.button("🚀 Envoyer", key="send_button"):
    st.session_state.enter_pressed = True
    st.rerun()

# --- AFFICHAGE CHAT ---
st.markdown("<hr>", unsafe_allow_html=True)
for msg in reversed(st.session_state.chat_history):
    st.markdown(f"<div class='chat-container'><span class='user'>Vous :</span> {msg['user']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chat-container'><span class='iadrix'>IAdrix :</span> {msg['bot']}</div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)
st.caption("💬 Tape ton message et appuie sur Entrée ou clique sur Envoyer.")

# --- SCRIPT POUR ENVOYER AVEC ENTRÉE ---
st.markdown("""
    <script>
    const input = window.parent.document.querySelector('input[type="text"]');
    input.addEventListener("keydown", function(event) {
        if (event.key === "Enter") {
            window.parent.document.querySelector('button[kind="secondary"]').click();
        }
    });
    </script>
""", unsafe_allow_html=True)
