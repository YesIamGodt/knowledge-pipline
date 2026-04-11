# LLM Provider Configuration

`build_graph.py` now supports multiple LLM providers for semantic relationship inference.

## Quick Start

### Option 1: Claude (Default)

```bash
# Uses Claude Haiku by default
python tools/build_graph.py
```

Requires:
- `pip install anthropic`
- API key in `~/.config/anthropic/config.json` or `ANTHROPIC_API_KEY` env var

### Option 2: OpenAI

```bash
LLM_PROVIDER=openai LLM_MODEL=gpt-4o-mini python tools/build_graph.py
```

Requires:
- `pip install openai`
- `OPENAI_API_KEY` environment variable

### Option 3: Ollama (Local Models)

```bash
# First, install Ollama and pull a model:
# ollama pull llama3.2

LLM_PROVIDER=ollama LLM_MODEL=llama3.2 python tools/build_graph.py
```

Requires:
- `pip install requests`
- Ollama running locally (default: `http://localhost:11434`)

### Option 4: OpenAI-Compatible Endpoints

For vLLM, LocalAI, text-generation-webui, etc:

```bash
LLM_PROVIDER=openai \
LLM_BASE_URL=http://localhost:8000/v1 \
LLM_MODEL=qwen2.5 \
python tools/build_graph.py
```

## Configuration File

Create `tools/.env`:

```bash
cp tools/.env.example tools/.env
# Edit tools/.env with your preferred provider
```

## Provider Comparison

| Provider | Model Used | Speed | Quality | Cost |
|----------|-----------|-------|---------|------|
| **Claude** | claude-haiku-4-5-20251001 | ⚡ Fast | ✅ High | 💰 Low |
| **OpenAI** | gpt-4o-mini | ⚡ Fast | ✅ High | 💰 Low |
| **Ollama** | llama3.2 (7B) | 🐢 Medium | ⚠️ Medium | ✅ Free |

## Caching

The script uses SHA256 hashing to cache results:
- Only processes changed pages
- Cache stored in `graph/.cache.json`
- Delete `graph/.cache.json` to force full rebuild

## Troubleshooting

### "ImportError: anthropic package required"
```bash
pip install anthropic
```

### "ImportError: openai package required"
```bash
pip install openai
```

### "Failed to infer for page X: connection refused"
- Ensure Ollama is running: `ollama serve`
- Check `LLM_BASE_URL` if using custom endpoint

### Want to skip LLM entirely?
```bash
python tools/build_graph.py --no-infer
```
This only extracts explicit `[[wikilinks]]` (Pass 1), skipping semantic inference.
