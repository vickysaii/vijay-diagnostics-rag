import re
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

# If a section is longer than this many characters, we sub-split it further
# so that each chunk stays focused and retrieval doesn't pull in too much
# unrelated text alongside the relevant part.
MAX_CHUNK_CHARS = 1000
CHUNK_OVERLAP = 100


@dataclass
class Chunk:
    section: str
    content: str


def split_markdown_into_chunks(markdown_text: str) -> list[Chunk]:
    """
    Splits a markdown document into chunks, one per `## Section Header`,
    sub-splitting any section that's too long for a single embedding chunk.
    """
    # Split on "## Heading" lines, keeping the heading text.
    # This regex finds each "## ..." line and everything until the next one.
    pattern = re.compile(r"^## (.+)$", re.MULTILINE)
    matches = list(pattern.finditer(markdown_text))

    sections: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown_text)
        body = markdown_text[start:end].strip()
        sections.append((heading, body))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=MAX_CHUNK_CHARS,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "],
    )

    chunks: list[Chunk] = []
    for heading, body in sections:
        if len(body) <= MAX_CHUNK_CHARS:
            chunks.append(Chunk(section=heading, content=body))
        else:
            for sub_piece in splitter.split_text(body):
                chunks.append(Chunk(section=heading, content=sub_piece))

    return chunks
