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

# Global events list to share events between listener thread and main thread
received_responses = {}
received_events_lock = threading.Lock()
stop_listening = False
endpoint_url_found = None
endpoint_event = threading.Event()

def with_requests(url):
    """Get a streaming response for the given event feed using requests."""
    res = requests.get(url, stream=True)
    yield from sseclient.SSEClient(res).events()

def sse_listener_thread(url):
    global stop_listening, endpoint_url_found
    try:
        for event in with_requests(url):
            if stop_listening:
                break
            
            if event.event == 'endpoint':
                endpoint_url_found = event.data
                endpoint_event.set()
                print(f"\n[SSE event: '{event.event}'] Data: {event.data}")
            elif event.event == 'message':
                try:
                    parsed_data = json.loads(event.data)
                    msg_id = parsed_data.get("id")
                    if msg_id is not None:
                        with received_events_lock:
                            received_responses[msg_id] = parsed_data
                    
                    print(f"\n[SSE event: '{event.event}']")
                    print(f"Data: {json.dumps(parsed_data, indent=2)}")
                except Exception:
                    print(f"\n[SSE event: '{event.event}'] Data: {event.data}")
    except Exception as e:
        if not stop_listening:
            print(f"\n[SSE Listener Error] {e}")

def send_rpc_request(post_url, method, params, request_id):
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params
    }
    print(f"\n--- Sending {method} (id={request_id}) ---")
    print(f"Payload: {json.dumps(payload)}")
    try:
        # We use a long timeout (90s) because the server's DB queries can take ~70s to time out/respond
        response = requests.post(post_url, json=payload, timeout=90)
        print(f"HTTP Post status: {response.status_code}")
        print(f"HTTP Post response: {response.text}")
        return True
    except requests.exceptions.Timeout:
        print(f"❌ HTTP Post request timed out (90 seconds limit reached)")
        return False
    except Exception as e:
        print(f"❌ HTTP Post error: {e}")
        return False

def wait_for_response(request_id, timeout_seconds=90):
    print(f"Waiting up to {timeout_seconds} seconds for response with id={request_id} from SSE stream...")
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        with received_events_lock:
            if request_id in received_responses:
                return received_responses[request_id]
        time.sleep(0.5)
    return None

def main():
    global stop_listening, endpoint_url_found
    server_url = "http://11.170.12.150:8000"
    sse_url = f"{server_url}/sse"
    
    print(f"==================================================")
    print(f"MCP SSE Connection Test using sseclient-py")
    print(f"Server URL: {server_url}")
    print(f"SSE Endpoint: {sse_url}")
    print(f"==================================================")
    
    # 1. Start SSE Listener in thread
    listener = threading.Thread(target=sse_listener_thread, args=(sse_url,))
    listener.daemon = True
    listener.start()
    
    # 2. Wait for endpoint event
    print("Waiting for 'endpoint' event from the SSE stream...")
    if not endpoint_event.wait(timeout=10.0):
        print("❌ Error: Did not receive the 'endpoint' event from the server within 10 seconds.")
        stop_listening = True
        return
        
    endpoint_path = endpoint_url_found
    print(f"✔ Received 'endpoint' event: {endpoint_path}")
    
    # Construct full POST URL
    if endpoint_path.startswith("http"):
        post_url = endpoint_path
    else:
        post_url = f"{server_url}{endpoint_path}" if endpoint_path.startswith("/") else f"{server_url}/{endpoint_path}"
    print(f"Message Post URL: {post_url}")
    
    # 3. Send Initialize Request
    init_id = 101
    init_params = {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "sseclient-py-tester",
            "version": "1.0.0"
        }
    }
    
    if send_rpc_request(post_url, "initialize", init_params, request_id=init_id):
        resp = wait_for_response(init_id, timeout_seconds=15)
        if resp:
            print(f"✔ Initialize completed successfully!")
        else:
            print(f"❌ Initialize response was not received in SSE stream.")
            
    # 4. Send list_tools request
    tools_id = 102
    if send_rpc_request(post_url, "tools/list", {}, request_id=tools_id):
        resp = wait_for_response(tools_id, timeout_seconds=15)
        if resp:
            print(f"✔ Tools list retrieved successfully!")
        else:
            print(f"❌ Tools list response was not received in SSE stream.")
            
    # 5. Call get_catalogo_datos
    call_id = 103
    if send_rpc_request(post_url, "tools/call", {"name": "get_catalogo_datos", "arguments": {"limit": 1}}, request_id=call_id):
        resp = wait_for_response(call_id, timeout_seconds=90)
        if resp:
            print(f"✔ Tool call response received!")
            if "error" in resp:
                print(f"⚠ Server returned an error: {resp['error']}")
            else:
                print(f"Result data: {json.dumps(resp.get('result'), indent=2)}")
        else:
            print(f"❌ Tool call response was not received (timeout).")
            
    # Shut down listener
    stop_listening = True
    print("\nTest run completed.")

if __name__ == "__main__":
    main()
