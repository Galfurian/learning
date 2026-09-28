# Ollama on WSL / Linux

Ollama is the local model runtime used by learning units that need an LLM.

This document is repository-level because installation, the local API, model management, and troubleshooting are reusable across multiple learning units.

## Mental model

Keep these three operations separate:

```text
install Ollama
      |
      v
ollama serve              long-running local API server
      |
      v
http://localhost:11434
      ^
      |
ollama pull MODEL         download model weights
      ^
      |
your program / curl / ollama run
```

- `ollama serve` starts the local Ollama API service.
- `ollama pull <model>` downloads a model.
- `ollama run <model>` starts an interactive CLI session with a model. It will also pull the model if needed.
- Programs in this repository normally talk to the API at `http://localhost:11434`.

For a WSL-first setup, install the Linux version **inside WSL**. This keeps the learning workspace and the model runtime in the same environment and avoids Windows/WSL networking being part of the exercise.

## 1. Install Ollama inside WSL

Run:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify:

```bash
ollama --version
```

## 2. Start the Ollama server

First check whether the installer/system service already started it:

```bash
curl http://localhost:11434/api/tags
```

If you get JSON back, Ollama is already running. You do **not** need another `ollama serve`.

If the connection fails, start it manually in a separate terminal:

```bash
ollama serve
```

Leave that terminal open.

Then, from another WSL terminal:

```bash
curl http://localhost:11434/api/tags
```

You should now get JSON describing the locally available models.

### If WSL is using systemd

You can also inspect the service with:

```bash
systemctl status ollama
```

and start it with:

```bash
sudo systemctl start ollama
```

The manual `ollama serve` route is enough for the learning exercises and makes it obvious which process is providing the API.

## 3. Download a model

For a small machine and exercises involving tool calling:

```bash
ollama pull qwen3:1.7b
```

List installed models:

```bash
ollama list
```

The `qwen3:1.7b` Ollama package is roughly 1.4 GB and advertises tool support, which makes it a useful low-resource starting point.

If your machine has more headroom, use:

```bash
ollama pull qwen3:4b
```

## 4. Sanity-check inference

The simplest interactive test is:

```bash
ollama run qwen3:1.7b
```

Type something such as:

```text
Reply with exactly: hello local model
```

Exit the interactive session with:

```text
/bye
```

This exits the CLI conversation; it does not necessarily stop the Ollama API service.

## 5. Sanity-check the HTTP API

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "qwen3:1.7b",
  "messages": [
    {"role": "user", "content": "Reply with exactly: API works"}
  ],
  "stream": false
}'
```

If this works, Python programs can use Ollama too.

## 6. Normal startup for a learning session

In practice, after the first installation the routine is usually:

```bash
# Terminal 1, only if Ollama is not already running
ollama serve
```

Then:

```bash
# Terminal 2
curl http://localhost:11434/api/tags
ollama list
cd ~/path/to/learning/<unit>
# run the unit
```

You do **not** need to run `ollama run ...` before a Python program. The program only needs:

1. the Ollama server reachable;
2. the requested model already downloaded.

## 7. Useful commands

```bash
ollama --version
ollama list
ollama pull qwen3:1.7b
ollama run qwen3:1.7b
ollama ps
ollama serve
```

## 8. Windows-native Ollama vs Ollama inside WSL

Both can work, but choose one setup deliberately.

For these learning units, the default assumption is:

```text
WSL
├── git repo
├── Python
├── MCP server
└── Ollama
```

That gives the simplest path: everything can use `localhost:11434`.

If Ollama runs natively on Windows instead, WSL-to-Windows networking becomes an extra concern. That can be useful later, but it is unnecessary complexity for the first exercises.

## Troubleshooting

### `ollama: command not found`

Open a new shell after installation, or check where the installer placed the executable:

```bash
which ollama
```

### `curl: (7) Failed to connect ... 11434`

The API server is not reachable. Run:

```bash
ollama serve
```

and retry the curl command from another terminal.

### Model not found

Download it:

```bash
ollama pull qwen3:1.7b
```

### The laptop is too slow

For the learning goal, latency is not important. Tool calling still demonstrates the same architecture on CPU.

Start with `qwen3:1.7b`; only move to a larger model if the small model fails to follow the tool-calling task reliably.
