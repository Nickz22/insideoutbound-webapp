import os, json

CODE_VERIFIER_FILE = "code_verifier.json"
TOKEN_FILE = "tokens.json"


def save_code_verifier(code_verifier):
    with open(CODE_VERIFIER_FILE, "w") as f:
        json.dump({"code_verifier": code_verifier}, f)


def load_code_verifier():
    if os.path.exists(CODE_VERIFIER_FILE):
        with open(CODE_VERIFIER_FILE, "r") as f:
            data = json.load(f)
            return data.get("code_verifier")
    return None


def save_tokens(access_token, instance_url):
    with open(TOKEN_FILE, "w") as f:
        json.dump({"access_token": access_token, "instance_url": instance_url}, f)


def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            return data.get("access_token"), data.get("instance_url")
    return None, None
