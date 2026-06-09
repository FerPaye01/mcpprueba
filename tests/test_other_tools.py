import requests
import json
import time

def check_get(name, params=None):
    url = f"http://11.170.12.150:8000/tools/{name}"
    print(f"\nTesting GET {url} with parameters {params}...")
    start_time = time.time()
    try:
        r = requests.get(url, params=params or {}, timeout=10)
        elapsed = time.time() - start_time
        print(f"Status Code: {r.status_code}")
        print(f"Time taken: {elapsed:.2f} seconds")
        if r.status_code == 200:
            result = r.json()
            print("Success! Number of items/length:", len(result))
            print("Sample item:", json.dumps(result[0] if isinstance(result, list) and result else result, indent=2)[:300])
        else:
            print("Error response:", r.text)
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"Error after {elapsed:.2f} seconds: {e}")

if __name__ == "__main__":
    check_get("get_unidades", {"limit": 5})
    check_get("get_catalogo_datos", {"limit": 5})
