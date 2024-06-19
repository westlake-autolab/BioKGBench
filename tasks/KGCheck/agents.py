from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os

from .prompts import kg_agent_prompt
from .prompts import team_leader_prompt
from .prompts import validation_agent_prompt


load_dotenv()

llm = ChatOpenAI(model=os.getenv('MODEL', "Qwen1.5-70B-Chat"), temperature=0, api_key=os.getenv('API_KEY', "sk-key"), base_url=os.getenv('ENDPOINT', "http://10.0.1.194:7410/v1"))

kg_chain = (
    kg_agent_prompt
    |llm
)

leader_chain = (
    team_leader_prompt
    | llm
)

validation_chain = (
    validation_agent_prompt
    |llm
)
