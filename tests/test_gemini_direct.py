import openai
import os
from dotenv import load_dotenv

# Cargar .env de forma explícita
env_path = r"C:\Users\opaye\Proyectos\MCPdinamicoPrueba\.env"
print(f"Loading .env from: {env_path}")
load_dotenv(env_path, override=True)

api_key = os.getenv("GEMINI_API_KEY")
if api_key is None:
    print("GEMINI_API_KEY is not found in env!")
else:
    print(f"Testing GEMINI_API_KEY: {api_key[:10]}... (len: {len(api_key)})")

    client = openai.OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=api_key
    )

    try:
        print("Sending test request to gemini-2.5-flash...")
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": "Hola, di 'Ok'"}],
            max_tokens=10
        )
        print("Success! Response:")
        print(response.choices[0].message.content)
    except Exception as e:
        print("Error calling Gemini directly:", e)
