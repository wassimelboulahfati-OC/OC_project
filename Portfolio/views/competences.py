import altair as alt
import streamlit as st

from data.projects import SKILL_DESCRIPTIONS
from utils import skill_projects, skills_long, skills_summary

st.title("Compétences démontrées et valeur ajoutée")
st.write(
    "Chaque compétence est rattachée aux projets qui la prouvent. "
    "La matrice montre d'un coup d'œil où elle a été mise en pratique."
)

summary = skills_summary()
long_df = skills_long()

st.header("Matrice compétences × projets")
order = summary["Compétence"].tolist()
heatmap = (
    alt.Chart(long_df)
    .mark_rect(cornerRadius=3)
    .encode(
        x=alt.X("Projet:N", sort=alt.SortField("Numéro"), title=None, axis=alt.Axis(orient="top", labelAngle=0)),
        y=alt.Y("Compétence:N", sort=order, title=None, axis=alt.Axis(labelLimit=300)),
        color=alt.value("#2E86C1"),
        tooltip=["Compétence", "Titre"],
    )
    .properties(height=alt.Step(26))
)
st.altair_chart(heatmap, use_container_width=True)

st.header("Poids de chaque compétence")
st.bar_chart(summary.set_index("Compétence"), horizontal=True)

st.header("Détail par compétence")
for _, row in summary.iterrows():
    skill = row["Compétence"]
    demontre, valeur = SKILL_DESCRIPTIONS.get(skill, ("", ""))
    with st.expander(f"{skill} · {row['Projets']} projet(s)"):
        if demontre:
            st.markdown(f"**Ce que j'ai fait :** {demontre}")
        if valeur:
            st.markdown(f"**Valeur ajoutée :** {valeur}")
        st.markdown("**Projets :**")
        for p in skill_projects(skill):
            st.markdown(f"- Projet {p['number']} · {p['title']}")
