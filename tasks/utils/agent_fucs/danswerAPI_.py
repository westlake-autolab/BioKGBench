from loguru import logger as logging
import requests
from time import sleep

from ..constant_ import DOCUMENT_SET_NAME
from ..constant_ import DEFAULT_MODEL_ENDPOINT
from ..constant_ import AUTH_URL, BASE_URL


def get_connectors(token):
    url = BASE_URL + "manage/connector"
    headers = {"Token": token}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    if response.status_code == 200:
        return response.json()
    else:
        logging.debug(response.status_code, response.reason)

        
def get_model_name(endpoints):
    url = endpoints + "/models"
    res = requests.get(url)
    res.raise_for_status()
    return res.json()['data'][0]['id']


def talk(token, data: list, llm_endpoint: str="http://10.0.1.194:7010") -> dict | str:
    url = BASE_URL + "agent/direct-talk"
    data = {
        "llm_endpoint": llm_endpoint,
        "temperature": 0.7,
        "max_tokens": 10240,
        "history": data
    }
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=data, headers=headers, timeout=600)
    if response.status_code != 200:
        logging.error(response.json())
    response.raise_for_status()
    return response.json()['model_name'], response.json()['answer']


def fact_check(*, token, claim, api_key, llm_name, llm_endpoint=DEFAULT_MODEL_ENDPOINT, api_type:str="local", document_set: list=[DOCUMENT_SET_NAME], num_hits: int=50, source_type: list=['plain_text'], target_quotes: list[str]=None) -> dict | str:
    url = BASE_URL + "agent/fact-checking"
    data = {
        "query": claim,
        "api_key": api_key,
        "llm_name": llm_name,
        "llm_endpoint": llm_endpoint,
        "api_type": api_type,
        "num_hits": num_hits,
        "filters": {
            "document_set": document_set,
            "source_type": source_type,
            "time_cutoff": None
        },
        "collection": "danswer_index",
        "enable_auto_detect_filters": False,
        # "enable_web": web_types,
        # "offset": 0
        "target_quotes": target_quotes
    }
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=data, headers=headers, timeout=600)
    if response.status_code != 200:
        logging.error(response.json())
    response.raise_for_status()
    return response.json()


def search_doc(*, token, claim: str, document_set:list[str]=[DOCUMENT_SET_NAME], web_types: dict={}, source_type: list=[]):
    url = BASE_URL + "document-search"
    headers = {"Token": token}
    body = {
        "query": claim,
        "collection": "danswer_index",
        "enable_auto_detect_filters": False,
        "filters": {
            "document_set": document_set,
            "source_type": source_type,
            "time_cutoff": None
        },
        "enable_web": web_types,
        "offset": 0
    }
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    
    if response.status_code == 200:
        return response.json()['top_documents']
    
    
def index_status(token):
    # url = BASE_URL + "manage/connector/indexing-status"
    url = BASE_URL + "manage/connector/basic_status"
    headers = {"Token": token}
    response = requests.get(url, headers=headers, timeout=(180, 300))
    response.raise_for_status()
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(response.status_code, response.reason)


def get_document_list(token):
    url = BASE_URL + "manage/document-set"
    headers = {"Token": token}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(response.status_code, response.reason)
        
   
class IndexStatus:
    file_path: str| list = None
    origin_status: list = []
    document_sets: list = []
    
    def __init__(self, token) -> None:
        # self.token = getToken(username, passwd)
        self.token = token
        
    def direct_talk(self, data, llm_endpoint: str="http://10.0.1.194:7890"):
        return talk(self.token, data, llm_endpoint)
                
    def list_index_status(self, document_name: str=None):
        logging.debug(f"Document Name: {document_name}")
        status = index_status(self.token)
        if document_name is not None:
            status = [connector for connector in status if connector['name'] == document_name]

        self.origin_status = status
        return self.origin_status
        
    def list_document_set(self, document_name=None) -> list:
        logging.debug(f"Document_set Name: {document_name}")
        d_list = get_document_list(self.token)
        if document_name is not None:
            d_list = [d for d in d_list if d['name'] == document_name]
                    # ccs = [cc['name'] for cc in d['cc_pair_descriptors']]
                    # if all([1 for path in self.file_path if os.path.basename(path) in ccs]):
                    #     return 1
        self.document_sets = d_list
        return self.document_sets
    
    def get_connectors(self):
        return get_connectors(self.token)
        


if __name__ == "__main__":
    TOKEN = getToken('sqma', '123456')
    # # file_path = Path('data/split').glob("*.json")
    # # document_name = 'pride'
    # file_path = ["data/papers/pmic.201700001.pdf", "data/papers/msb.20188793.pdf"]
    # document_name = None
    # # print(file_path)

    instance = IndexStatus(TOKEN)
    # status = instance.list_index_status()
    # document_sets = [dc['name'] for dc in instance.list_document_set()]
    # print(document_sets)
    # document_sets = [dc['id'] for dc in instance.list_document_set()]
    # print(document_sets)
    # instance.delete_document_set(51)
    # document_sets = [instance.delete_document_set(dc['id']) for dc in instance.list_document_set()]

    # for cc in status:
    #     print(cc['name'], cc['connector']['id'])

    # for connector in instance.get_connectors():
    #     if connector['source'] == "file" and connector['connector_specific_config']['file_locations'][0].endswith(".pdf"):
    #         print(connector)
    #         try:
    #             instance.remove_connector(connector)
    #         except Exception as e:
    #             print(e)
    #             continue

    # instance.file_path = file_path
    # # # instance.get_index_ready()
    # instance.get_index_status(document_name)
    # # # instance.clean_index()

    # # instance.document_name = document_name
    # # instance.delete_document_set()
    # instance.make_document_set()
    
    # instance.list_document_set()
    
    # print(get_cc_from_id(TOKEN, 3235))
    # print(get_connectors(TOKEN))
