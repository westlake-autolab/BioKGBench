import json
from json.decoder import JSONDecodeError
from langchain_core.messages import BaseMessage
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.pydantic_v1 import BaseModel
import math
import re
import regex
import requests
from typing import Iterator
from typing import Generator
from typing import List
import jsonlines
from loguru import logger



class SCVDocumentLoader(BaseLoader):
    """An example document loader that reads a file line by line."""

    def __init__(self, file_path: str) -> None:
        """Initialize the loader with a file path.

        Args:
            file_path: The path to the file to load.
        """
        self.file_path = file_path

    def lazy_load(self) -> Iterator[Document]:  # <-- Does not take any arguments
        """A lazy loader that reads a file line by line.

        When you're implementing lazy load methods, you should use a generator
        to yield documents one by one.
        """
        
        with open(self.file_path, "r+", encoding="utf8") as f:
            line_number = 0
            for data in jsonlines.Reader(f):
                yield Document(
                    page_content=data['abstract'],
                    metadata={"pmid": data['pmid'], "title": data['title'], "source": self.file_path},
                )
                line_number += 1


class SCVEmbeddings(BaseModel, Embeddings):
    def _embed(self, texts: List[str]) -> List[List[float]]:
        outputs = []
        for text in texts:
            # Call Jina AI Embedding API
            # resp = requests.post("http://localhost:7005/embeddings", json={"texts": texts})
            resp = requests.post("http://10.0.1.196:17000/embedding", json={"texts": [text]})
            resp.raise_for_status()
            resp = resp.json()
            if "embeddings" not in resp:
                raise RuntimeError(resp["detail"])
            outputs.extend(resp["embeddings"])

        # Return just the embeddings
        return outputs

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Call out to Jina's embedding endpoint.
        Args:
            texts: The list of texts to embed.
        Returns:
            List of embeddings, one for each text.
        """
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        """Call out to Jina's embedding endpoint.
        Args:
            text: The text to embed.
        Returns:
            Embeddings for the text.
        """
        return self._embed([text])[0]

QUOTE_PAT = "Quotes: "
ANSWER_PAT = "Answer: "
UNCERTAINTY_PAT = "?"

def clean_up_code_blocks(model_out_raw: str) -> str:
    model_out_raw = model_out_raw.strip().strip("```").strip().replace("\\xa0", "")
    if not model_out_raw.startswith('{'):
        model_out_raw = model_out_raw[model_out_raw.find('{') : ]
    if not model_out_raw.endswith('}'):
        model_out_raw = model_out_raw[ : model_out_raw.rfind('}') + 1]
    return model_out_raw


def extract_answer_quotes_freeform(
    answer_raw: str,
):
    """Splits the model output into an Answer and 0 or more Quote sections.
    Splits by the Quote pattern, if not exist then assume it's all answer and no quotes
    """
    # If no answer section, don't care about the quote
    if answer_raw.lower().strip().startswith(QUOTE_PAT.lower()):
        return None, None

    # Sometimes model regenerates the Answer: pattern despite it being provided in the prompt
    if answer_raw.lower().startswith(ANSWER_PAT.lower()):
        answer_raw = answer_raw[len(ANSWER_PAT) :]

    # Accept quote sections starting with the lower case version
    answer_raw = answer_raw.replace(
        f"\n{QUOTE_PAT}".lower(), f"\n{QUOTE_PAT}"
    )  # Just in case model unreliable

    sections = re.split(rf"(?<=\n){QUOTE_PAT}", answer_raw)
    sections_clean = [
        str(section).strip() for section in sections if str(section).strip()
    ]
    if not sections_clean:
        return None, None

    answer = str(sections_clean[0])
    if len(sections) == 1:
        return answer, None
    return answer, sections_clean[1:]


def extract_answer_quotes_json(
    answer_dict: dict[str, str | list[str]]
):
    answer_dict = {k.lower(): v for k, v in answer_dict.items()}
    answer = str(answer_dict.get("answer"))
    quotes = answer_dict.get("quotes") or answer_dict.get("quote")
    if isinstance(quotes, str):
        quotes = [quotes]
    return answer, quotes


def separate_answer_quotes(
    answer_raw: str, is_json_prompt: bool = False
):
    try:
        model_raw_json = json.loads(answer_raw, strict=False)
        return extract_answer_quotes_json(model_raw_json)
    except JSONDecodeError:
        # LLMs get confused when handling the list in the json. Sometimes it doesn't attend
        # enough to the previous { token so it just ends the list of quotes and stops there
        # here, we add logic to try to fix this LLM error.
        try:
            model_raw_json = json.loads(answer_raw + "}", strict=False)
            return extract_answer_quotes_json(model_raw_json)
        except JSONDecodeError:
            if is_json_prompt:
                logger.error("Model did not output in json format as expected.")
                raise
            return extract_answer_quotes_freeform(answer_raw)


def shared_precompare_cleanup(text: str) -> str:
    """LLMs models sometime restructure whitespaces or edits special characters to fit a more likely
    distribution of characters found in its training data, but this hurts exact quote matching
    """
    text = text.lower()

    # \s: matches any whitespace character (spaces, tabs, newlines, etc.)
    # |: acts as an OR.
    # \*: matches the asterisk character.
    # \\": matches the \" sequence.
    # [.,:`"#-]: matches any character inside the square brackets.
    text = re.sub(r'\s|\*|\\"|[.,:`"#-]', "", text)

    return text


def clean_model_quote(quote: str, trim_length: int) -> str:
    quote_clean = quote.strip()
    if quote_clean[0] == '"':
        quote_clean = quote_clean[1:]
    if quote_clean[-1] == '"':
        quote_clean = quote_clean[:-1]
    if trim_length > 0:
        quote_clean = quote_clean[:trim_length]
    return quote_clean


def match_quotes_to_docs(
    quotes: list[str],
    chunks: list[Document],
    max_error_percent: float = 0.05,
    fuzzy_search: bool = False,
    prefix_only_length: int = 100,
):
    danswer_quotes: list[str] = []
    for quote in quotes:
        max_edits = math.ceil(float(len(quote)) * max_error_percent)

        for chunk in chunks:
            quote_clean = shared_precompare_cleanup(
                clean_model_quote(quote, trim_length=prefix_only_length)
            )
            chunk_clean = shared_precompare_cleanup(chunk.page_content)

            # Finding the offset of the quote in the plain text
            if fuzzy_search:
                re_search_str = (
                    r"(" + re.escape(quote_clean) + r"){e<=" + str(max_edits) + r"}"
                )
                found = regex.search(re_search_str, chunk_clean)
                if not found:
                    continue
                offset = found.span()[0]
            else:
                if quote_clean not in chunk_clean:
                    continue
                offset = chunk_clean.index(quote_clean)

            # Extracting the link from the offset
            curr_link = None

            danswer_quotes.append({
                "quote": quote,
                "semantic_identifier": chunk.metadata.get("pmid"),
                "title": chunk.metadata.get("title"),
                })
            break

    return {"quotes": danswer_quotes}


def process_answer(
    answer_raw: str,
    chunks: list[Document],
    is_json_prompt: bool = True,
):
    answer_clean = clean_up_code_blocks(answer_raw)

    answer, quote_strings = separate_answer_quotes(answer_clean, is_json_prompt)
    if answer == UNCERTAINTY_PAT or not answer:
        if answer == UNCERTAINTY_PAT:
            logger.debug("Answer matched UNCERTAINTY_PAT")
        else:
            logger.debug("No answer extracted from raw output")
        return {"answer": None}, {"quotes": []}

    if not quote_strings:
        logger.debug("No quotes extracted from raw output")
        return {"answer": answer}, {"quotes": []}
    quotes = match_quotes_to_docs(quote_strings, chunks)

    return {"answer": answer}, quotes


def stream_json_answer_end(answer_so_far: str, next_token: str) -> bool:
    next_token = next_token.replace('\\"', "")
    # If the previous character is an escape token, don't consider the first character of next_token
    # This does not work if it's an escaped escape sign before the " but this is rare, not worth handling
    if answer_so_far and answer_so_far[-1] == "\\":
        next_token = next_token[1:]
    if '"' in next_token:
        return True
    return False


def extract_quotes_from_completed_token_stream(
    model_output: str, context_chunks: list[Document], is_json_prompt: bool = True
):
    answer, quotes = process_answer(model_output, context_chunks, is_json_prompt)
    if answer:
        logger.debug(f"answer: {answer}, quotes: {quotes}")
    elif model_output:
        logger.warning("Answer extraction from model output failed.")

    return quotes


def process_model_tokens(
    tokens: Iterator[BaseMessage],
    context_docs: list[Document],
    is_json_prompt: bool = True,
):
    
    """Yields Answer tokens back out in a dict for streaming to frontend
    When Answer section ends, yields dict with answer_finished key
    Collects all the tokens at the end to form the complete model output"""
    quote_pat = f"\n{QUOTE_PAT}"
    # Sometimes worse model outputs new line instead of :
    quote_loose = f"\n{quote_pat[:-1]}\n"
    # Sometime model outputs two newlines before quote section
    quote_pat_full = f"\n{quote_pat}"
    model_output: str = ""
    found_answer_start = False if is_json_prompt else True
    found_answer_end = False
    hold_quote = ""
    tokens_backup = []

    for token in tokens:
        token = token.content
        tokens_backup.append(token)
        model_previous = model_output
        model_output += token
        if "{" not in model_output:
            continue
        model_output = model_output[model_output.index("{"):]

        if not found_answer_start and '{"answer":"' in re.sub(r"\s", "", model_output):
            # Note, if the token that completes the pattern has additional text, for example if the token is "?
            # Then the chars after " will not be streamed, but this is ok as it prevents streaming the ? in the
            # event that the model outputs the UNCERTAINTY_PAT
            found_answer_start = True

            # Prevent heavy cases of hallucinations where model is not even providing a json until later
            if is_json_prompt and len(model_output) > 20:
                found_answer_end = True

            continue

        if found_answer_start and not found_answer_end:
            if is_json_prompt and stream_json_answer_end(model_previous, token):
                found_answer_end = True
                yield {"answer_piece": None}
                continue
            elif not is_json_prompt:
                if quote_pat in hold_quote + token or quote_loose in hold_quote + token:
                    found_answer_end = True
                    yield {"answer_piece": None}
                    continue
                if hold_quote + token in quote_pat_full:
                    hold_quote += token
                    continue
            yield {"answer_piece": hold_quote + token}
            hold_quote = ""


    # for a JSON prompt, make sure that we're only passing through the "JSON part"
    # since that is what `extract_quotes_from_completed_token_stream` expects
    if is_json_prompt:
        try:
            # json_answer_ind = model_output.index('{"answer":')
            json_answer_ind = model_output.index('{')
            if json_answer_ind != 0:
                model_output = model_output[json_answer_ind:]
            end = model_output.rfind("}")
            if end != -1:
                model_output = model_output[: end + 1]
        except ValueError:
            yield {'error_msg': 'Did not find answer pattern in response for JSON prompt'}
            logger.exception("Did not find answer pattern in response for JSON prompt")

    yield extract_quotes_from_completed_token_stream(model_output, context_docs)
