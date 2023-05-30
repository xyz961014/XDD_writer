import os
import openai
import ipdb
openai.api_key = os.getenv("OPENAI_API_KEY")


completion = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {
        "role": "user", 
        "content": "续写：许多多点点头：“有道理"}
  ]
)

print(completion.to_dict()["choices"][0]["message"]["content"])
ipdb.set_trace()
pass
