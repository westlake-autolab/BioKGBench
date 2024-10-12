import requests
from langchain.tools import tool
import requests
import time
from requests.exceptions import ConnectionError, Timeout, HTTPError

@tool
def check_interaction_string(protein1, protein2):
    """This tool checks for the interaction between two proteins using the STRING database API. Given two protein ids, it will return a description on whether there is an interaction between them.

    Args:
        protein1 (str): a protein id
        protein2 (str): a protein id

    Returns:
        str: A description about whether there is an interaction between the two proteins.
    """
    species=9606
    retries=3
    delay=5
    string_api_url = "https://string-db.org/api/json/network"
    params = {
        "identifiers": f"{protein1}%0D{protein2}",
        "species": species
    }

    for attempt in range(retries):
        try:
            response = requests.get(string_api_url, params=params, timeout=10)
            response.raise_for_status()  # 如果返回状态码不是200，抛出HTTPError异常
            data = response.json()
            if data:
                return f"Interaction exists between {protein1} and {protein2}, as recorded in database STRING."
            else:
                return f"No interaction found between {protein1} and {protein2}, as recorded in database STRING."

        except (ConnectionError, Timeout, HTTPError) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return "Fail to access the database STRING."
            
            
@tool
def get_uniprot_protein_info(protein_id):
    """
    Fetch protein information from UniProt by protein ID and return a description about the protein, including id, accession and name.
    :param protein_id: UniProt protein ID
    :return: Formatted string with protein information, including id, accession and name
    """
    url = f"https://www.uniprot.org/uniprot/{protein_id}.txt"
    retries=3
    delay=5
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            if response.status_code == 200:
                # Process the response text to extract relevant information
                lines = response.text.split('\n')
                protein_info = {
                    'Gene Name': '',
                    'accession': '',
                }
                for line in lines:
                    if line.startswith('ID   '):
                        protein_info['accession'] = line.split()[1]
                    elif line.startswith('GN   Name='):
                        gene_name = line.split('=')[1].split(';')[0]
                        # Remove any reference identifiers from the gene name
                        protein_info['Gene Name'] = gene_name.split(' {')[0]

                # Format the information for LLM prompt
                prompt = f"id: {protein_id}"
                if not protein_info['accession']:
                    return f"The protein with ID '{protein_id}' is removed from UniProtKB."
                prompt += f", accession: {protein_info['accession']}"
                if protein_info['Gene Name']:
                    prompt += f", name: {protein_info['Gene Name']}"
                else:
                    prompt += ", name (i.e. gene) is not recorded."
                
                return prompt

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return f"Failed to retrieve information for protein ID: {protein_id} after {retries} attempts."