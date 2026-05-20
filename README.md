<p align="center">
  <img src="resources/images/Serviceware-horizon-logo-rgb.svg" alt="Serviceware" width="400">
</p>

<h1 align="center" style="color: #003f72;">Serviceware Knowledge API — Client Examples</h1>

<p align="center">
  Guides, code examples, and best practices for integrating with the
  <strong>Serviceware Knowledge REST API</strong>.
</p>

---

## Overview

The Serviceware Knowledge REST API provides programmatic access to content management, search, export, and administration features. This repository contains practical guides and working code examples to help you get started quickly.

## Getting Started

Before diving into specific use cases, review these foundational guides:

| Guide | Description |
|-------|-------------|
| [Generating an API Client](guides/getting-started/generating-an-api-client.md) | Generate a typed API client from the OpenAPI specification using Swagger Codegen |
| [Authentication](guides/getting-started/authentication.md) | Authenticate API requests using session tokens, API keys, or OAuth2 bearer tokens |

## Use Case Guides

Step-by-step walkthroughs for common integration scenarios:

| Guide | Description |
|-------|-------------|
| [Export Content View as HTML](guides/content-view-export/export-html.md) | Automate the export of a content view as a self-contained HTML/ZIP archive |
| [Searching the Knowledge Base](guides/search/search-guide.md) | Run full-text searches with filters, facets, sorting, and pagination via `POST /search` |
| [Resolving File References in Text Content](guides/file-management/file-links-in-text-content.md) | Resolve `data-sabio-file-id` HTML attributes to file metadata via `GET /fm/{id}` and to pre-signed download URLs via `GET /fm/url/{id}` |
| [Working with Entity Relations](guides/relations/relations-guide.md) | Retrieve attached, linked, and embedded relations between entities via `GET /relation/{type}/{id}` |
| [Generating AI Answers](guides/answer/generating-answers.md) | Generate grounded LLM answers via blocking `POST /ai/answer` or streaming `POST /ai/answer/sse` |

## Code Examples

Working code examples organized by use case and language:

| Use Case | Language | Path |
|----------|----------|------|
| Content View Export | Java | [`examples/content-view-export/java/`](examples/content-view-export/java/) |
| Content View Export | curl | [`examples/content-view-export/curl/`](examples/content-view-export/curl/) |
| Search | Python | [`examples/search/python/`](examples/search/python/) |
| Search | curl | [`examples/search/curl/`](examples/search/curl/) |
| File Management | Python | [`examples/file-management/python/`](examples/file-management/python/) |
| File Management | curl | [`examples/file-management/curl/`](examples/file-management/curl/) |
| Relations | Python | [`examples/relations/python/`](examples/relations/python/) |
| Relations | curl | [`examples/relations/curl/`](examples/relations/curl/) |
| Answer | Python | [`examples/answer/python/`](examples/answer/python/) |
| Answer | curl | [`examples/answer/curl/`](examples/answer/curl/) |

## Prerequisites

- A running Serviceware Knowledge instance
- A user account with the required permissions (varies by use case)
- The base URL of your Knowledge instance (e.g. `https://knowledge.example.com/sabio-web/services`)

## API Documentation

The full public API specification is available as an interactive Swagger UI at:

```
https://<your-instance>/sabio-web/services/api-docs
```

You can also download the OpenAPI specification YAML from that endpoint for use with code generators and other tools.

## License

Copyright Serviceware SE. All rights reserved.
