<p align="center"><img src="../../resources/images/Serviceware-horizon-logo-rgb.svg" alt="Serviceware" width="350"></p>

# Working with Entity Relations

The Serviceware Knowledge REST API exposes the **relations** between entities: which files are attached to a textelement, which textelements link to a file, which images are embedded in which content, and so on. This guide walks through the `GET /relation/{type}/{id}` endpoint — when to use it, how to read the response, and how to interpret the `attached` / `linked` / `embedded` distinction.

## Prerequisites

- **Authentication** — A valid session token, API key, or OAuth2 bearer token. See the [Authentication](../getting-started/authentication.md) guide.
- **Read permission on the queried entity** — The endpoint returns relations scoped to what the calling user is allowed to see. Targets the user is not permitted to read are filtered out of the response.
- **Base URL** — The service entry point of your Knowledge instance, e.g. `https://<your-instance>/sabio-web/services`.

## Endpoint

```
GET /relation/{type}/{id}
sabio-auth-token: <your-token>
```

| Path parameter | Type | Description |
|----------------|------|-------------|
| `type` | enum | The resource type of the entity whose relations you want to retrieve. Common values: `textelement`, `file`, `text`. |
| `id` | string | The ID of the entity. |

| Query parameter | Type | Default | Description |
|-----------------|------|---------|-------------|
| `baseOnly` | boolean | `false` | When `false`, both directions are returned — relations originating from the entity and relations pointing at it. When `true`, only relations originating from the entity are returned. See [Direction](#direction) below. |

## Direction

A relation has two ends: a **base** entity (where the relation originates) and a **target** entity (what the relation points at). The endpoint always reports relations in a uniform shape — the requested entity appears as the base, and the other side appears in the response.

- **`baseOnly=false` (default)** — Return both directions. For relations where the requested entity is naturally the target (e.g. asking about a file that is attached to several textelements), the response swaps the sides so the file still appears as the base. Use this when you want every relation involving the entity, regardless of direction.
- **`baseOnly=true`** — Return only relations that originate from the requested entity. Use this when the direction matters (e.g. "list the files attached to *this* textelement, not textelements that link to this file").

## Relation Types

Each relation has a [`relationType`](#relation-types) describing how the target is used by the base:

| Type | Meaning | Example |
|------|---------|---------|
| `attached` | Direct attachment relationship between the two entities. | A file attached to a textelement. |
| `linked` | The target is referenced via hyperlink in the base's HTML content. | A file linked from the body of a textelement. |
| `embedded` | The target is embedded inline within the base's HTML content. | An image rendered inline in the body of a textelement. |

These values are stable enums — they will not change for a given relation across requests.

## Response Body

The response is a `RelationListResponse` — a `ListResultResponse` envelope with the list of relations in `data.result`.

```json
{
  "success": true,
  "status": { "code": 200, "httpStatus": 200, "success": true, "text": "OK" },
  "data": {
    "start": 0,
    "limit": 3,
    "total": 3,
    "result": [
      {
        "id": "f-9c2a...",
        "entityType": "file",
        "relationType": "attached",
        "entityDetails": {
          "id": "f-9c2a...",
          "title": "Q3-policy.pdf",
          "mimeType": "application/pdf",
          "size": 184320,
          "path": [
            { "id": "tree-root", "title": "Knowledge Base" },
            { "id": "tree-hr",   "title": "HR" }
          ]
        }
      },
      {
        "id": "te-71fb...",
        "entityType": "textelement",
        "relationType": "linked",
        "entityDetails": {
          "id": "te-71fb...",
          "title": "Onboarding checklist",
          "textId": "txt-44ad...",
          "fragmentIndex": 2,
          "contentviewIds": ["cv-public", "cv-internal"]
        }
      },
      {
        "id": "f-3ed0...",
        "entityType": "file",
        "relationType": "embedded",
        "entityDetails": {
          "id": "f-3ed0...",
          "title": "logo.png",
          "mimeType": "image/png",
          "size": 24080
        }
      }
    ]
  }
}
```

### Notable fields

- `result[].id` and `result[].entityType` — Identify the **target** entity of the relation. Together they form a `(type, id)` pair you can pass back to other endpoints.
- `result[].relationType` — `attached`, `linked`, or `embedded` (see [Relation Types](#relation-types)).
- `result[].entityDetails` — Human-readable details about the target. Most fields are optional and only populated for the entity types they apply to. The detail schema is shared across target types, so:
  - For **file** targets, expect `mimeType`, `size`, and a tree `path`.
  - For **textelement** targets, expect `textId` *or* `templateId` (depending on whether the textelement belongs to a text or a text template), `fragmentIndex`, and `contentviewIds`.
  - For **version** targets, expect `versionNumber`.
- `entityDetails.title` — May be `null` if the calling user is not permitted to see the target's text.

## Common Use Cases

### List files attached to a textelement

```
GET /relation/textelement/{textelement-id}?baseOnly=true
```

Filter the response to `relationType == "attached"` and `entityType == "file"` to obtain only the attached files.

### Find textelements linking to a file

```
GET /relation/file/{file-id}
```

By default both directions are returned. The textelements that hyperlink to the file appear as targets with `relationType == "linked"`.

### Find content embedding an image

```
GET /relation/file/{image-id}
```

Filter the response to `relationType == "embedded"` to discover which textelements render the image inline.

## Error Responses

| Status | Meaning |
|--------|---------|
| `401 Unauthorized` | The authentication header is missing or invalid. |
| `403 Forbidden` | The authenticated user does not have read permission on the requested entity. |
| `404 Not Found` | No entity with the given `(type, id)` exists, or the user is not permitted to see it. |
| `default` | Other failures are returned as a generic `ErrorResponse` (`status` + `success`). |

## Complete Examples

For complete, runnable examples, see:

- **Bash/curl:** [`../../examples/relations/curl/get-relations.sh`](../../examples/relations/curl/get-relations.sh)
- **Python:** [`../../examples/relations/python/get_relations.py`](../../examples/relations/python/get_relations.py)
