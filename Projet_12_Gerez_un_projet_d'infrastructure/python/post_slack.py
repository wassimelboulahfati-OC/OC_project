import os
import json
import time

import requests
import urllib3

WEBHOOK = os.environ["SLACK_WEBHOOK_URL"]
VERIFY = os.getenv("SLACK_VERIFY_SSL", "true").lower() != "false"
if not VERIFY:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

activites = json.loads(os.getenv("ACTIVITES_JSON", "[]"))

# Emoji selon le type d'activite
EMOJIS = {
    "Marche/running": ":running:",
    "Vélo/Trottinette/Autres": ":bike:",
    "Natation": ":swimmer:",
    "Musculation": ":muscle:",
}

if not activites:
    print("Aucune activité hier — aucun message envoyé.")
else:
    envoyes = 0
    for act in activites:
        nom = act.get("nom_complet", "Un salarié")
        type_act = act.get("type_activite", "activité")
        emoji = EMOJIS.get(type_act, ":sports_medal:")

        texte = f"{emoji} Bravo *{nom}* pour ta séance de *{type_act}* hier ! :clap:"

        resp = requests.post(
            WEBHOOK,
            json={"text": texte},
            verify=VERIFY,
            timeout=20,
        )
        resp.raise_for_status()
        envoyes += 1
        time.sleep(1.1)  # throttling anti rate-limit Slack (~1 msg/s)

    print(f"{envoyes} message(s) Slack envoyé(s).")
