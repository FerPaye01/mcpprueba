import requests
import json

URL_BASE = "http://11.170.12.150:8000"

def check_endpoint(path, method="GET", json_data=None):
    url = f"{URL_BASE}{path}"
    print(f"\n--- Checking {method} {url} ---")
    try:
        if method == "GET":
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json=json_data or {}, timeout=5)
        print("Status Code:", r.status_code)
        print("Headers:", dict(r.headers))
        print("Content (first 200 chars):", r.text[:200])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    check_endpoint("/sse")
    check_endpoint("/tools/list")
    check_endpoint("/tools/get_catalogo_datos", method="POST")
    check_endpoint("/tools")
    check_endpoint("/message", method="POST")
