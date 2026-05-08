<p align="center"><img src="../../resources/images/Serviceware-horizon-logo-rgb.svg" alt="Serviceware" width="350"></p>

# Reading and Searching Texts

A **text** is the primary content unit in a Serviceware Knowledge instance. Each text has a title, one or more text elements (the actual editable content), validity dates, content view assignments, and metadata such as approval state, ratings, and tags.

This guide covers two endpoints:

- `GET /text/{id}` — fetch a single text by ID, including its full content.
- `POST /text/search` — full-text search restricted to texts.

Both endpoints scope their responses to the texts (and text elements) the calling user is allowed to read.

## Prerequisites

- **`TEXT_READ` permission** — Your user account must have the `TEXT_READ` permission assigned via its role. Without it, both endpoints return `403 Forbidden`.
- **Authentication** — A valid session token, API key, or OAuth2 bearer token. See the [Authentication](../getting-started/authentication.md) guide.
- **Base URL** — The service entry point of your Knowledge instance, e.g. `https://<your-instance>/sabio-web/services`.

---

## Reading a Single Text — `GET /text/{id}`

```
GET /text/{id}
sabio-auth-token: <your-token>
```

| Path parameter | Type | Description |
|----------------|------|-------------|
| `id` | string | The ID of the text. |

| Query parameter | Type | Default | Description |
|-----------------|------|---------|-------------|
| `mode` | enum | `view` | Controls how the content is loaded. `view` performs view-time transformations such as resolving placeholder values; `edit` returns the raw editable content. |
| `filter` | string | — | Reserved for future use; currently ignored. |

### `mode` — `view` vs. `edit`

| Mode | Behavior |
|------|----------|
| `view` | **Default.** Returns the rendered text: placeholder values resolved, replacements applied, content ready for display. |
| `edit` | Returns the raw editable content without view-time transformations. Use this when fetching the text for an authoring/editing UI. |

### Response Body

The response is a `TextResponse` envelope. The text itself is in `data.result`:

```json
{
  "success": true,
  "status": { "code": 200, "httpStatus": 200, "success": true, "text": "OK" },
  "data": {
    "result": {
      "id": "txt-44ad...",
      "title": "Annual Vacation Policy",
      "treePath": "Knowledge Base > HR > Policies",
      "fragments": [
        {
          "id": "te-71fb...",
          "content": "<p>All <strong>vacation</strong> requests must be submitted...</p>",
          "tags": ["hr", "policy"],
          "attachments": [],
          "branches": [{ "id": "cv-public", "title": "Public" }]
        }
      ],
      "userPermission": 15,
      "groupPermission": 11,
      "validFrom": null,
      "validTo": null,
      "visible": true
    }
  }
}
```

### Notable Response Fields

- `data.result.fragments` — The list of [TextFragment](#) (text element) items that make up the text. A text always has at least one fragment.
- `data.result.fragments[].content` — The HTML content of the fragment. Whether placeholders are resolved depends on the `mode` query parameter.
- `data.result.fragments[].textLinks` — Hyperlinks, embedded images, and other media references found inside `content`. Resolve these client-side using the `replacementToken` to render the final rich text.
- `data.result.userPermission` / `groupPermission` — CRUD permission bitfields. Each is an integer 0–15 where bit 0 = read, bit 1 = create, bit 2 = update, bit 3 = delete. A value of `15` means full CRUD; `1` means read-only.
- `data.result.branches` — The content views assigned to the text. Visibility for unprivileged users depends on whether their groups share a content view with the text.
- `data.result.approval` — The approval state, if approval is configured for this text's tree node.
- `data.result.validFrom` / `validTo` — Optional validity window. Unprivileged users do not see the text outside this window.

### Error Responses

| Status | Meaning |
|--------|---------|
| `401 Unauthorized` | The authentication header is missing or invalid. |
| `403 Forbidden` | The authenticated user does not have the `TEXT_READ` permission, or no read permission on this specific text. |
| `404 Not Found` | No text with the given ID exists, or the user is not permitted to see it. |
| `default` | Other failures are returned as a generic `ErrorResponse`. |

---

## Searching Texts — `POST /text/search`

```
POST /text/search
Content-Type: application/json; charset=utf-8
sabio-auth-token: <your-token>
```

This endpoint runs a full-text search restricted to texts (no files, contacts, users, or other resource types are returned). The request and response shapes are identical to the generic `POST /search` endpoint.

For the full reference of the request body — query syntax, filters, facets, sorting, pagination, and synonym expansion — see the [Searching the Knowledge Base](../search/search-guide.md) guide. Everything in that guide applies here, except that the result set is implicitly limited to texts.

### When to use `/text/search` vs. `/search`

| Use case | Endpoint |
|----------|----------|
| You only want text hits, ever. | `/text/search` |
| You want to mix text, file, contact, and other hits in one query. | `/search` |
| You want text hits but conditionally include files. | `/search` with a `resource` filter. |

### Minimal request

```json
{
  "query": "vacation policy",
  "limit": 10
}
```

### Response Body

The response is a `SearchResultResponse` envelope. Hits are in `data.result`. Each hit's `objectType` will reflect that it is a text result:

```json
{
  "success": true,
  "status": { "code": 200, "httpStatus": 200, "success": true, "text": "OK" },
  "data": {
    "start": 0,
    "limit": 10,
    "total": 7,
    "queryTerm": "vacation policy",
    "result": [
      {
        "objectType": "SearchResult",
        "id": "txt-44ad...",
        "resource": "text",
        "title": "Annual Vacation Policy",
        "excerpt": "...all <em>vacation</em> requests must be...",
        "score": "12.3",
        "lastModified": "2026-04-14T09:21:00Z"
      }
    ]
  }
}
```

To fetch the full content of a hit, take its `id` and call `GET /text/{id}`.

### Error Responses

| Status | Meaning |
|--------|---------|
| `400 Bad Request` | The request body is malformed or contains invalid field values. |
| `401 Unauthorized` | The authentication header is missing or invalid. |
| `403 Forbidden` | The authenticated user does not have the `TEXT_READ` permission. |
| `default` | Other failures are returned as a generic `ErrorResponse`. |

---

## Common Pattern: Search → Fetch

The two endpoints are designed to be chained: search to find candidate texts, then fetch the full content of the selected hit.

```
POST /text/search           →  list of hits with id, title, excerpt, score
GET  /text/{first-hit-id}   →  full text + fragments + metadata
```

The complete examples below demonstrate this pattern end-to-end.

---

## Complete Examples

For complete, runnable examples, see:

- **Bash/curl:**
  - [`../../examples/texts/curl/find-text.sh`](../../examples/texts/curl/find-text.sh) — fetch a single text by ID.
  - [`../../examples/texts/curl/search-and-fetch.sh`](../../examples/texts/curl/search-and-fetch.sh) — search texts and fetch the top hit.
- **Python:**
  - [`../../examples/texts/python/find_text.py`](../../examples/texts/python/find_text.py) — fetch a single text by ID.
  - [`../../examples/texts/python/search_and_fetch.py`](../../examples/texts/python/search_and_fetch.py) — search texts and fetch the top hit.
