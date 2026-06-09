import asyncio
import httpx
import json
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class CustomSseMcpClient:
    def __init__(self, base_url="http://11.170.12.150:8000"):
        self.base_url = base_url
        self.sse_url = f"{base_url}/sse"
        self.post_url = None
        self.client = httpx.AsyncClient(timeout=30.0)
        self.pending_responses = {}
        self.request_id = 0
        self.read_task = None
        self.connected_event = asyncio.Event()

    async def connect(self):
        self.read_task = asyncio.create_task(self._read_stream())
        try:
            await asyncio.wait_for(self.connected_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            raise RuntimeError("Timeout waiting for endpoint from SSE stream.")

    async def _read_stream(self):
        try:
            async with self.client.stream("GET", self.sse_url) as response:
                current_event = None
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:"):
                        data_content = line[5:].strip()
                        if current_event == "endpoint":
                            if data_content.startswith("http"):
                                self.post_url = data_content
                            else:
                                self.post_url = f"{self.base_url}{data_content}"
                            self.connected_event.set()
                        elif current_event == "message":
                            await self._handle_message(data_content)
                        current_event = None
        except Exception as e:
            print(f"Error in SSE stream reader: {e}")
            self.connected_event.set()

    async def _handle_message(self, raw_msg):
        try:
            msg = json.loads(raw_msg)
            msg_id = msg.get("id")
            if msg_id is not None:
                future = self.pending_responses.pop(msg_id, None)
                if future and not future.done():
                    future.set_result(msg)
        except Exception as e:
            print(f"Error parsing incoming message: {e}")

    async def send_request(self, method, params):
        self.request_id += 1
        rid = self.request_id
        payload = {
            "jsonrpc": "2.0",
            "id": rid,
            "method": method,
            "params": params
        }
        future = asyncio.get_running_loop().create_future()
        self.pending_responses[rid] = future
        
        try:
            r = await self.client.post(self.post_url, json=payload)
            if r.status_code not in [200, 202]:
                self.pending_responses.pop(rid, None)
                raise RuntimeError(f"POST failed: {r.status_code} - {r.text}")
        except Exception as e:
            self.pending_responses.pop(rid, None)
            raise e
            
        response = await future
        return response

    async def initialize(self):
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "CustomSseMcpClient", "version": "1.0"}
        }
        return await self.send_request("initialize", params)

    async def call_tool(self, name, arguments):
        params = {"name": name, "arguments": arguments}
        res = await self.send_request("tools/call", params)
        return res.get("result", {})

    async def close(self):
        if self.read_task:
            self.read_task.cancel()
        await self.client.aclose()

async def test():
    client = CustomSseMcpClient()
    try:
        await client.connect()
        await client.initialize()
        
        print("\nCalling get_unidades via Custom SSE Client...")
        start = asyncio.get_running_loop().time()
        res = await client.call_tool("get_unidades", {"limit": 5})
        elapsed = asyncio.get_running_loop().time() - start
        print(f"Response received in {elapsed:.2f} seconds!")
        print(json.dumps(res, indent=2))
        
    except Exception as e:
        print("\nError during test:", e)
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test())
