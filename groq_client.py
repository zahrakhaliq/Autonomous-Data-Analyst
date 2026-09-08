import json
from groq import Groq

from config import get_groq_api_key, get_model


class GroqClient:
    def __init__(self):
        key = get_groq_api_key()

        if not key:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Add it to Streamlit secrets."
            )

        self.client = Groq(api_key=key)
        self.model = get_model()

    def json_completion(self, system_prompt, user_prompt, schema, schema_name):
        """
        Ask Groq for structured JSON that must follow the supplied JSON schema.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            max_completion_tokens=4096,
            reasoning_effort="low",
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
            messages=[
                {
                    "role": "system",
                    "content": (
                        system_prompt
                        + "\n\nReturn ONLY the JSON object required by the schema."
                    ),
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("Groq returned an empty response.")

        return json.loads(content)

    def text_completion(self, system_prompt, user_prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            max_completion_tokens=4096,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        return response.choices[0].message.content
