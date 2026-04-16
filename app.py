import os
import asyncio
from flask import Flask, request, jsonify, render_template

from src.orchestrator import orchestrator
from src.config.settings import FIRECRAWL_API_KEY

app = Flask(__name__)

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

        # Run the full pipeline using the Orchestrator
        # We don't need to wrap in to_thread here because process_url is already async
        result = await orchestrator.process_url(url, mode, options)

        if "error" in result:
            return jsonify({"error": result["error"]}), 500

        return jsonify(result)

    except Exception as e:
        print(f"Flask Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
