from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

response = client.responses.create(
    model="gpt-5.6",
    input="日本語で『OpenAI API接続成功』とだけ返してください。",
)

print(response.output_text)