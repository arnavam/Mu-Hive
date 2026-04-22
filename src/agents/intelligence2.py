from groq import Groq
from src.config.settings import GROQ_API_KEY, GROQ_MODEL

class IntelligenceAgent:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        self.model = GROQ_MODEL

    def summarize(self, content):
        if not self.client:
            return "Groq API key not configured."
        
        if not content:
            return "No content to summarize."

        # Convert content to string if it's a dict/list
        if isinstance(content, (dict, list)):
            import json
            content = json.dumps(content, indent=2)

        # Truncate content if too long (rough estimate for token limits)
        max_chars = 15000 
        if len(content) > max_chars:
            content = content[:max_chars] + "... [truncated]"

        prompt = f"""
        You are a highly efficient text summarizer for the Mu-Hive pipeline.
        Your goal is to provide a concise and insightful summary of the following scraped data.
        Focus on the key technical details, opportunities, and main points.
        
        Data to summarize:
        {content}
        
        Summary:
        """

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional technical researcher and summarizer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            return f"Error during summarization: {str(e)}"

    def analyze_event(self, content):
        if not self.client:
            return None
        
        if not content:
            return None

        if isinstance(content, (dict, list)):
            import json
            content = json.dumps(content, indent=2)

        max_chars = 15000 
        if len(content) > max_chars:
            content = content[:max_chars] + "... [truncated]"

        prompt = f"""
        Extract structured hackathon/event information from the following scraped data.
        Provide the result in RAW JSON format with the following keys:
        - title (string): The name of the event.
        - type (string): The type of event (e.g., Hackathon, Internship, Conference).
        - platform (string): The hosting platform (e.g., Devpost, Unstop, etc.).
        - location (string): Where it is held (e.g., Online, City Name).
        - days_left (integer): Number of days remaining for registration/submission. If not found, use null.
        - ig (string): Instagram handle or link if mentioned, otherwise null.
        - score (integer): A relevance score from 1-100 based on the quality and prestige of the event.

        Data:
        {content}
        
        Return ONLY the JSON object.
        """

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data extraction specialist. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            import json
            return json.loads(completion.choices[0].message.content.strip())
        except Exception as e:
            print(f"Error during event analysis: {str(e)}")
            return None

intelligence = IntelligenceAgent()
