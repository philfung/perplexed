#!/usr/local/bin/python

import os

from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Respond with 'Groq is alive'",
        }
    ],
    model="llama3-8b-8192",  # quick model
    max_completion_tokens=10,
    temperature=0,
)

print(chat_completion.choices[0].message.content)
