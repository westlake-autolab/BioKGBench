from fastapi import FastAPI
from fastapi.responses import JSONResponse
from transformers import AutoTokenizer, AutoModel
import uvicorn
import torch
import torch.nn.functional as F
import argparse

from api_models import EmbeddingRequest
from api_models import EmbeddingResponse
import os

app = FastAPI()


def torch_gc():
    if torch.cuda.is_available():
        with torch.cuda.device(CUDA_DEVICE):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()


app = FastAPI()


def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


@app.post("/embedding")
async def get_embedding(request: EmbeddingRequest):
    global model, tokenizer
    prompt = request.texts
    max_length = request.max_length

    encoded_input = tokenizer(prompt, padding=True, truncation=True, return_tensors='pt').to(CUDA_DEVICE)
    with torch.no_grad():
        model_output = model(**encoded_input)
    embeddings = mean_pooling(model_output, encoded_input['attention_mask'])
    embeddings = F.normalize(embeddings, p=2, dim=1).cpu().numpy().tolist()
    # embeddings = F.normalize(embeddings, p=2, dim=1).cpu().squeeze().numpy().tolist()
    # if isinstance(embeddings[0], float):
    #     embeddings = [embeddings]
    torch_gc()
    return EmbeddingResponse(embeddings=embeddings)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', type=int, default=0)
    parser.add_argument('--port', type=int, default=7005)
    args = parser.parse_args()
    DEVICE_ID = args.device

    DEVICE = "cuda"
    CUDA_DEVICE = f"{DEVICE}:{DEVICE_ID}"

    tokenizer = AutoTokenizer.from_pretrained('jinaai/jina-embeddings-v2-base-zh', trust_remote_code=True)
    model = AutoModel.from_pretrained('jinaai/jina-embeddings-v2-base-zh', trust_remote_code=True) # trust_remote_code is needed to use the encode method
    model.to(CUDA_DEVICE)
    model.eval()
    uvicorn.run(app, host='0.0.0.0', port=args.port, workers=1)
