"""MCP server with one tool: search_manuals. The EXE09 host starts it over stdio.

Nothing may print to stdout here: stdout carries the MCP messages.
"""

import config
from mcp.server import MCPServer

from raglab.cache import EmbeddingCache
from raglab.chunking import chunk_all
from raglab.corpus import PLANT_MANUALS, load_manuals
from raglab.embedders import OllamaEmbedder
from raglab.hybrid import BM25, HybridSearch
from raglab.index import Index

mcp = MCPServer("plant-manuals")
_search = None


def searcher():
    global _search
    if _search is None:
        chunks = chunk_all(load_manuals(PLANT_MANUALS), config.SIZE, config.OVERLAP)
        index = Index.build(chunks, OllamaEmbedder(cache=EmbeddingCache()))
        _search = {"semantic": index.search, "keyword": BM25(chunks).search,
                   "hybrid": HybridSearch(index, BM25(chunks)).search}[config.RETRIEVER]
    return _search


@mcp.tool()
def search_manuals(query: str, k: int = 3) -> dict:
    """Search the plant's machine manuals. Returns the k most relevant excerpts, each with an id to cite.

    Args:
        query: A short search query, for example 'Ibis R-37 error E-6213'.
        k: How many excerpts to return (1-8).
    """
    hits = searcher()(query, max(1, min(int(k), 8)))
    return {"excerpts": [
        {"id": h.chunk.id, "section_id": h.chunk.section_id, "source": h.chunk.source,
         "title": h.chunk.title, "text": h.chunk.text, "score": round(h.score, 4)}
        for h in hits
    ]}


if __name__ == "__main__":
    mcp.run(transport="stdio")
