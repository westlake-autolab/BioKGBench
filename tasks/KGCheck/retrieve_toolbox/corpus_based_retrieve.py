from langchain.tools import tool
from langchain_openai import ChatOpenAI
from typing import List, Dict
from ...utils.agent_fucs.fact_check import search_claim_related_docs
import re
import json

llm = ChatOpenAI(
    # model='llama-3.1-70b', 
    model='llama-3.1-405b',
    temperature=0,
    base_url='https://api2.aigcbest.top/v1',
    api_key="sk-1DEQnEbUPNagRrWU7a98Dd2e5e8f49FaA8DaD10d4c974d09"
)

def process_doc(claim, doc: List[Dict]):

    _prompt = '''Read this literature and determine whether it supports this claim and give your confidence score.
    REQUIREMENTS:
    1. Please respond in the following format:
        {{"attitude": 'support', 'refute', or 'not enough information', 
        "confidence": a number from 1 to 5, with a higher number indicating greater certainty}}
    2. Please return a valid JSON format.
    CLAIM: {claim}
    LITERATURE: {literature}'''
    prompt_check = '''This document is considered insufficient to determine whether the claim is correct. Please confirm if this is the case. If it is indeed the case, reply with "not enough information." If it supports the claim, reply with "support." If it does not support the claim, reply with "refute." Please only respond with the requested content, without any additional information.
    CLAIM: {claim}
    DOCUMENT: {document}'''
    supp_evidence, refu_evidence = [], []
    support, refute = 0, 0

    for d in doc:
        doc_id = d['document_id']
        doc_content = d['content']
        prompt = _prompt.format(claim=claim, literature=doc_content)

        isparsed = False
        for i in range(3):
            res = llm.invoke([("human", prompt)]).dict()['content']
            try:
                match = re.search(r'\{.*\}', res, re.DOTALL)
                if match:
                    _json_res = match.group(0)
                    json_res = json.loads(_json_res)
                    isparsed = True
                    break
            except:
                pass
        if not isparsed:
            continue
        
        # print(json.dumps(json_res, indent=4))

        attitude = json_res['attitude']
        confidence = json_res['confidence']
        if attitude == 'support':
            support += confidence
            supp_evidence.append(doc_id)
        elif attitude == 'refute':
            refute += confidence
            refu_evidence.append(doc_id)
        else:
            if confidence < 3:
                try:
                    check_res = llm.invoke([("human", prompt_check)]).dict()['content']
                    # print(check_res)
                    if check_res == 'support':
                        support += 1
                        supp_evidence.append(doc_id)
                    elif check_res == 'refute':
                        refute += 1
                        refu_evidence.append(doc_id)
                except:
                    pass

    # import pdb; pdb.set_trace()
    if support > refute:
        return f"support, evidence: {', '.join([pid for pid in supp_evidence])}"
    elif support == refute:
        return f"The retrieved literature is insufficient to provide adequate information to determine whether the claim is correct."
    else:
        return f"refute, evidence: {', '.join([pid for pid in refu_evidence])}"


@tool
def pub_rag(query: str):
    '''retrieve evidence from provided documents to help making a verdict of the given claim
        Args:
            query(str): the claim to be verdicted
        Returns:
            no more than 10 documents ralated to the claim with their ids.
            the basic format is 'document_id: document_content'
    '''
    
    documents = [{'document_id': doc['document_id'], 'content': doc['content']} for doc in search_claim_related_docs(query)[:10]]
    # print(json.dumps(documents, indent=4))
    result = process_doc(query, documents)

    return result

if __name__ == '__main__':
    res = pub_rag('Protein with ID P19878 has a CURATED relationship with Protein ID P14598 as per literature')
    print(res)