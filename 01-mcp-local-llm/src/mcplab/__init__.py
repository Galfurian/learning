"""Reusable host-side plumbing shared by all the exercises.

- ``agent``    — the orchestration loop (HOST <-> OLLAMA <-> MCP SERVER)
- ``bridge``   — MCP <-> Ollama format conversion
- ``model_io`` — rendered prompt inspection (``--show-raw``)
- ``ui``       — Rich rendering for the observation modes
- ``exercise`` — CLI used by every ``exercises/*/exeNN.py`` file
- ``checks``   — tiny assertion helpers used by ``exercises/*/check.py``
"""
