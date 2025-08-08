
import json
import os

USER_FILE = "backend/users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return []
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

def add_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

def remove_user(user_id):
    users = load_users()
    if user_id in users:
        users.remove(user_id)
        save_users(users)
