import os
import asyncio
import json
import openai
from dotenv import load_dotenv

load_dotenv()

async def test_tool_call():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found")
        return
        
    client = openai.AsyncOpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=api_key
    )
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a location",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "location": {"type": "STRING", "description": "City name"}
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    messages = [
        {"role": "user", "content": "What is the weather in Tokyo?"}
    ]
    
    print("--- FIRST CALL ---")
    stream = await client.chat.completions.create(
        model="gemini-3.1-flash-lite",
        messages=messages,
        tools=tools,
        parallel_tool_calls=False,
        stream=True
    )
    
    tool_calls_chunks = {}
    async for chunk in stream:
        # print("Chunk:", chunk)
        # Check model_extra at different levels
        # print("Chunk extra:", getattr(chunk, "model_extra", None))
        if chunk.choices:
            choice = chunk.choices[0]
            # print("Choice extra:", getattr(choice, "model_extra", None))
            delta = choice.delta
            # print("Delta extra:", getattr(delta, "model_extra", None))
            
            # Print if there is a thought_signature or anything extra in delta
            if getattr(delta, "model_extra", None):
                print("Delta model_extra:", delta.model_extra)
                
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    print("Tool call structure:", tc)
                    print("Tool call model_extra:", getattr(tc, "model_extra", None))
                    idx = tc.index
                    if idx not in tool_calls_chunks:
                        tool_calls_chunks[idx] = {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": "", "arguments": ""}
                        }
                    if tc.id:
                        tool_calls_chunks[idx]["id"] = tc.id
                    if tc.function and tc.function.name:
                        tool_calls_chunks[idx]["function"]["name"] += tc.function.name
                    if tc.function and tc.function.arguments:
                        tool_calls_chunks[idx]["function"]["arguments"] += tc.function.arguments
                        
                    # Accumulate model_extra if present
                    tc_extra = getattr(tc, "model_extra", None) or {}
                    if tc_extra:
                        if "extra" not in tool_calls_chunks[idx]:
                            tool_calls_chunks[idx]["extra"] = {}
                        tool_calls_chunks[idx]["extra"].update(tc_extra)
                        
    print("Accumulated tool calls:", tool_calls_chunks)
    
    # Now let's try calling with the assistant response
    tool_calls_list = list(tool_calls_chunks.values())
    
    # Strip the temporary "extra" key from tool_calls_list for standard formatting,
    # but keep track of it to see if we need to put it elsewhere or keep it.
    assistant_msg = {
        "role": "assistant",
        "content": None,
        "tool_calls": []
    }
    
    for tc in tool_calls_list:
        tc_dict = {
            "id": tc["id"],
            "type": tc["type"],
            "function": tc["function"]
        }
        # If we have extras, put them in
        if "extra" in tc:
            tc_dict.update(tc["extra"])
        assistant_msg["tool_calls"].append(tc_dict)
        
    messages.append(assistant_msg)
    
    # Append the tool response
    for tc in tool_calls_list:
        messages.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "name": tc["function"]["name"],
            "content": json.dumps({"weather": "sunny, 22C"})
        })
        
    print("\n--- SECOND CALL MESSAGES ---")
    print(json.dumps(messages, indent=2))
    
    print("\n--- SECOND CALL ---")
    try:
        response = await client.chat.completions.create(
            model="gemini-3.1-flash-lite",
            messages=messages,
            tools=tools,
            parallel_tool_calls=False
        )
        print("Success! Response:", response.choices[0].message.content)
    except Exception as e:
        print("Failed! Error:", e)

if __name__ == "__main__":
    asyncio.run(test_tool_call())
