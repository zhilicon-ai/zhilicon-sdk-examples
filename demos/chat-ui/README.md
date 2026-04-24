# Zhilicon chat UI

A single-file, zero-build HTML page that streams token-by-token from
a Zhilicon serving layer deployment. ~350 lines total including CSS,
no external dependencies, no bundler, no npm.

![one-screenshot-worth-of-it](../kernel-hello-world/README.md#tl-dr)

## What it shows

- Live SSE token streaming from `POST /v1/chat/completions`.
- OpenAI-compatible request / response shape — the same page works
  against OpenAI-API-compatible servers like vLLM or TGI with just a
  URL change.
- Temperature / top-p / max-tokens controls inline.
- Conversation history — the client keeps the full `messages` array
  and sends it on each turn, so the server can do multi-turn context
  without a session store.
- Readiness polling — the status dot lights green when the server
  responds to `/readyz`.

## Running it

### Start the serving layer

From the repo root:

```sh
pip install 'fastapi>=0.110' 'pydantic>=2.5' 'uvicorn[standard]>=0.29'
pip install -e src/sdk/python -v

# Enable CORS so the browser can talk to localhost from a file:// origin.
ZHILICON_ENABLE_CORS=true python -m uvicorn \
    zhilicon.serving.entrypoint:build --factory \
    --host 0.0.0.0 --port 8080
```

### Open the page

The page is self-contained — open it directly with a file:// URL, or
serve it over HTTP for a prettier browser experience:

```sh
cd demo/chat-ui
python -m http.server 8000
# then browse to http://localhost:8000/
```

The endpoint input defaults to `http://localhost:8080`; point it at
another host if your server lives elsewhere.

## What it does not do

- **No authentication.** Production deployments should front this with
  an ingress that terminates auth. The page assumes unauthenticated
  same-origin access.
- **No conversation persistence.** History lives in-memory in the tab
  and dies on reload. That is intentional — this is a demo surface,
  not a product.
- **No markdown / code rendering.** Messages render as plain text via
  `textContent` (XSS-safe). Rendering markdown would require a
  sanitiser like DOMPurify and a renderer — deferred until a real
  chat product is needed.
- **No file upload / multi-modal.** The chat API surface does not
  support it yet.

## Why a raw HTML page vs. a React/Vue/SPA demo

- **Zero build step.** Anyone can read the source, tweak a line, and
  refresh. No `npm install`.
- **One-file auditability.** Security-conscious deployments can diff
  the whole file against the repo and be confident nothing else is
  executing in the page.
- **Matches the "sovereign deployment" story.** The chat UI is meant
  to be served from the same cluster as the inference endpoint, not
  from a CDN. Keeping it static + tiny makes that deployment trivial.

## Related

- [ADR-0019](../../docs/adr/ADR-0019-serving-layer.md) — serving-layer scope
- [ADR-0020](../../docs/adr/ADR-0020-chat-completions-api.md) — chat API decisions
- [`src/sdk/python/zhilicon/serving/README.md`](../../src/sdk/python/zhilicon/serving/README.md)
