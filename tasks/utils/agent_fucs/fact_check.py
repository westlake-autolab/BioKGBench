from loguru import logger as console_logger
from langchain.tools import tool

from ..constant_ import ERROR_RETRY_TIMES
from ..constant_ import DEFAULT_MODEL_ENDPOINT
from ..constant_ import FACT_CHECK
from .danswerAPI_ import fact_check, get_model_name, search_doc


@tool
def validate_claim_by_rag(claim, api_key:str="sk-cairi", api_type:str="local", endpoint:str=DEFAULT_MODEL_ENDPOINT) -> dict:
    '''
    validate_claim_by_rag(claim) -> dict
    Validate the claim by RAG.
    :param claim: str, the claim to validate
    '''
    # token = getToken(USERNAME, PASSWORD)
    token = ""
    llm_name = get_model_name(endpoint) 
    error_cnt = 0
    # log = {"claim": claim}
    log = {}
    while 1:
        answer = fact_check(query=claim, token=token, api_key=api_key, api_type=api_type, llm_name=llm_name, llm_endpoint=endpoint, document_set=[FACT_CHECK], num_hits=10)
        if answer['error_msg']:
            error_msg = answer['error_msg']
            console_logger.error(f"{claim} {error_cnt} {error_msg}")
            error_cnt += 1
            if error_cnt >= ERROR_RETRY_TIMES:
                log.update({'answer': "ERROR", 'error_msg': error_msg})
                break
        
        if answer['answer'] in ["SUPPORTED", "SUPPORTS"]:
            log.update({'answer': "SUPPORTED"})
        elif answer in ["UNSUPPORT", "UNSUPPORTED", "UNSUPPORTS", "UNSUPPORTE", "REFUTED", "REFUTES"]:
            log.update({'answer': "REFUTED"})
        else:
            log.update({'answer': "UNSURE"})

        # log.update({"quotes": answer['quotes']})
        log.update({'error_msg': 'None'})
        break

    return log


def search_claim_related_docs(claim) -> dict:
    '''
    search_claim_related_docs(claim) -> dict
    Search the documents related to the claim.
    :param claim: str, the claim to search
    '''
    token = ""
    docs = search_doc(token=token, claim=claim, document_set=['main_task'])

    outputs = [{"document_id": doc['semantic_identifier'], "content": doc['content']} for doc in docs]

    return outputs


if __name__ == "__main__":
    query = "Teaching medical students to investigate medication errors can change their attitudes towards patient safety."
    # log = validate_claim_by_rag(query)
    log = search_claim_related_docs(query)
    console_logger.info(log)
    # print(validate_claim_by_rag.__doc__)
