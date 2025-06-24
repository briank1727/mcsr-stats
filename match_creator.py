import requests
import json
from datetime import datetime
import os

matchIds = []

res = requests.get(
    f"https://mcsrranked.com/api/users/LazarBim/matches?type=2&count=100"
)
try:
    res = res.json()
    if res["status"] == "success":
        for match in res["data"]:
            matchIds.append(match["id"])
    else:
        print(res)
except Exception as e:
    print(f"{e}")
    exit()

now = datetime.now()
month = now.month
day = now.day
year = now.year

folder_name = f"matches/{month}_{day}_{year}"
os.makedirs(folder_name, exist_ok=True)

for matchId in matchIds:
    res = requests.get(f"https://mcsrranked.com/api/matches/{matchId}")
    try:
        res = res.json()
        if res["status"] == "success":
            with open(f"{folder_name}/{matchId}.json", "w") as f:
                json.dump(res["data"], f, indent=4)  # pretty-print with indent
                print(f"{matchId} processed")
    except Exception as e:
        print(e)
