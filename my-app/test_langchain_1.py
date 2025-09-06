from dotenv import load_dotenv; load_dotenv()
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
resp = llm.invoke("Return the word PONG.")
print("Model:", llm.model)
print("Reply:", getattr(resp, "content", resp))
