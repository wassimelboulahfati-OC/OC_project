import streamlit as st

from data.profile import PROFILE

st.set_page_config(
    page_title=f"Portfolio · {PROFILE['name']}",
    page_icon="📊",
    layout="wide",
)

pages = {
    "accueil": st.Page("views/accueil.py", title="Accueil", icon="🏠", default=True),
    "projets": st.Page("views/projets.py", title="Récapitulatif des projets", icon="🗂️"),
    "detail": st.Page("views/detail.py", title="Détail d'un projet", icon="🔍"),
    "competences": st.Page("views/competences.py", title="Compétences & valeur ajoutée", icon="🧠"),
}
st.session_state["_pages"] = pages

with st.sidebar:
    st.markdown(f"**{PROFILE['name']}**  \n{PROFILE['title']}")
    for label, url in PROFILE["links"].items():
        if url:
            st.link_button(label, url, use_container_width=True)

st.navigation(list(pages.values())).run()
