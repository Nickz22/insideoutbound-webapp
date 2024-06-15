import os, json
from models import Filter, FilterContainer

CODE_VERIFIER_FILE = "code_verifier.json"
TOKEN_FILE = "tokens.json"
SETTINGS_FILE = "settings.json"

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

def custom_decoder(obj):
    if 'filters' in obj and 'name' in obj and 'filterLogic' in obj:
        return FilterContainer(name=obj['name'], filters=obj['filters'], filterLogic=obj['filterLogic'])
    if 'field' in obj and 'data_type' in obj and 'operator' in obj and 'value' in obj:
        return Filter(field=obj['field'], data_type=obj['data_type'], operator=obj['operator'], value=obj['value'])
    return obj

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as file:
            settings = json.load(file, object_hook=custom_decoder)
            return settings
    return None
