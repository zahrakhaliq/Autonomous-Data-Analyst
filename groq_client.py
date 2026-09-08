import json
from groq import Groq
from config import get_groq_api_key, get_model

class GroqClient:
    def __init__(self):
        key = get_groq_api_key()
        if not key:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Add it to Streamlit secrets or your environment."
            )
        self.client = Groq(api_key=key)
        self.model = get_model()

    def json_completion(self, system_prompt, user_prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return json.loads(response.choices[0].message.content)

    def text_completion(self, system_prompt, user_prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
