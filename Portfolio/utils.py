"""Fonctions utilitaires partagées par les pages du portfolio."""

from collections import Counter
from urllib.parse import quote

import pandas as pd

from data.profile import REPO_TREE_URL
from data.projects import PROJECTS, SKILL_DESCRIPTIONS


def github_url(folder: str, path: str | None = None) -> str:
    """Construit l'URL GitHub d'un dossier de projet, ou d'un fichier de ce dossier."""
    parts = [quote(p) for p in folder.split("/")]
    if path:
        parts += [quote(p) for p in path.split("/")]
    return f"{REPO_TREE_URL}/{'/'.join(parts)}"


def project_label(project: dict) -> str:
    return f"Projet {project['number']} · {project['title']}"


def get_project(number: int) -> dict:
    return next(p for p in PROJECTS if p["number"] == number)


def all_tools() -> list[str]:
    return sorted({t for p in PROJECTS for t in p["tools"]}, key=str.lower)


def all_skills() -> list[str]:
    return sorted({s for p in PROJECTS for s in p["skills"]})


def tool_counts() -> pd.DataFrame:
    counts = Counter(t for p in PROJECTS for t in p["tools"])
    return (
        pd.DataFrame(counts.items(), columns=["Outil", "Projets"])
        .sort_values(["Projets", "Outil"], ascending=[False, True])
        .reset_index(drop=True)
    )


def skills_long() -> pd.DataFrame:
    """Une ligne par couple (compétence, projet) : sert à la matrice et aux comptages."""
    rows = [
        {"Compétence": s, "Projet": f"P{p['number']}", "Numéro": p["number"], "Titre": p["title"]}
        for p in PROJECTS
        for s in p["skills"]
    ]
    return pd.DataFrame(rows)


def skills_summary() -> pd.DataFrame:
    df = skills_long().groupby("Compétence").size().rename("Projets").reset_index()
    return df.sort_values(["Projets", "Compétence"], ascending=[False, True]).reset_index(drop=True)


def projects_table(projects: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "N°": [p["number"] for p in projects],
            "Projet": [p["title"] for p in projects],
            "Contexte": [p["client"] for p in projects],
            "Catégorie": [p["category"] for p in projects],
            "Outils": [", ".join(p["tools"]) for p in projects],
        }
    )


def skill_projects(skill: str) -> list[dict]:
    return [p for p in PROJECTS if skill in p["skills"]]


__all__ = [
    "SKILL_DESCRIPTIONS",
    "all_skills",
    "all_tools",
    "get_project",
    "github_url",
    "project_label",
    "projects_table",
    "skill_projects",
    "skills_long",
    "skills_summary",
    "tool_counts",
]
