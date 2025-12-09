import json
import os

DATA_FILE = "DATA.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def ensure_user(user_id, name):
    data = load_data()
    if str(user_id) not in data["users"]:
        data["users"][str(user_id)] = {
            "name": name,
            "phone": None,
            "credit": 0,
            "crypto": {"BTC":0,"Tether":0,"TonCoin":0,"EUR":0}
        }
        save_data(data)
    return data["users"][str(user_id)]

def update_user(user_id, user_data):
    data = load_data()
    data["users"][str(user_id)] = user_data
    save_data(data)
