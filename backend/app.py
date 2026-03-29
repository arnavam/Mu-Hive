import os
import json
import asyncio
import asyncpg
from flask import Flask, request, jsonify, render_template
from firecrawl import FirecrawlApp
from dotenv import load_dotenv

load_dotenv(override=True)

app = Flask(__name__)

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/postgres")

db_pool = None

async def get_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        async with db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS scraped_data (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    return db_pool

def call_firecrawl(firecrawl_app, mode, url, options):
    if mode == 'crawl':
        return firecrawl_app.crawl(url, scrape_options=options)
    else:
        return firecrawl_app.scrape_url(url, params=options) if hasattr(firecrawl_app, 'scrape_url') else firecrawl_app.scrape(url, **options)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
async def scrape():
    try:
        data = request.json
        url = data.get('url')
        mode = data.get('mode', 'scrape')
        options = data.get('options', {})

        if not FIRECRAWL_API_KEY:
            return jsonify({"error": "Firecrawl API key not found in backend .env"}), 400

        firecrawl_app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
        
        # Run blocking Firecrawl API calls in thread so it does not block the event loop
        result = await asyncio.to_thread(call_firecrawl, firecrawl_app, mode, url, options)

        # Handle object serialization if the result is a custom Document object from Firecrawl
        if hasattr(result, 'model_dump'):
            serializable_result = result.model_dump()
        elif hasattr(result, 'dict'):
            serializable_result = result.dict()
        elif hasattr(result, '__dict__'):
            serializable_result = result.__dict__
        else:
            serializable_result = result

        # Wait for the DB pool and insert data
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO scraped_data (url, mode, data) VALUES ($1, $2, $3)",
                url, mode, json.dumps(serializable_result)
            )

        return jsonify(serializable_result)

    except Exception as e:
        print(f"Flask Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
