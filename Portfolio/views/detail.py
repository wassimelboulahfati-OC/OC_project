from pathlib import Path

import streamlit as st

from data.projects import PROJECTS
from utils import get_project, github_url, project_label

ROOT = Path(__file__).resolve().parent.parent

numbers = [p["number"] for p in PROJECTS]
st.session_state.setdefault("selected_project", numbers[0])


def go_to(offset: int) -> None:
    idx = numbers.index(st.session_state["selected_project"]) + offset
    st.session_state["selected_project"] = numbers[idx]


selected = st.selectbox(
    "Choisir un projet",
    numbers,
    key="selected_project",
    format_func=lambda n: project_label(get_project(n)),
)
p = get_project(selected)

st.title(p["title"])
meta = [p["category"], p["client"]] + ([p["period"]] if p["period"] else [])
st.caption(" · ".join(meta))
st.write(p["summary"])

tab_desc, tab_tools, tab_results, tab_value = st.tabs(
    ["Description", "Outils", "Résultats", "Compétences & valeur ajoutée"]
)

with tab_desc:
    st.subheader("Contexte")
    st.write(p["context"])
    st.subheader("Démarche")
    for step in p["approach"]:
        st.markdown(f"- {step}")

with tab_tools:
    st.subheader("Outils utilisés")
    st.markdown(" ".join(f"`{t}`" for t in p["tools"]))

with tab_results:
    st.subheader("Résultats obtenus")
    for item in p["results"]:
        st.markdown(f"- {item}")
    if p["images"]:
        st.subheader("Illustrations")
        cols = st.columns(len(p["images"]))
        for col, (caption, rel_path) in zip(cols, p["images"]):
            col.image(str(ROOT / rel_path), caption=caption)
    if p["limits"]:
        st.subheader("Limites et perspectives")
        for item in p["limits"]:
            st.markdown(f"- {item}")

with tab_value:
    st.subheader("Compétences démontrées")
    st.markdown(" ".join(f"`{s}`" for s in p["skills"]))
    st.subheader("Valeur ajoutée")
    st.info(p["value"])

st.divider()
st.subheader("Livrables et code")
st.link_button("Dossier du projet sur GitHub", github_url(p["folder"]))
for label, path in p["deliverables"]:
    st.markdown(f"- [{label}]({github_url(p['folder'], path)})")

prev_col, next_col = st.columns(2)
idx = numbers.index(selected)
if idx > 0:
    prev_col.button("← Projet précédent", on_click=go_to, args=(-1,), use_container_width=True)
if idx < len(numbers) - 1:
    next_col.button("Projet suivant →", on_click=go_to, args=(1,), use_container_width=True)
