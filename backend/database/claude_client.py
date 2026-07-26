import logging
import os
from typing import Optional

import httpx
from anthropic import Anthropic
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-5"
MAX_DOCUMENT_CHARS = 8000  # per-document cost guard, not a feature

_client: Optional[Anthropic] = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        # Same SSL relaxation app.py/vector_store.py apply for this environment's
        # intercepted HTTPS — httpx (which this SDK uses) doesn't honor the
        # stdlib ssl._create_default_https_context monkeypatch app.py sets.
        _client = Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            http_client=httpx.Client(verify=False),
        )
    return _client


def _model_name() -> str:
    return os.environ.get("MODEL", DEFAULT_MODEL)


class DocumentExtraction(BaseModel):
    document_id: int
    relevant: bool = Field(description="True only if this document actually "
        "contains information that answers or matches the filter phrase.")
    question_text: Optional[str] = Field(None, description="A short, "
        "question-like sentence based on the text surrounding the match. "
        "Required when relevant is true, otherwise null.")
    answer_short: Optional[str] = Field(None, description="Concise summary, "
        "80 chars or fewer. Required when relevant is true, otherwise null.")
    answer_detail: Optional[str] = Field(None, description="The fuller "
        "supporting context from the document. Required when relevant is "
        "true, otherwise null.")


class FilterExtractionResult(BaseModel):
    extractions: list[DocumentExtraction]


class ExtractionError(Exception):
    """Any failure to obtain/parse a Claude extraction. Caller must catch
    this and fall back to the existing regex-based extraction."""


def extract_filter_matches(filter_text: str, documents: list[dict]) -> list[DocumentExtraction]:
    """documents: [{"id": int, "description": str|None, "text": str}, ...]
    (text = db._document_full_text output). Returns one DocumentExtraction
    per input document. Raises ExtractionError on any API/parsing failure."""
    if not documents:
        return []

    doc_blocks = "\n\n".join(
        f"--- Document id={d['id']} ---\n"
        f"Description: {d['description'] or '(none)'}\n"
        f"Content:\n{d['text'][:MAX_DOCUMENT_CHARS]}"
        for d in documents
    )
    prompt = (
        "A user typed this search filter while looking for a question/answer pair:\n"
        f"  {filter_text!r}\n\n"
        "Below are candidate documents a vector search judged loosely related. "
        "For EACH document, decide whether it actually contains information "
        "that answers or matches the filter phrase, and extract a question/"
        "answer pair from it if so. Return exactly one extraction entry per "
        "document listed (matched by document_id); for any document that "
        "is not actually relevant, set relevant=false and leave the other "
        "fields null.\n\n"
        f"{doc_blocks}"
    )

    try:
        response = _get_client().messages.parse(
            model=_model_name(),
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            output_format=FilterExtractionResult,
        )
    except Exception as e:
        raise ExtractionError(str(e)) from e

    if response.stop_reason != "end_turn" or response.parsed_output is None:
        raise ExtractionError(f"unusable response, stop_reason={response.stop_reason!r}")

    logger.info(
        "claude_client/extract_filter_matches filter=%r documents=%d -> %d extraction(s) "
        "input_tokens=%s output_tokens=%s",
        filter_text, len(documents), len(response.parsed_output.extractions),
        response.usage.input_tokens, response.usage.output_tokens,
    )
    return response.parsed_output.extractions


FILES_API_BETA = "files-api-2025-04-14"


def upload_pdf(filename: str, data: bytes) -> str:
    """Uploads a PDF via the Anthropic Files API. Returns the file_id, which
    can be referenced as a `document` content block in later messages instead
    of re-sending the raw bytes."""
    uploaded = _get_client().beta.files.upload(
        file=(filename, data, "application/pdf"),
        betas=[FILES_API_BETA],
    )
    return uploaded.id


def chat_reply(messages: list[dict], file_ids: Optional[list[str]] = None) -> str:
    """messages: [{"role": "user"|"assistant", "content": str}, ...] (the
    Chat.jsx contract). file_ids: Files-API PDF ids (from upload_pdf) attached
    as native document context on the final (current) user turn only —
    earlier turns are sent as plain text history. Returns the reply text."""
    if not messages:
        return ""

    *history, last = messages
    content = [
        {"type": "document", "source": {"type": "file", "file_id": file_id}}
        for file_id in (file_ids or [])
    ]
    content.append({"type": "text", "text": last["content"]})

    response = _get_client().beta.messages.create(
        model=_model_name(),
        max_tokens=1024,
        messages=[*history, {"role": "user", "content": content}],
        betas=[FILES_API_BETA],
    )
    return "".join(block.text for block in response.content if block.type == "text")
