import sseclient
import requests
import json
import threading
import time
import sys

# Ensure UTF-8 output on Windows terminal
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def listen_sse(url, events_list, stop_event):
    print(f"Connecting to SSE URL: {url}...")
    try:
        # Use stream=True to keep connection open
        response = requests.get(url, stream=True, timeout=15)
        print("Connected to stream. Listening for events...")
        client = sseclient.SSEClient(response)
        for event in client.events():
            if stop_event.is_set():
                break
            print(f"\n[SSE Event Received]")
            print(f"  Event type: '{event.event}'")
            print(f"  Data: {event.data}")
            events_list.append(event)
    except Exception as e:
        print(f"\n❌ Error in SSE stream: {e}")

def main():
    base_url = "http://11.170.12.150:8000"
    url = f"{base_url}/sse"
    events = []
    stop_event = threading.Event()
    
    # Start the SSE client in a background thread
    t = threading.Thread(target=listen_sse, args=(url, events, stop_event))
    t.daemon = True
    t.start()
    
    # Wait for the endpoint event
    print("Waiting up to 10 seconds for the 'endpoint' event from the server...")
    endpoint_url = None
    start_time = time.time()
    while time.time() - start_time < 10:
        for ev in list(events):
            if ev.event == 'endpoint':
                endpoint_url = ev.data
                break
        if endpoint_url:
            break
        time.sleep(0.5)
        
    if not endpoint_url:
        print("❌ Timeout: Did not receive the 'endpoint' event from the server.")
        stop_event.set()
        return
        
    print(f"✔ Received endpoint event. Raw data: {endpoint_url}")
    
    # Construct the full URL if it's relative
    if not endpoint_url.startswith("http"):
        if endpoint_url.startswith("/"):
            endpoint_url = base_url + endpoint_url
        else:
            endpoint_url = base_url + "/" + endpoint_url
            
    print(f"Full Message POST URL: {endpoint_url}")
    
    # Send JSON-RPC initialize request
    print("\nSending 'initialize' request...")
    initialize_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "sseclient-py-test-client",
                "version": "1.0.0"
            }
        }
    }
    
    try:
        post_response = requests.post(endpoint_url, json=initialize_payload, timeout=10)
        print(f"POST Response Status Code: {post_response.status_code}")
        print(f"POST Response Body: {post_response.text}")
    except Exception as e:
        print(f"❌ Error sending POST request: {e}")
        
    # Wait to receive the JSON-RPC response from the SSE stream
    print("\nWaiting for initialization response in SSE stream...")
    time.sleep(4)
    
    # Send a tools/list request
    print("\nSending 'tools/list' request...")
    list_tools_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        post_response = requests.post(endpoint_url, json=list_tools_payload, timeout=10)
        print(f"POST Response Status Code: {post_response.status_code}")
    except Exception as e:
        print(f"❌ Error sending tools/list POST request: {e}")
        
    # Wait to receive the tools/list response
    print("\nWaiting for tools/list response in SSE stream...")
    time.sleep(4)
    
    # Send a tools/call request for 'get_unidades'
    print("\nSending 'tools/call' request for 'get_unidades'...")
    call_tool_payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "get_unidades",
            "arguments": {
                "limit": 5
            }
        }
    }
    
    try:
        post_response = requests.post(endpoint_url, json=call_tool_payload, timeout=15)
        print(f"POST Response Status Code: {post_response.status_code}")
    except Exception as e:
        print(f"❌ Error sending tools/call POST request: {e}")
        
    # Wait to receive the tools/call response
    print("\nWaiting for tools/call response in SSE stream...")
    time.sleep(5)
    
    stop_event.set()
    print("\nTest finished.")

if __name__ == "__main__":
    main()
