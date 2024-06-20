import os
import yaml

config = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "../../config/llm_config.yml")))

FACT_CHECK = "fact_check"

DEFAULT_ENDPOINT = config['base_url']
DEFAULT_MODEL = config['model']
DEFAULT_API_KEY = config['api_key']

AUTH_URL = os.environ.get("AUTH_BASE") or "http://10.0.1.197:9992"
BASE_URL = os.environ.get("SERVER_BASE") or "http://172.17.0.1:3000/api/"

REFUTES_OPTION = ["UNSUPPORTED", "UNSUPPORT", "UNSUPPORTS", "UNSUPPORTE", "REFUTED", "REFUTES"]
SUPPORTS_OPTION = ["SUPPORTED", "SUPPORTS"]
UNSURE_OPTION = ["UNSURE", "UNRELATED"]

ERROR_RETRY_TIMES = 3
