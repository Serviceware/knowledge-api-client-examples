<p align="center"><img src="../../resources/images/Serviceware-horizon-logo-rgb.svg" alt="Serviceware" width="350"></p>

# Generating AI Answers

Serviceware Knowledge exposes a question-answering endpoint that combines neural search over the calling user's accessible knowledge content with a Large Language Model to produce a grounded natural-language answer. The same logic is offered in two delivery modes:

- `POST /ai/answer` — blocking. The server holds the connection open until the full answer is generated and then returns it in a single JSON response.
- `POST /ai/answer/sse` — streaming via Server-Sent Events. The server emits the answer incrementally so a client can render it as it is produced.

Use the blocking endpoint when you only need the final answer (batch jobs, simple bots). Use the streaming endpoint when you want a typing-style UX in a chat-like interface.

## Prerequisites

- **Authentication** — A valid session token, API key, or OAuth2 bearer token. See the [Authentication](../getting-started/authentication.md) guide.
- **Read access to knowledge content** — The user's role / group permissions determine which texts and files are eligible as sources. The endpoint only grounds the LLM on content the calling user is permitted to see.
- **Base URL** — The service entry point of your Knowledge instance, e.g. `https://<your-instance>/sabio-web/services`.

---

## The `sabio-client` Header (Required)

Both AI answer endpoints **require** a `sabio-client` header on every request. It identifies your integration to the Knowledge backend for usage tracking, analytics, and audit purposes.

The header value is a JSON object (sent verbatim, not URL-encoded):

```
sabio-client: {"name":"acme-portal","version":"1.4.2","tracking":{"tab":"home","navigation":"answers"}}
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Stable identifier for your integration. Choose a short, lowercase, hyphenated string (e.g. `acme-portal`, `support-bot`). This is the value that appears as the channel name in usage reports — pick one and stick with it. |
| `version` | no | Free-form version string for your integration (e.g. `1.4.2`). Useful for distinguishing traffic from different releases of your client. |
| `tracking.tab` | no | Identifier of the tab/page the request was issued from, if your UI has multiple. |
| `tracking.navigation` | no | Identifier of the navigation context (e.g. the section of your UI the user is in). |
| `tracking.index` | no | Zero-based index of the result the user interacted with, if applicable. |

**Pick a `name` that uniquely identifies your integration.** Do not reuse a value that another integrator might already be using — the channel name is how usage is attributed back to a client.

---

## Blocking — `POST /ai/answer`

```
POST /ai/answer
Content-Type: application/json
sabio-auth-token: <your-token>
sabio-client: {"name":"<your-integration>"}
```

### Minimal Request

```json
{
  "query": "How do I reset my password?"
}
```

With no `textIds`, the server runs a neural search over the user's accessible knowledge content, picks the top hits as context, and asks the LLM to produce a grounded answer.

### Targeted Request (Sources Provided)

If your client already knows which knowledge texts the answer should be grounded in (e.g. after a manual selection in the UI), pass their IDs in `textIds` to skip neural search:

```json
{
  "query": "How do I reset my password?",
  "textIds": ["txt-44ad...", "txt-7b2c..."]
}
```

### Restricting Resource Types

When relying on neural search, you can restrict the candidate sources to specific resource types (e.g. only texts, no files) via `includedResources`:

```json
{
  "query": "How do I reset my password?",
  "includedResources": ["text"]
}
```

If `includedResources` is omitted or empty, every resource type the user has access to is eligible.

### Response Body

```json
{
  "success": true,
  "status": { "code": 200, "httpStatus": 200, "success": true, "text": "OK" },
  "data": {
    "result": {
      "answer": "To reset your password, open the login screen and click 'Forgot password' [ref:txt-44ad...].",
      "sources": [
        { "id": "txt-44ad...", "title": "Password Reset Procedure", "resource": "text" },
        { "id": "txt-7b2c...", "title": "Account Recovery FAQ",     "resource": "text" }
      ],
      "success": true
    }
  }
}
```

### Citations

The `answer` text may contain inline citations of the form `[ref:<source-id>]`. Match each `<source-id>` against the `id` of an entry in `sources` to find which knowledge article a citation points at. Not every entry in `sources` is necessarily cited; only those the LLM actually used.

A simple client-side parser:

```python
import re
CITATION_RE = re.compile(r"\[ref:([^\]]+)\]")
cited_ids = set(CITATION_RE.findall(answer))
```

### `success: false`

If the LLM declines to answer (e.g. the question cannot be answered from the available knowledge), `success` is `false`. The `answer` field may still contain a short explanatory message ("I don't have enough information to answer that.") — render it as you would any other answer, but do not treat it as authoritative.

---

## Streaming — `POST /ai/answer/sse`

```
POST /ai/answer/sse
Content-Type: application/json
sabio-auth-token: <your-token>
sabio-client: {"name":"<your-integration>"}
Accept: text/event-stream
```

The request body is identical to the blocking endpoint. The response is a [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) stream.

### Event Flow

| Order | Event | When | Payload (`SseAnswer`) |
|-------|-------|------|------------------------|
| 1 | `sources` | Immediately, before generation starts | `sources` populated with the full list of candidate sources |
| 2 | `answer` (0…n) | Once per incremental text chunk | `answer` populated with the next chunk |
| 3 | `done` | After the last `answer` chunk | `done: true`, `success` |

If an error occurs at any point:

| Event | When | Payload |
|-------|------|---------|
| `error` | Instead of `done` | `success: false`, `error: { code, text }` |

No `done` event follows an `error` event — the client should treat `error` as terminal and close the connection.

### Reconstructing the Full Answer

Concatenate the `answer` field of every `answer` event in order. Inline `[ref:<source-id>]` citations appear in this stream just like they do in the blocking response.

### Browser Example

```js
const response = await fetch("/sabio-web/services/ai/answer/sse", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
    "sabio-auth-token": token,
    "sabio-client": JSON.stringify({ name: "acme-portal", version: "1.4.2" }),
  },
  body: JSON.stringify({ query }),
});

