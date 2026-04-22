import os
import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
base_url = "https://openrouter.ai/api/v1"

models_to_test = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-3-12b:free",
    "google/gemma-3-4b:free",
    "openai/gpt-oss-120b:free"
]

async def test_model(model_id):
    print(f"Testing {model_id}...")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 5
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                print(f"✅ {model_id} works!")
                return True
            else:
                print(f"❌ {model_id} failed with {resp.status_code}: {resp.text}")
                return False
    except Exception as e:
        print(f"⚠️ {model_id} error: {e}")
        return False

async def main():
    if not api_key:
        print("OPENROUTER_API_KEY not found in .env")
        return
        
    for model in models_to_test:
        await test_model(model)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
