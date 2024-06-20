
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage


# svc_prompt_template = ChatPromptTemplate.from_messages(
#   [
#     SystemMessage(content="You are a fact-checking agent that is constantly learning and improving. A claim is given to you, and you can determine if the claim is correct with the provided documents."),
#     HumanMessage(content='You ALWAYS respond with only a JSON containing an answer and quotes that support the answer. \nThe answer can only be "SUPPORTS" or "REFUTES", with no details. You should reason out the answers step by step, but make sure they are correct. \nDo NOT use your historical knowledge, but answer based on the information in the provided context. '
#         "CONTEXT:\n``````\n{context_docs_str}\n``````"
#         'SAMPLE_RESPONSE:\n```\n{"answer": "Place your final answer here. It can only be SUPPORTS or REFUTES without detail.", "quotes": ["each quote must be UNEDITED and EXACTLY as shown in the context documents!", "HINT, quotes are not shown to the user!",],}\```'
#         "CLAIM: {user_claim}\n"
#         "Hint: Make the answer respond in JSON format! \nQuotes MUST be EXACT substrings from provided documents!")
#   ]
# )

one_shot = '''SAMPLE_RESPONSE:\n```\n{"answer": "Place your final answer here. It can only be SUPPORTS or REFUTES without detail.", "quotes": ["each quote must be UNEDITED and EXACTLY as shown in the context documents!", "HINT, quotes are not shown to the user!"]}\```'''

svc_prompt_template = PromptTemplate(
    input_variables=["context_docs_str", "user_claim"],
    template="""You are a fact-checking agent that is constantly learning and improving. A claim is given to you, and you can determine if the claim is correct with the provided documents.\n
    You ALWAYS respond with only a JSON containing an answer and quotes that support the answer. \nThe answer can only be "SUPPORTS" or "REFUTES", with no details. You should reason out the answers step by step, but make sure they are correct. \nDo NOT use your historical knowledge, but answer based on the information in the provided context. \n
    CONTEXT:\n``````\n{context_docs_str}\n``````\n
    {one_shot}
    CLAIM: {user_claim}\n
    Hint: Make the answer respond in JSON format! \nQuotes MUST be EXACT substrings from provided documents!"""
)

svc_prompt = svc_prompt_template.partial(one_shot=one_shot)