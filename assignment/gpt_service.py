import json
from typing import List, Dict
from openai import OpenAI, AsyncOpenAI
from openai.types.chat.completion_create_params import ResponseFormat


class GPTService:
    def __init__(self, openai_api_key, profanity_prompt=""):
        self.client = OpenAI(api_key=openai_api_key, organization="org-Ib9jshDWhoPzZ7iCkDx0rwYB")
        self.aclient = AsyncOpenAI(api_key=openai_api_key, organization="org-Ib9jshDWhoPzZ7iCkDx0rwYB")
        self.profanity_prompt = profanity_prompt

    async def aquery_gpt(self, message_history: list,
                         query: str, model="gpt-4"):
        return await (self.aclient.chat.
                      completions.
                      create(model=model,
                             messages=message_history + [
                                 {"role": "user", "content": query}],
                             stream=True))

    def query_gpt(self, message_history: List[Dict],
                  query: str, model="gpt-4"):
        message_history_req = message_history + [{"role": "user", "content": query}]
        return (self.client
                .chat.completions.create(model=model,
                                         messages=message_history_req, ))

    def get_ai_response(self, message_history, user_message: str) -> str:
        gpt_response = self.query_gpt(message_history, user_message, model="gpt-4")
        return gpt_response.choices[0].message.content

    def contains_profanity(self, user_input: str) -> bool:
        response = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_format=ResponseFormat(type="json_object"),
            messages=[
                {
                    "role": "system",
                    "content": self.profanity_prompt
                },
                {
                    "role": "user",
                    "content": user_input
                },
            ])
        try:
            response = json.loads(response.choices[0].message.content)
            return response['flagged']
        except:
            return False
