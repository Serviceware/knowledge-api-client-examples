---
name: extending-api-docs
description: Use when adding new public API documentation — guides, code examples, or OpenAPI spec entries — to the Serviceware Knowledge API. Covers the full workflow from writing the guide in the examples repo through marking schemas with x-public, adding externalDocs links, and verifying the build pipeline.
---

# Extending API Documentation

## Overview

Add new public API documentation by writing a guide in the examples repository, marking the relevant OpenAPI operations and schemas as public, and linking them together via `externalDocs`. The build pipeline then includes them in the filtered public spec and Swagger UI.

## When to Use

- Adding a new use case guide (e.g. "Exporting content", "Managing API keys")
- Making an internal endpoint publicly documented
- Adding code examples for an existing public endpoint
- Extending authentication or getting-started documentation

## Repositories

| Repository | Purpose |
|------------|---------|
| `knowledge-backend` (`rest-api/src/main/resources/openapi/spec/`) | OpenAPI spec source files |
| `knowledge-api-client-examples` | Guides, code examples, brand assets |

## Quick Reference: The Checklist

```
1. Write the guide         → knowledge-api-client-examples/guides/<topic>/
2. Write code examples     → knowledge-api-client-examples/examples/<topic>/
3. Mark operations         → x-public: true on each operation in tag YAML
4. Mark schemas            → x-public: true on all transitively referenced schemas
5. Add externalDocs        → on the primary operation, linking to the guide
6. Verify pipeline         → bundle → filter → prune → check public spec
7. Commit both repos
```

## Step 1: Write the Guide

Create a markdown guide in the examples repository under `guides/<topic>/`.

**Template:**

```markdown
<p align="center"><img src="../../resources/images/Serviceware-horizon-logo-rgb.svg" alt="Serviceware" width="350"></p>

# Guide Title

Brief intro — what this feature does and why you'd use it.

## Prerequisites

- Required permissions
- What you need to know beforehand
- Link to [Authentication](../getting-started/authentication.md)

## Step 1: ...

## Step 2: ...

## Complete Examples

- [Bash/curl](../../examples/<topic>/curl/<script>.sh)
- [Java](../../examples/<topic>/java/<Class>.java)
```

**Style rules:**
- Serviceware logo at the top of every guide
- Use placeholders, never real credentials (`<your-instance>`, `<your-token>`)
- Link to the authentication guide rather than re-explaining auth
- Include complete curl examples inline in the guide
- Separate runnable code examples go in `examples/<topic>/<language>/`

## Step 2: Mark Operations as Public

Add `x-public: true` to each operation that should appear in the public spec:

```yaml
paths:
  /my-endpoint:
    get:
      x-public: true    # <-- add this
      description: ...
      operationId: myOperation
```

## Step 3: Mark Transitively Referenced Schemas

Every schema, response, and parameter referenced by a public operation must also be marked. Trace the full dependency tree:

```
Operation
├── Request body schema        → x-public: true
├── Response schema            → x-public: true
│   └── allOf parent schemas   → x-public: true
│       └── Their $ref deps    → x-public: true (recurse)
└── Error response             → x-public: true (if not already marked)
```

**Common schemas that may already be marked** (check before adding):
- `ResponseStatus`, `StatusDetails`, `ErrorResponse`
- `SingleResultResponse`, `ListResultResponse`, `Result`, `ListResult`
- `AdminEntity`, `BaseEntity`
- `ResultConstraint`, `Notification`

**Where to add the marker** — as a sibling of `type` or `description`:

```yaml
MySchema:
  x-public: true          # <-- add here
  type: object
  properties: ...
```

## Step 4: Add externalDocs to Operations

Link the guide from the operation using OpenAPI's `externalDocs`:

```yaml
get:
  operationId: myOperation
  externalDocs:
    description: Step-by-step guide with code examples
    url: https://github.com/Serviceware/knowledge-api-client-examples/blob/main/guides/<topic>/<guide>.md
```

Swagger UI renders this as a clickable "Find more info here" link below the operation description.

## Step 5: Verify the Build Pipeline

Run all three steps and validate:

```bash
cd rest-api

# 1. Bundle full spec
pnpm exec -- swagger-cli bundle src/main/resources/openapi/spec/openapi.yaml \
  --outfile src/main/resources/openapi/spec/_build/knowledge.yaml --type yaml

# 2. Filter to public-only
pnpm exec -- openapi-filter --flags x-public --inverse --strip --valid --info \
  -- src/main/resources/openapi/spec/_build/knowledge.yaml \
  src/main/resources/openapi/spec/_build/knowledge-public.yaml

# 3. Prune unused schemas
pnpm exec -- openapi-format src/main/resources/openapi/spec/_build/knowledge-public.yaml \
  -o src/main/resources/openapi/spec/_build/knowledge-public.yaml \
  --filterFile src/main/resources/openapi/spec/filter-public.json
```

**Validation checks:**

```bash
# Only expected operationIds
grep "operationId" src/main/resources/openapi/spec/_build/knowledge-public.yaml

# No internal schemas leaked
grep -c "User\|Realm\|Group\|Bookmark" src/main/resources/openapi/spec/_build/knowledge-public.yaml

# externalDocs links present
grep -A2 "externalDocs" src/main/resources/openapi/spec/_build/knowledge-public.yaml

# No x-public markers in output (--strip removes them)
grep "x-public" src/main/resources/openapi/spec/_build/knowledge-public.yaml
```

## Common Mistakes

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| Forgot `x-public` on a transitive schema | Dangling `$ref` in public spec, Swagger UI shows error | Trace full dependency tree before committing |
| Used inline description link instead of `externalDocs` | Link not rendered natively by Swagger UI | Use `externalDocs` block on the operation |
| Forgot to mark security schemes | `securitySchemes` section stripped from public spec | Add `x-public: true` to each scheme in `openapi.yaml` |
| Guide uses real credentials in examples | Security risk in public GitHub repo | Always use placeholders |
| Didn't run the prune step | Public spec contains hundreds of unrelated schemas | Run all three pipeline steps |

## Build Pipeline Architecture

```
Tag files (x-public: true on operations + schemas)
    │
    ▼
swagger-cli bundle ──► _build/knowledge.yaml (full spec)
    │                         │
    │                         ▼
    │                  openapi-generator (code gen, unchanged)
    ▼
openapi-filter --inverse --flags x-public --strip
    │
    ▼
_build/knowledge-public.yaml (public paths only, all schemas)
    │
    ▼
openapi-format --filterFile filter-public.json
    │
    ▼
_build/knowledge-public.yaml (public paths + referenced schemas only)
    │
    ▼
ApiDocsStartupTask inlines into Swagger UI HTML page
```
