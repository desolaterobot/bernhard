import os
from strands import Agent
from dotenv import load_dotenv

from agent_tools import (
    semantic_search,
    get_document_names,
    get_full_document,
    get_document_page,
    create_document,
    get_created_documents,
    read_created_document,
    convert_markdown_document,
)

load_dotenv(".env")

PROMPT_PATH = os.getenv(
    "AGENT_SYSTEM_PROMPT",
    os.path.join(os.path.dirname(__file__), "system_prompt.txt"),
)

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    PROMPT = f.read().strip()

MODEL_ID = os.getenv("LLM_MODEL_ID")  

def build_agent():
    kwargs = {
        "system_prompt": PROMPT,
        "tools": [
            semantic_search,
            get_document_names,
            get_full_document,
            get_document_page,
            create_document,
            get_created_documents,
            read_created_document,
            convert_markdown_document,
        ],
        "model": MODEL_ID
    }
    return Agent(**kwargs)

agent = build_agent()

if __name__ == "__main__":
    print(agent("Tell me about yourself"))
