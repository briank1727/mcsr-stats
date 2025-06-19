import requests
import json

res = requests.get(
    f"https://mcsrranked.com/api/users/LazarBim/matches?type=2&count=100"
)
with open("matchIds.txt", "a") as f:
    try:
        res = res.json()
        if res["status"] == "success":
            for match in res["data"]:
                print(match["id"], file=f)
        else:
            print(res)
    except Exception as e:
        print(f"{e}")
