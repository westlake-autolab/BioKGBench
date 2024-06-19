from langchain.tools import tool

from ...utils.agent_fucs.fact_check import search_claim_related_docs

@tool
def pub_rag(query: str):
    '''retrieve evidence from provided documents to help making a verdict of the given claim
        Args:
            query(str): the claim to be verdicted
        Returns:
            no more than 10 documents ralated to the claim with their ids.
            the basic format is 'document_id: document_content'
    '''
    return "\n".join([doc['document_id']+': '+doc['content'] for doc in search_claim_related_docs(query)[:10]])