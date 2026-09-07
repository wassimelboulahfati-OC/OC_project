# -*- coding: utf-8 -*-
"""
post_slack.py
-------------
Publie le digest sportif sur Slack à partir des KPI passés en
variables d'environnement (calculés en amont par une requête Kestra).
Contourne l'inspection SSL de l'entreprise (SLACK_VERIFY_SSL=false).
"""

import os
import requests

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
NB_ACTIVITES = os.getenv("NB_ACTIVITES", "0")
NB_SALARIES = os.getenv("NB_SALARIES", "0")
TOP_SALARIES = os.getenv("TOP_SALARIES", "aucun")
TOP_ACTIVITES = os.getenv("TOP_ACTIVITES", "aucune")
FENETRE_JOURS = os.getenv("FENETRE_JOURS", "30")
VERIFY_SSL = os.getenv("SLACK_VERIFY_SSL", "true").lower() != "false"

if not VERIFY_SSL:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    if not SLACK_WEBHOOK_URL:
        raise RuntimeError("SLACK_WEBHOOK_URL introuvable.")

    message = (
        f":trophy: *Défi sport du mois !*\n\n"
        f"Sur les {FENETRE_JOURS} derniers jours : "
        f"*{NB_ACTIVITES} activités* réalisées par "
        f"*{NB_SALARIES} salariés* ! :muscle:\n\n"
        f":first_place_medal: *Podium des plus actifs :* {TOP_SALARIES}\n"
        f":running: *Sports les plus pratiqués :* {TOP_ACTIVITES}\n\n"
        f"Bravo à toutes et tous, continuez comme ça ! :bike: :swimmer:"
    )

    print("Message à publier :\n" + message + "\n")

    resp = requests.post(
        SLACK_WEBHOOK_URL,
        json={"text": message},
        timeout=15,
        verify=VERIFY_SSL,
    )
    resp.raise_for_status()
    print(f"Publié sur Slack (HTTP {resp.status_code}).")


if __name__ == "__main__":
    main()
