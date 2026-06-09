import os
import openai
from dotenv import load_dotenv

env_path = r"C:\Users\opaye\Proyectos\MCPdinamicoPrueba\.env"
load_dotenv(env_path, override=True)
api_key = os.getenv("GEMINI_API_KEY")

client = openai.OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=api_key
)

def test_tool_schema(value_schema):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "test_schema",
                "description": "Test tool schema definition",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filters": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field": {"type": "string"},
                                    "value": value_schema
                                },
                                "required": ["field"]
                            }
                        }
                    }
                }
            }
        }
    ]
    try:
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": "Hola"}],
            tools=tools,
            max_tokens=10
        )
        return True, "Success!"
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    # Test 1: Omitting "type" entirely
    ok1, res1 = test_tool_schema({"description": "Valor del filtro"})
    print("Test 1 (Omit type):", ok1, res1)
    
    # Test 2: Using type: "string"
    ok2, res2 = test_tool_schema({"type": "string", "description": "Valor del filtro"})
    print("Test 2 (type: string):", ok2, res2)
