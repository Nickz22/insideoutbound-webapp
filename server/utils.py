import uuid

def pluck(arr, param):
    return [d[param] for d in arr if param in d]

def generate_unique_id():
    return str(uuid.uuid4())