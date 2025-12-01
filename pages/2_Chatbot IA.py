import os
import streamlit as st
from dotenv import load_dotenv

# Ensure root import
import sys
import os as _os
root_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from chat_agent import run_agent
from styles import GLOBAL_STYLE

# Appliquer le style global
st.markdown(GLOBAL_STYLE, unsafe_allow_html=True)


def init_state():
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []  # list of {role, content}


def show_header():
    st.markdown('<h1 class="animate-fade-in">🤖 Assistant Météo Intelligent</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 1.1rem; opacity: 0.8; text-align: center;">Agent IA propulsé par LangChain & Groq — Réponses contextualisées et enrichies</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Context coords if set
    lat = st.session_state.get("latitude")
    lon = st.session_state.get("longitude")
    ville = st.session_state.get("ville_selectionnee")
    
    st.markdown('<div class="weather-card">', unsafe_allow_html=True)
    if lat is not None and lon is not None:
        st.success(f"📍 **Contexte actif :** {ville or 'N/A'} — ({lat:.4f}, {lon:.4f})")
        st.info("💡 L'assistant peut maintenant vous donner des prévisions précises et des recommandations pour cette ville !")
    else:
        st.warning("⚠️ Aucune ville sélectionnée — Retournez à l'accueil pour choisir une ville.")
    st.markdown('</div>', unsafe_allow_html=True)


def show_chat():
    for m in st.session_state.chat_messages:
        with st.chat_message("assistant" if m["role"] == "assistant" else "user"):
            st.write(m["content"])

    user_input = st.chat_input("Posez votre question météo…")
    if user_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Réflexion de l'agent…"):
                try:
                    answer = run_agent(user_input, st.session_state.chat_messages)
                except RuntimeError as e:
                    st.error(str(e))
                    return
                except Exception as e:
                    st.error(f"Erreur agent: {e}")
                    return
                st.write(answer)
                st.session_state.chat_messages.append({"role": "assistant", "content": answer})


def main():
    load_dotenv()
    init_state()
    show_header()

    # Quick actions
    c1, c2, c3, c4 = st.columns(4)
    quick_action_triggered = False
    with c1:
        if st.button("🌤️ Météo actuelle"):
            st.session_state.chat_messages.append({"role": "user", "content": "Donne un résumé météo actuel."})
            quick_action_triggered = True
    with c2:
        if st.button("⏱ Prochaines heures"):
            st.session_state.chat_messages.append({"role": "user", "content": "Quelles sont les prévisions des prochaines heures ?"})
            quick_action_triggered = True
    with c3:
        if st.button("📿 Saint du jour"):
            st.session_state.chat_messages.append({"role": "user", "content": "Quel est le saint du jour ?"})
            quick_action_triggered = True
    with c4:
        if st.button("😄 Blague"):
            st.session_state.chat_messages.append({"role": "user", "content": "Raconte une courte blague."})
            quick_action_triggered = True

    # Si un bouton a été cliqué, on appelle l'agent
    if quick_action_triggered:
        user_msg = st.session_state.chat_messages[-1]["content"]
        with st.chat_message("assistant"):
            with st.spinner("Réflexion de l'agent…"):
                try:
                    answer = run_agent(user_msg, st.session_state.chat_messages[:-1])
                    st.session_state.chat_messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Erreur agent: {e}")
        st.rerun()

    show_chat()


main()
