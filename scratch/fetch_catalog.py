import requests
import json

base_url = "http://10.10.17.216:8001"
name = "get_catalogo_datos"
url = f"{base_url}/tools/{name}"

try:
    r = requests.post(url, json={}, timeout=10)
    print(f"Status Code: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Count: {len(data)}")
        if data:
            print("First item keys:", list(data[0].keys()))
            print("First item sample:")
            print(json.dumps(data[0], indent=2, ensure_ascii=False))
            print("All table names:")
            for idx, item in enumerate(data):
                t_name = item.get("NO_TABLA") or item.get("table_name") or item.get("name")
                id_cat = item.get("ID_CATALOGO_DATO") or item.get("id_catalogo")
                schema = item.get("NO_ESQUEMA_ORIGEN") or item.get("schema")
                print(f"[{idx}] {schema}.{t_name} (ID: {id_cat})")
    else:
        print("Error content:", r.text)
except Exception as e:
    print("Exception occurred:", str(e))
