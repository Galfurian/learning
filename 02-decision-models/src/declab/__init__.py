"""Reusable application-side plumbing shared by all the exercises.

- ``client``    — one HTTP call to Ollama's decision endpoint (``/v1/systemone``)
- ``questions`` — local validation of the request, before the model sees it
- ``ui``        — Rich rendering for the observation modes
- ``exercise``  — CLI used by every ``exercises/*/exeNN.py`` file
- ``checks``    — assertion helpers and fake answers used by ``exercises/*/check.py``
"""
