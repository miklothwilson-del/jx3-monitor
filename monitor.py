import os
import json
import time
import smtplib
import subprocess
import requests

from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage

URL = "https://zhishui.cc/api/jx3/search/"
STATE_FILE = Path("state.json")

name = os.environ["ROLE_NAME"]
server = os.environ["ROLE_SERVER"]

def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    subprocess.run(["git", "config", "user.name", "JX3 Monitor"], check=True)
    subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
    subprocess.run(["git", "add", "state.json"], check=True)

    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode != 0:
        subprocess.run(["git", "commit", "-m", "Update monitor state"], check=True)
        subprocess.run(["git", "push"], check=True)

def send_email():
    msg = EmailMessage()
    msg["Subject"] = f"剑网三角色上线提醒：{name}"
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["SMTP_USER"]
    msg.set_content(f"角色 {name}（{server}）刚刚检测到上线！")

    with smtplib.SMTP_SSL("smtp.qq.com", 465) as smtp:
        smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        smtp.send_message(msg)

def stop_workflow():
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GITHUB_TOKEN"]

    response = requests.patch(
        f"https://api.github.com/repos/{repo}/actions/workflows/monitor.yml/disable",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        },
        timeout=20
    )
    response.raise_for_status()
    print("监控已满7天，自动停止。")

now = datetime.now(timezone.utc)

if STATE_FILE.exists():
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
else:
    state = {
        "started_at": now.isoformat(),
        "status": None
    }

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

if status not in (0, 1):
    raise RuntimeError(f"无法识别角色状态：{result}")

previous = state["status"]

if previous == 0 and status == 1:
    send_email()
    print("角色上线！QQ邮箱提醒已发送。")
elif status == 0:
    print("角色离线，不发送邮件。")
elif status == 1:
    print("角色在线。")
else:
    print("首次查询，已记录当前状态，不发送邮件。")

state["status"] = status
save_state(state)

print("查询完成。")
