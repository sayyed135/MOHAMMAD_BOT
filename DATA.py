import json
import os

DATA_FILE = "DATA.json"

# اطمینان از وجود فایل و ساختار اولیه
def ensure_data_file():
    if not os.path.exists(DATA_FILE):
        data = {
            "users": {}
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

# بارگذاری دیتا
def load_data():
    ensure_data_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ذخیره دیتا
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# اطمینان از وجود کاربر
def ensure_user(user_id, name):
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str not in data["users"]:
        data["users"][user_id_str] = {
            "name": name,
            "phone": None,
            "credit": 0,
            "crypto": {
                "Bitcoin": 0,
                "Toncoin": 0,
                "Tether": 0,
                "Euro": 0
            }
        }
        save_data(data)
    return data["users"][user_id_str]

# بروزرسانی اطلاعات کاربر
def update_user(user_id, user_data):
    data = load_data()
    user_id_str = str(user_id)
    data["users"][user_id_str] = user_data
