import requests
import json

URL = "http://11.170.12.150:8000/tools/list"
try:
    r = requests.get(URL, timeout=10)
    if r.status_code == 200:
        tools = r.json()
        print(f"Total tools: {len(tools)}")
        for i, t in enumerate(tools):
            print(f"Tool {i+1}: {t.get('name')} - {t.get('description')[:60]}...")
    else:
        print("Failed to get tools. Status code:", r.status_code)
except Exception as e:
    print("Error:", e)
