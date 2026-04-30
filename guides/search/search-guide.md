<p align="center"><img src="../../resources/images/Serviceware-horizon-logo-rgb.svg" alt="Serviceware" width="350"></p>

# Searching the Knowledge Base

The Serviceware Knowledge REST API provides a full-text search endpoint that returns content items, files, contacts, users, and other entities matching a query. The result set is automatically scoped to the resources the calling user has read permission on.

This guide walks through the `POST /search` endpoint: query syntax, filtering, faceting, sorting, pagination, and dictionary-driven synonym expansion.

## Prerequisites

- **`SEARCH_READ` permission** -- Your user account must have the `SEARCH_READ` permission assigned via its role. Without it, the endpoint returns `403 Forbidden`.
- **Authentication** -- A valid session token, API key, or OAuth2 bearer token. See the [Authentication](../getting-started/authentication.md) guide.
- **Base URL** -- The service entry point of your Knowledge instance, e.g. `https://<your-instance>/sabio-web/services`.

## Endpoint

```
POST /search
Content-Type: application/json; charset=utf-8
sabio-auth-token: <your-token>
```

## Request Body

The request body is a `SearchRequest` object. All fields are optional — an empty body returns the first page of results for the wildcard query `*`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | `"*"` | Full-text query. Supports the underlying search engine's query syntax (`AND`, `OR`, `NOT`, phrase quoting, wildcard `*`, etc.). |
| `start` | integer | `0` | Index of the first result to return. Used for pagination. |
| `limit` | integer | `10` | Maximum number of results in the response. |
| `fields` | array of string | `["*"]` | Whitelist of result fields to return. `["*"]` returns all fields. |
| `sort` | array of `FieldSort` | -- | Sort order. Each entry has `property` (index field name) and `direction` (`ASC` / `DESC`). When omitted, results are ordered by relevance score. |
| `filters` | array of `IndexFieldFilter` | -- | Restricts the result set. See [Filters](#filters). |
| `filterMode` | enum | `filtered` | Controls which facet values are returned. See [Facets](#facets). |
| `facets` | array of string | -- | Names of facets (= index property names) to compute alongside the result. |
| `useDictionary` | boolean | `true` | When `true`, the query is expanded with synonyms from the configured dictionary. |
| `provider` | enum | -- | `elastic` or `search-api`. Selects the backend search provider. Leave unset to use the system default. |

### Minimal request

```json
{
  "query": "vacation policy"
}
```

## Response Body

The response is a `SearchResultResponse` (a `ListResultResponse` envelope with search-specific extras). The hits are in `data.result`, where each item is a `SearchResult` whose properties depend on its `objectType` (text, document, file, contact, user, ...).

```json
{
  "success": true,
  "status": { "code": 200, "httpStatus": 200, "success": true, "text": "OK" },
  "data": {
    "start": 0,
    "limit": 10,
    "total": 42,
    "queryTerm": "vacation policy",
    "originalQueryTerm": null,
    "autoReSearch": false,
    "filter": [
      {
        "property": "resource",
        "title": "Type",
        "values": [
          { "value": "text", "title": "Text", "count": 30, "checked": false },
          { "value": "document", "title": "Document", "count": 12, "checked": false }
        ]
      }
    ],
    "result": [
      {
        "objectType": "SearchResult",
        "id": "8e7d1f...",
        "resource": "text",
        "title": "Annual Vacation Policy",
        "excerpt": "...all <em>vacation</em> requests must be...",
        "score": "12.3",
        "lastModified": "2026-04-14T09:21:00Z",
        "matchedTerms": {
          "title": ["Vacation"],
          "content": ["vacation", "policy"],
          "highlights": ["vacation", "policy"]
        }
      }
    ]
  }
}
```

### Notable response fields

- `data.total` -- Total hits matching the query (independent of `limit`).
- `data.queryTerm` / `data.originalQueryTerm` -- If the original query produced no results, the search engine may automatically re-run the query with an alternative term (auto re-search). `originalQueryTerm` then holds the submitted query and `queryTerm` the executed alternative; `autoReSearch` is `true`. Otherwise `originalQueryTerm` is `null`.
- `data.filter` -- The computed facets, requested via the request's `facets` field.
- `result[].score` -- Relevance score; higher means a better match.
- `result[].matchedTerms` -- Terms that matched, suitable for client-side highlighting.

## Query Syntax

The `query` field accepts the underlying search engine's query syntax. Common patterns:

| Goal | Example |
|------|---------|
| All items | `*` |
| Single term | `vacation` |
| Required AND optional | `vacation +policy` |
| Phrase | `"vacation policy"` |
| Wildcard prefix | `vac*` |
| Boolean | `vacation AND (policy OR rules)` |
| Negation | `vacation NOT policy` |

> **Note:** Special characters reserved by the query parser (`+ - && || ! ( ) { } [ ] ^ " ~ * ? : \`) must be escaped with a backslash if you want to match them literally.

## Filters

Filters narrow the result set without affecting the query relevance. Each filter targets one index property and lists allowed values; multiple values for the same property are combined with logical OR; multiple filter objects are combined with logical AND.

```json
{
  "query": "*",
  "filters": [
    { "property": "resource", "values": ["text", "document"] },
    { "property": "language", "values": ["en"] }
  ]
}
```

### Negation

Prefix the property name with `-` to invert a filter:

```json
{
  "filters": [
    { "property": "-resource", "values": ["file"] }
  ]
}
```

This returns all items whose `resource` is **not** `file`.

## Facets

Facets are aggregated counts of values for a given index property within the current result set. Use them to build "filter by..." UI elements.

Request facets via the `facets` field; the result is returned in `data.filter`:

```json
{
  "query": "vacation",
  "facets": ["resource", "language", "ownerGroup"]
}
```

The `filterMode` field controls which facet values appear in the response:

| Mode | Behavior |
|------|----------|
| `all` | All facet values for the unfiltered result set. |
| `filtered` | Only facet values for the current (filtered) result set. **Default.** |
| `unselectedKategories` | Only facets where no value is currently filtered. |
| `unselectedValues` | Within each facet, only values not currently selected as a filter. |

## Sorting

Sort by one or more index fields. Each entry is a `{ property, direction }` pair:

```json
{
  "query": "vacation",
  "sort": [
    { "property": "lastModified", "direction": "DESC" },
    { "property": "title", "direction": "ASC" }
  ]
}
```

When `sort` is omitted, results are ordered by relevance score (descending).

## Pagination

Pagination uses zero-based offsets:

```json
{ "query": "*", "start": 0,  "limit": 25 }
{ "query": "*", "start": 25, "limit": 25 }
{ "query": "*", "start": 50, "limit": 25 }
```

Read `data.total` from the first response to determine how many pages exist. There is no cursor; use `start` + `limit` for every page.

> **Note:** Deep pagination (very large `start` values) can be slow on large indexes. If you need to iterate over the full result set, prefer narrower filters or the CSV download endpoint (`POST /search/download-link`).

## Synonym Expansion

When `useDictionary` is `true` (the default), the query is expanded using synonyms from the Knowledge instance's configured dictionary. Set `useDictionary` to `false` to disable expansion and match only the literal query terms.

## Field Whitelisting

To minimize payload size, restrict the returned fields with `fields`:

```json
{
  "query": "vacation",
  "fields": ["id", "title", "resource", "score", "lastModified"]
}
```

Only the listed properties are populated on each result item.

## Error Responses

| Status | Meaning |
|--------|---------|
| `400 Bad Request` | The request body is malformed or contains invalid field values. |
| `401 Unauthorized` | The authentication header is missing or invalid. |
| `403 Forbidden` | The authenticated user does not have the `SEARCH_READ` permission. |
| `default` | Other failures are returned as a generic `ErrorResponse` (`status` + `success`). |

## Complete Examples

For complete, runnable examples that combine the building blocks above, see:

- **Bash/curl:** [`../../examples/search/curl/search.sh`](../../examples/search/curl/search.sh)
- **Python (basic search):** [`../../examples/search/python/search.py`](../../examples/search/python/search.py)
- **Python (paginated iteration):** [`../../examples/search/python/search_paginated.py`](../../examples/search/python/search_paginated.py)
- **Python (faceted search):** [`../../examples/search/python/search_facets.py`](../../examples/search/python/search_facets.py)
