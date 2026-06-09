import requests
import json
import time

URL = "http://11.170.12.150:8000/tools/get_catalogo_datos"
print("Testing get_catalogo_datos with 60s timeout...")
start_time = time.time()
try:
    r = requests.post(URL, json={"limit": 50}, timeout=60)
    elapsed = time.time() - start_time
    print(f"Status Code: {r.status_code}")
    print(f"Time taken: {elapsed:.2f} seconds")
    if r.status_code == 200:
        result = r.json()
        print("Success! Number of items:", len(result))
        print("Sample item:", json.dumps(result[0] if result else {}, indent=2))
    else:
        print("Error response:", r.text)
except Exception as e:
    elapsed = time.time() - start_time
    print(f"Error after {elapsed:.2f} seconds: {e}")
