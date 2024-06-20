import argparse
from functools import partial
from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import yaml

from .utils import SCVDocumentLoader, SCVEmbeddings
from .utils import process_model_tokens
from .prompt import svc_prompt as prompt


def get_retriever(data_path=None):
    # Generate the embeddings
    if os.path.exists("results/svc/db"):
        vectorstore = Chroma(persist_directory="results/svc/db", embedding_function=SCVEmbeddings())
    else:
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data file not found at {data_path}")
        # Load the documents from the file
        loader = SCVDocumentLoader(file_path=data_path)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=200)
        splits = text_splitter.split_documents(loader.lazy_load())
        vectorstore = Chroma.from_documents(persist_directory="results/svc/db", documents=splits, embedding=SCVEmbeddings())

    # Retrieve and generate using the relevant snippets of the blog.
    retriever = vectorstore.as_retriever()
    return retriever


def get_chain(claim, retriever:VectorStoreRetriever):
    config = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "../../config/llm_config.yml")))
    # load_dotenv()

    llm = ChatOpenAI(model=config['model'], temperature=0, api_key=config['api_key'], base_url=config['base_url'])


    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    procss_after = partial(process_model_tokens, context_docs=[doc for doc in retriever.invoke(claim)])

    rag_chain = (
        {"context_docs_str": retriever | format_docs, "user_claim": RunnablePassthrough()}
        | prompt
        | llm
        | procss_after
    )
    return rag_chain


if __name__ == "__main__":
    
    os.makedirs("result/svc", exist_ok=True)

    parse = argparse.ArgumentParser(description="SVC Task")

    parse.add_argument("--data_path", "-d", type=str, help="The path to the data file", required=True)

    args = parse.parse_args()

    claim = "Double balloon enteroscopy is efficacious and safe in a community setting.?"
    rag_chain = get_chain(claim, get_retriever(args.data_path))
    answer = ""
    for piece in rag_chain.stream(claim):
        if piece is not None and "answer_piece" in piece and piece['answer_piece'] is not None:
            answer += piece['answer_piece']
        if piece is not None and "quotes" in piece:
            quotes = piece['quotes']

    print(answer, quotes)