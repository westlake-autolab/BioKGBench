from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os
import yaml

from .prompts import kg_agent_prompt
from .prompts import team_leader_prompt
from .prompts import validation_agent_prompt


config = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "../../config/llm_config.yml")))
# load_dotenv()

llm = ChatOpenAI(model=config['model'], temperature=0, api_key=config['api_key'], base_url=config['base_url'])

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


if __name__ == "__main__":
    print(config)