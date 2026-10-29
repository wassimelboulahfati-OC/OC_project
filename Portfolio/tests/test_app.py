import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
APP = str(ROOT / "app.py")

PAGES = ["views/accueil.py", "views/projets.py", "views/detail.py", "views/competences.py"]


@pytest.mark.parametrize("page", PAGES)
def test_page_runs_without_exception(page):
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.switch_page(page).run()
    assert not at.exception, [e.value for e in at.exception]


def test_every_project_detail_renders():
    from data.projects import PROJECTS

    at = AppTest.from_file(APP, default_timeout=30).run()
    at.switch_page("views/detail.py").run()
    for p in PROJECTS:
        at.selectbox[0].set_value(p["number"]).run()
        assert not at.exception, (p["number"], [e.value for e in at.exception])
        assert at.title[0].value == p["title"]

    # Dernier projet sélectionné : seul le bouton « précédent » existe.
    at.button[-1].click().run()
    assert not at.exception
    assert at.selectbox[0].value == PROJECTS[-2]["number"]


def test_detail_button_opens_selected_project():
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.switch_page("views/projets.py").run()
    at.button(key="detail-5").click().run()
    assert not at.exception
    assert at.selectbox[0].value == 5


def test_projects_data_is_consistent():
    from data.projects import CATEGORIES, PROJECTS, SKILL_DESCRIPTIONS

    assert len({p["number"] for p in PROJECTS}) == len(PROJECTS)
    for p in PROJECTS:
        assert p["category"] in CATEGORIES
        assert p["tools"] and p["results"] and p["approach"]
        assert set(p["skills"]) <= set(SKILL_DESCRIPTIONS), p["number"]
