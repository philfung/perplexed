#!/usr/local/bin/python

import os
import httpx

from groq import Groq

# Workaround for groq/httpx compatibility issue
http_client = httpx.Client()
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
    http_client=http_client,
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Respond with 'Groq is alive'",
        }
    ],
    model="llama3-8b-8192",  # quick model
    max_tokens=10,
    temperature=0,
)

print(chat_completion.choices[0].message.content)
