import streamlit as st
import requests
from sympy import sympify
import time
import wikipedia
import re

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
    st.session_state.history = []  # [{"role":"user"/"assistant", "content":"..."}]

# ---------------------------
# Utilitaires
# ---------------------------
def calculer(expr):
    try:
        return str(sympify(expr).evalf())
    except Exception:
        return "Erreur dans le calcul"

def est_calcul(expr):
    return all(c in "0123456789+-*/(). " for c in expr.strip())

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
    except Exception:
        return "Erreur météo"

# Recherche Wikipédia améliorée (gestion désambiguïsation)
def recherche_wiki(query):
    try:
        wikipedia.set_lang("fr")
        # première recherche pour obtenir la page la plus pertinente
        search_hits = wikipedia.search(query, results=5)
        if not search_hits:
            return "Aucun résultat Wikipédia trouvé."
        # si premier résultat correspond bien, on prend son résumé
        try:
            # tente d'obtenir un résumé du premier résultat
            title = search_hits[0]
            summary = wikipedia.summary(title, sentences=3)
            return f"Wikipedia — {title} :\n\n{summary}"
        except wikipedia.DisambiguationError as e:
            # si ambiguïté, renvoyer un message clair avec options
            options = e.options[:5]
            return ("Résultat ambigu sur Wikipédia. Choisis une option ou précise ta recherche :\n" +
                    "\n".join(f"- {opt}" for opt in options))
        except Exception:
            return "Problème avec Wikipédia pour ce sujet."
    except Exception:
        return "Erreur recherche Wikipédia."

def afficher_texte_animation(texte, vitesse=0.02):
    """Animation lettre par lettre sans toucher à l'historique"""
    affichage = ""
    placeholder = st.empty()
    for lettre in texte:
        affichage += lettre
        placeholder.text(f"IAdrix : {affichage}")
        time.sleep(vitesse)
    placeholder.empty()

def nettoie_reponse_du_role(text):
    """
    Si le modèle a récité une description du bot (cas fréquent),
    on enlève les phrases qui ressemblent à "Je suis IAdrix..." ou "Tu es IAdrix...".
    -> évite que l'IA nous ressorte sa fiche de poste.
    """
    # supprimer phrases contenant "Je suis IAdrix" ou "Tu es IAdrix" ou "assistant" descriptif
    patterns = [
        r"Je suis IAdrix[^\.\n]*[\.!\?]?", 
        r"Tu es IAdrix[^\.\n]*[\.!\?]?",
        r"Je suis un assistant[^\.\n]*[\.!\?]?",
        r"Je peux être sérieux[^\.\n]*[\.!\?]?"
    ]
    cleaned = text
    for p in patterns:
        cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE)
    # si après nettoyage il reste beaucoup de vide, retourne version originale courte
    if len(cleaned.strip()) < 10:
        return text.strip()
    # sinon retourne nettoyé et propre
    # retire espaces en double et début/fin blancs
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned

# ---------------------------
# Fonction IA (Mistral)
# ---------------------------
def obtenir_reponse_ia(question, echo_mode=False):
    """
    - echo_mode True : on demande AU MODELE de répéter exactement (prompt minimal)
    - echo_mode False: prompt système optimisé (sans la phrase demandée)
    """
    api_key = "yzmNsxBU31PkKWs7v4EGkbUeiLZvplpU"  # remplace si besoin
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    if echo_mode:
        messages = [{"role": "system", "content": "Répète exactement ce que l'utilisateur dit, sans rien ajouter, sans commentaire."}]
    else:
        # PROMPT SYSTÈME AMÉLIORÉ — plus direct, pas de phrase "Wesh..." et directive pour être concis
        messages = [{"role": "system", "content": (
            "Tu joues le rôle d'IAdrix, un pote drôle et direct. "
            "Réponds de façon naturelle, concise et utile. "
            "Si l'utilisateur demande une répétition exacte, obéis (mode echo). "
            "Ne dis jamais que tu es un assistant, et ne répète pas ce texte système. "
            "Si tu ne sais pas, dis simplement 'Je ne sais pas' et propose d'effectuer une recherche avec la commande 'cherche <sujet>'."
        )}]

    # Ajouter les 10 derniers messages du chat (user/assistant)
    for msg in st.session_state.history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Ajouter le message courant
    messages.append({"role": "user", "content": question})

    data = {"model": "open-mixtral-8x22b", "messages": messages}

    try:
        response = requests.post(url, json=data, headers=headers, timeout=20)
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content'].strip()
            # Nettoyage anti-répétition du rôle
            content = nettoie_reponse_du_role(content)
            # Ajout unique à l'historique
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
    # Ajout du message utilisateur dans l'historique (unique)
    st.session_state.history.append({"role": "user", "content": texte})
    cmd = texte.lower().strip()

    # Mode echo (détecte "répète après moi" ou "repete apres moi")
    if "répète après moi" in cmd or "repete apres moi" in cmd:
        echo_mode = True
        # on récupère la partie à répéter : tout après "après moi"
        # si l'utilisateur n'a rien après, on garde le texte entier
        parts = re.split(r"après moi|apres moi", texte, flags=re.IGNORECASE)
        texte_a_repeater = parts[-1].strip() if len(parts) > 1 and parts[-1].strip() else texte
    else:
        echo_mode = False
        texte_a_repeater = texte

    # Commandes directes : calc / meteo / cherche
    if cmd.startswith("calc ") or est_calcul(texte):
        res = calculer(texte[5:].strip() if cmd.startswith("calc ") else texte)
        assistant_text = f"Résultat → {res}"
        st.session_state.history.append({"role": "assistant", "content": assistant_text})
        afficher_texte_animation(assistant_text)

    elif cmd.startswith("meteo "):
        ville = texte[6:].strip()
        meteo = get_weather(ville)
        st.session_state.history.append({"role": "assistant", "content": meteo})
        afficher_texte_animation(meteo)

    elif cmd.startswith("cherche ") or cmd.startswith("qui est "):
        # On essaie Wikipédia d'abord
        query = re.sub(r'^(cherche|qui est)\s+', '', texte, flags=re.IGNORECASE).strip()
        res = recherche_wiki(query)
        st.session_state.history.append({"role": "assistant", "content": res})
        afficher_texte_animation(res)

    else:
        # Appel normal à l'IA (echo_mode géré)
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
