"""Adapted from unit 04 (04-reranking/src/reranklab/generation.py): the context, the prompt, the checks.

Two kinds of context reach the same generator:

- chunks (pipeline A), each with its chunk id: `[rovers-missions]`;
- facts from the graph (pipelines B and C), one per line, each with a fact
  id: `[f3] Rover R-1 serves_bay Bay 5 (source: rovers-missions)`.

The answer cites ids in square brackets. A citation that exists is not a
citation that supports the claim: check_citations only proves the first.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from .corpus import Chunk
from .evalset import Question
from .graph import Edge, Graph
from .scenario import SCENARIO

DEFAULT_BUDGET = 1500
REFUSAL = SCENARIO.generation["refusal"]
DOCUMENTS = SCENARIO.generation["documents_label"]


def estimate_tokens(text: str) -> int:
    return (len(text) + 3) // 4


@dataclass
class Context:
    ids: list[str]
    text: str
    tokens: int
    sources: dict[str, str] = field(default_factory=dict)   # fact id -> edge source; chunk id -> chunk id
    dropped: int = 0


def chunk_context(chunks: Sequence[Chunk], budget: int = DEFAULT_BUDGET) -> Context:
    ids, parts, used, dropped = [], [], 0, 0
    for c in chunks:
        if c.id in ids:
            continue
        part = f"[{c.id}]\n{c.text}"
        cost = estimate_tokens(part) + 1
        if used + cost > budget:
            dropped += 1
            continue
        ids.append(c.id)
        parts.append(part)
        used += cost
    text = "\n\n".join(parts)
    return Context(ids, text, estimate_tokens(text), {i: i for i in ids}, dropped)


def label(graph: Graph, node_id: str) -> str:
    node = graph.nodes.get(node_id)
    if node is None or not node.name or node.name == node_id:
        return node_id
    return f"{node.name} ({node_id})"


def fact_line(graph: Graph, edge: Edge) -> str:
    return f"{label(graph, edge.s)} {edge.r} {label(graph, edge.o)}"


def facts_context(graph: Graph, edges: Sequence[Edge], budget: int = DEFAULT_BUDGET) -> Context:
    """One line per edge, numbered; the same edge once. The source stays outside the text the model reads."""
    ids, lines, sources, used, dropped = [], [], {}, 0, 0
    seen = set()
    for e in edges:
        if (e.s, e.r, e.o) in seen:
            continue
        seen.add((e.s, e.r, e.o))
        fid = f"f{len(ids) + 1}"
        line = f"[{fid}] {fact_line(graph, e)}"
        cost = estimate_tokens(line) + 1
        if used + cost > budget:
            dropped += 1
            continue
        ids.append(fid)
        lines.append(line)
        sources[fid] = e.source
        used += cost
    text = "\n".join(lines)
    return Context(ids, text, estimate_tokens(text), sources, dropped)


SYSTEM_PROMPT = f"""You answer questions about {SCENARIO.generation["domain"]}.
Use only the excerpts or facts in the user message. Each one starts with its id in square brackets.
After every sentence that uses an excerpt or a fact, write its id in square brackets, for example [f2].
If they do not contain the answer, reply exactly: {REFUSAL}
Do not use any other knowledge."""


def build_messages(question: str, context: Context, system_prompt: str = SYSTEM_PROMPT) -> list[dict]:
    body = context.text or "(none)"
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{DOCUMENTS}:\n\n{body}\n\nQuestion: {question}"},
    ]


BRACKET = re.compile(r"\[([^\[\]]+)\]")
CITE_ID = re.compile(r"^[a-z0-9][a-z0-9_/#.:-]*$")


def cited_ids(answer: str) -> list[str]:
    found: list[str] = []
    for inside in BRACKET.findall(answer):
        for token in re.split(r"[,;\s]+", inside.strip()):
            token = token.lower() if token[:1] in "fF" and token[1:].isdigit() else token
            if CITE_ID.match(token) and token not in found:
                found.append(token)
    return found


def is_refusal(answer: str) -> bool:
    return REFUSAL.lower().rstrip(".") in answer.lower()


@dataclass
class CitationReport:
    cited: list[str]
    unknown: list[str]
    refused: bool
    ok: bool
    problem: str


def check_citations(answer: str, context_ids: Sequence[str]) -> CitationReport:
    cited = cited_ids(answer)
    unknown = [c for c in cited if c not in set(context_ids)]
    refused = is_refusal(answer)
    if refused:
        problem = "refusal with citations" if cited else ""
    elif not cited:
        problem = "no citations"
    elif unknown:
        problem = "cites ids that are not in the context: " + ", ".join(unknown)
    else:
        problem = ""
    return CitationReport(cited, unknown, refused, problem == "", problem)


def names_of(graph: Graph, node_id: str) -> list[str]:
    node = graph.nodes.get(node_id)
    if node is None:
        return [node_id]
    return [x for x in [node.name, *node.aliases, node_id] if x]


def mentioned(answer: str, graph: Graph, node_id: str) -> bool:
    text = answer.lower()
    return any(re.search(rf"(?<![a-z0-9]){re.escape(n.lower())}(?![a-z0-9])", text) for n in names_of(graph, node_id))


@dataclass
class AnswerScore:
    found: list[str]        # gold answers the text names
    missing: list[str]      # gold answers it does not name
    extra: list[str]        # other nodes of the same types that it names
    refused: bool
    ok: bool


def score_answer(answer: str, question: Question, graph: Graph) -> AnswerScore:
    """A check by code: the answer names every gold node and no other node of their types; or it refuses."""
    refused = is_refusal(answer)
    if not question.answerable:
        return AnswerScore([], [], [], refused, refused)
    found = [g for g in question.gold_answers if mentioned(answer, graph, g)]
    missing = [g for g in question.gold_answers if g not in found]
    types = {graph.nodes[g].type for g in question.gold_answers if g in graph.nodes}
    # "Busy" names the Busy flag of every device: a node that shares a name with a gold node is not extra.
    gold_names = {x.lower() for g in question.gold_answers for x in names_of(graph, g)}
    extra = [n.id for n in graph.nodes.values()
             if n.type in types and n.id not in question.gold_answers
             and not gold_names & {x.lower() for x in names_of(graph, n.id)} and mentioned(answer, graph, n.id)]
    if question.count is not None:
        count_ok = re.search(rf"(?<!\d){question.count}(?!\d)", answer) is not None
        return AnswerScore(found, missing, extra, refused, not refused and count_ok)
    return AnswerScore(found, missing, extra, refused, not refused and not missing and not extra)