const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
// Parse the stream as SSE; see the linked code examples for a complete implementation.
```

The browser's built-in `EventSource` only supports `GET`; since this endpoint is `POST`, use `fetch` with manual SSE parsing instead.

### Why Streaming?

Streaming produces a noticeably better UX for chat-style interfaces — the user sees the answer typing in instead of waiting for the full response. Operationally, the two endpoints consume the same LLM tokens and run for roughly the same wall-clock time; streaming just makes that wall-clock time felt-time shorter.

---

## Error Responses

Both endpoints share the same error model. For the blocking endpoint, errors arrive as a standard `ErrorResponse`. For SSE, they arrive as an `error` SSE event.

| Status | Meaning |
|--------|---------|
| `400 Bad Request` | Malformed request body, missing `query`, or missing `sabio-client` header. |
| `401 Unauthorized` | The authentication header is missing or invalid. |
| `429 Too Many Requests` | The realm has hit its AI answer rate limit. |
| `default` | Other failures (LLM provider outage, internal errors) are returned as a generic `ErrorResponse`. |

---

## Complete Examples

For complete, runnable examples, see:

- **Bash/curl:**
  - [`../../examples/answer/curl/generate-answer.sh`](../../examples/answer/curl/generate-answer.sh) — blocking call against `POST /ai/answer`.
  - [`../../examples/answer/curl/generate-answer-sse.sh`](../../examples/answer/curl/generate-answer-sse.sh) — streaming call against `POST /ai/answer/sse`, printing each event as it arrives.
- **Python:**
  - [`../../examples/answer/python/generate_answer.py`](../../examples/answer/python/generate_answer.py) — blocking call.
  - [`../../examples/answer/python/generate_answer_sse.py`](../../examples/answer/python/generate_answer_sse.py) — streaming call with a minimal SSE parser.
