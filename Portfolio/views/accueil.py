import streamlit as st

from data.profile import PROFILE
from data.projects import CATEGORIES, PROJECTS
from utils import all_skills, all_tools, tool_counts

pages = st.session_state["_pages"]

st.title(f"{PROFILE['name']}")
st.subheader(PROFILE["title"])
st.write(PROFILE["tagline"])
st.write(PROFILE["about"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Projets réalisés", len(PROJECTS))
col2.metric("Domaines couverts", len({p["category"] for p in PROJECTS}))
col3.metric("Outils & technologies", len(all_tools()))
col4.metric("Compétences démontrées", len(all_skills()))

st.divider()

st.header("Ce que contient ce portfolio")
nav1, nav2, nav3 = st.columns(3)
with nav1, st.container(border=True):
    st.markdown("#### 🗂️ Récapitulatif")
    st.write("Tous les projets du parcours Data Engineer, filtrables par domaine, outil ou compétence.")
    st.page_link(pages["projets"], label="Voir le récapitulatif", icon="➡️")
with nav2, st.container(border=True):
    st.markdown("#### 🔍 Détail des projets")
    st.write("Contexte, démarche, outils utilisés, résultats obtenus, limites et livrables de chaque projet.")
    st.page_link(pages["detail"], label="Explorer un projet", icon="➡️")
with nav3, st.container(border=True):
    st.markdown("#### 🧠 Compétences")
    st.write("Les compétences démontrées, les projets qui les prouvent et la valeur ajoutée pour une équipe.")
    st.page_link(pages["competences"], label="Voir les compétences", icon="➡️")

st.divider()

st.header("Le parcours en un coup d'œil")
for category in CATEGORIES:
    items = [p for p in PROJECTS if p["category"] == category]
    if not items:
        continue
    st.markdown(f"**{category}**")
    for p in items:
        st.markdown(f"- Projet {p['number']} · {p['title']} : {p['summary']}")

st.divider()

st.header("Outils les plus utilisés")
counts = tool_counts().head(12).set_index("Outil")
st.bar_chart(counts, horizontal=True)
