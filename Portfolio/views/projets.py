import streamlit as st

from data.projects import CATEGORIES, PROJECTS
from utils import all_skills, all_tools, project_label, projects_table

pages = st.session_state["_pages"]

st.title("Récapitulatif des projets")
st.caption("Parcours Data Engineer : filtrez par domaine, outil ou compétence.")

with st.container(border=True):
    f1, f2, f3 = st.columns(3)
    categories = f1.multiselect("Domaine", CATEGORIES)
    tools = f2.multiselect("Outil", all_tools())
    skills = f3.multiselect("Compétence", all_skills())

filtered = [
    p
    for p in PROJECTS
    if (not categories or p["category"] in categories)
    and (not tools or set(tools) & set(p["tools"]))
    and (not skills or set(skills) & set(p["skills"]))
]

st.markdown(f"**{len(filtered)}** projet(s) affiché(s) sur {len(PROJECTS)}.")

if not filtered:
    st.info("Aucun projet ne correspond à ces filtres.")
    st.stop()

st.dataframe(projects_table(filtered), hide_index=True, use_container_width=True)

st.subheader("Fiches synthétiques")
for p in filtered:
    with st.container(border=True):
        head, action = st.columns([5, 1], vertical_alignment="center")
        head.markdown(f"### {project_label(p)}")
        head.caption(f"{p['category']} · {p['client']}" + (f" · {p['period']}" if p["period"] else ""))
        head.write(p["summary"])
        head.markdown(" ".join(f"`{t}`" for t in p["tools"]))
        if action.button("Voir le détail", key=f"detail-{p['number']}", use_container_width=True):
            st.session_state["selected_project"] = p["number"]
            st.switch_page(pages["detail"])
