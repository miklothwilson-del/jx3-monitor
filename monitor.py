import requests
import time
import os

URL = "https://zhishui.cc/api/jx3/search/"

name = os.environ["ROLE_NAME"]
server = os.environ["ROLE_SERVER"]

payload = {
    "username": name,
    "server": server,
    "pvp_type": "3",
    "cursor": 0,
    "page_size": 200
}

response = requests.post(URL, json=payload, timeout=20)
response.raise_for_status()

result = response.json()
status = result.get("data", {}).get("game_login")

if status == 1:
    print("角色在线！")
elif status == 0:
    print("角色离线。")
else:
    print("无法识别状态：", result)
