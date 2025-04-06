
# from openai import OpenAI
import openai
print(openai.__version__)


client = openai.OpenAI(
  api_key="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"
)

completion = client.chat.completions.create(
  model="gpt-4o-mini",
  store=True,
  messages=[
    {"role": "user", "content": "Why wrote the mahabharata"}
  ]
)

print("returned message\n", completion.choices[0].message.content);
