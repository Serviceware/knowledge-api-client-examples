<p align="center"><img src="../../resources/images/Serviceware-horizon-logo-rgb.svg" alt="Serviceware" width="350"></p>

# Resolving File References in Knowledge Text Content

Knowledge texts contain HTML that may reference files managed by **File Management** (FM). Instead of embedding a hard-coded URL, the HTML carries a custom attribute that holds the file's stable ID. Your client is responsible for turning that ID into either a metadata lookup or a downloadable URL at render time.

This guide covers:

- The `data-sabio-file-id` HTML attribute — what it looks like, where it appears.
- `GET /fm/{id}` — fetch a file's metadata (filename, MIME type, permissions, ...).
- `GET /fm/url/{id}` — obtain a short-lived pre-signed URL for the file's binary.
- An end-to-end pattern: fetch a text, scan its content, resolve every file reference.

## Prerequisites

- **`FILE_READ` permission** — Both endpoints require the calling user to hold the `FILE_READ` role.
- **`TEXT_READ` permission** — Needed to fetch the text whose content you want to resolve. See the [Reading and Searching Texts](../texts/texts-guide.md) guide.
- **Authentication** — A valid session token, API key, or OAuth2 bearer token. See the [Authentication](../getting-started/authentication.md) guide.
- **Base URL** — The service entry point of your Knowledge instance, e.g. `https://<your-instance>/sabio-web/services`.

---

## The `data-sabio-file-id` Attribute

When a knowledge text is authored and a file from FM is inserted into the rich-text editor, the editor adds a `data-sabio-file-id="<file-id>"` attribute to the surrounding HTML element. The attribute is preserved verbatim in the stored content and is the contract your client uses to resolve the reference later.

The attribute may appear on any tag that can carry a media reference. The most common cases:

```html
<!-- A clickable link to a downloadable file (e.g. a PDF attachment) -->
<a data-sabio-file-id="853646d7881f43aa9995c82656396316"
   data-sabio-link-target="window"
   href="#">
  Annual-Report-2026.pdf
</a>

<!-- An embedded image -->
<img data-sabio-file-id="5288176b47364998a2ac1823409a6680"
     src="data:,"
     alt="Architecture diagram"
     style="max-width:100%;">

<!-- An embedded object, video, or audio element -->
<object data-sabio-file-id="..." data="..."></object>
<video  data-sabio-file-id="..." src="..."></video>
<audio  data-sabio-file-id="..." src="..."></audio>
```

**Important:** the `href` and `src` placeholders in stored content are intentionally inert (`#`, `data:,`, or a stale URL). The authoritative reference is the ID in `data-sabio-file-id`. Always resolve through the API rather than following the placeholder URL.

### Extracting IDs Client-Side

Any HTML parser that supports attribute selectors will do. Examples:

- **JavaScript (browser / jsdom):**
  ```js
  const ids = Array.from(
    doc.querySelectorAll("[data-sabio-file-id]")
  ).map(el => el.getAttribute("data-sabio-file-id"));
  ```
- **Python (BeautifulSoup):**
  ```python
  ids = [el["data-sabio-file-id"] for el in soup.select("[data-sabio-file-id]")]
  ```
- **Java (Jsoup):**
  ```java
  List<String> ids = Jsoup.parse(html)
      .getElementsByAttribute("data-sabio-file-id")
      .stream().map(e -> e.attr("data-sabio-file-id"))
      .toList();
  ```

Deduplicate IDs before resolving — the same file may appear multiple times in one text.

---

## Resolving an ID to File Metadata — `GET /fm/{id}`

```
GET /fm/{id}
sabio-auth-token: <your-token>
```

| Path parameter | Type | Description |
|----------------|------|-------------|
| `id` | string | The value of `data-sabio-file-id`. |

### Response Body

The response is a `FileResponse` envelope. The metadata is in `data.result`:

```json
{
  "success": true,
  "status": { "code": 200, "httpStatus": 200, "success": true, "text": "OK" },
  "data": {
    "result": {
      "id": "853646d7881f43aa9995c82656396316",
      "objectType": "file",
      "title": "Annual Report 2026",
      "filename": "Annual-Report-2026.pdf",
      "mimeType": "application/pdf",
      "size": 1843204,
      "extension": "pdf",
      "isBinary": true,
      "userPermission": 1,
      "path": [
        { "id": "fld-root", "title": "Knowledge Base" },
        { "id": "fld-reports", "title": "Reports" }
      ],
      "branches": [{ "id": "cv-public", "title": "Public" }],
      "validFrom": null,
      "validTo": null
    }
  }
}
```

Use this when you need to **describe** the file (render the filename next to the link, choose an icon based on MIME type, gate the UI on `userPermission`, etc.) without yet downloading the binary.

### Notable Response Fields

- `data.result.filename` — Original filename. Suitable for the visible link text.
- `data.result.mimeType` — MIME type. Use to pick the right HTML element (`<img>` for images, `<video>` for videos, generic link otherwise).
- `data.result.userPermission` — CRUD bitfield for the calling user. Bit 0 = read, bit 1 = create, bit 2 = update, bit 3 = delete. `1` = read-only, `15` = full CRUD. Hide edit/delete affordances client-side based on this.
- `data.result.path` — Folder breadcrumb, useful for tooltips ("This file lives in: Knowledge Base > Reports").
- `data.result.validFrom` / `validTo` — If set, the file is only visible to agent users inside this window. The endpoint already enforces this; you only need to read it for display.

### Error Responses

| Status | Meaning |
|--------|---------|
| `401 Unauthorized` | The authentication header is missing or invalid. |
| `403 Forbidden` | The user does not have `FILE_READ`, or no read permission on this specific file. |
| `404 Not Found` | No file with the given ID exists, or the user is not permitted to see it. |
| `default` | Other failures are returned as a generic `ErrorResponse`. |

---

## Resolving an ID to a Downloadable URL — `GET /fm/url/{id}`

```
GET /fm/url/{id}?download=false
sabio-auth-token: <your-token>
```

| Path parameter | Type | Description |
|----------------|------|-------------|
| `id` | string | The value of `data-sabio-file-id`. |

| Query parameter | Type | Default | Description |
|-----------------|------|---------|-------------|
| `download` | boolean | `false` | If `true`, the returned `url` is constructed so that fetching it triggers a browser download (`Content-Disposition: attachment`). If `false`, the URL is suitable for **inline rendering** — embedding in `<img src>`, `<video src>`, etc. |

### Response Body

```json
{
  "success": true,
  "status": { "code": 200, "httpStatus": 200, "success": true, "text": "OK" },
  "data": {
    "result": {
      "url": "https://files.example.com/storage/...&X-Amz-Signature=...",
      "preview": "https://files.example.com/storage/...&X-Amz-Signature=..."
    }
  }
}
```

### `url` vs. `preview`

| Field | What it is |
|-------|------------|
| `url` | Pre-signed URL of the **original** uploaded binary. Always populated. |
| `preview` | Either a pre-signed URL of the **converted preview** (e.g. PDF rendering of an Office document) **or** a status string. |

The status strings for `preview`:

| Value | Meaning |
|-------|---------|
| `done` | Conversion finished but no separate preview is needed (the original is already viewable in a browser). |
| `pending` | Conversion is in progress; poll again later. |
| `unsupported` | The file's MIME type cannot be converted to a preview. |
| `none` | No preview is configured for this file. |

**Always inspect `preview` before using it as a URL** — a naive `<img src="{{preview}}">` will break if the server returned `pending`.

### Pre-signed URL Lifetime

The URLs are short-lived. Lifetime is configured per realm and should not be assumed by clients. Re-fetch the URL when you actually need to load the binary, rather than caching it long-term. The `id` is stable; the URL is not.

### Error Responses

Same as `GET /fm/{id}`.

---

## End-to-End Pattern: Resolve Every File Reference in a Text

A typical client renders a knowledge text like this:

```
1. GET /text/{id}                       → text payload (HTML in fragments[].content)
2. Parse content; collect every data-sabio-file-id value (deduplicated).
3. For each ID:
     GET /fm/{id}        → metadata (filename, mime, …)
     GET /fm/url/{id}    → pre-signed URL for the binary
4. Rewrite the HTML:
     - Replace href="#" / src="data:," with the pre-signed URL.
     - Optionally swap the visible link text for filename.
     - Optionally pick <img> vs <video> vs <a> based on mimeType.
5. Render the rewritten HTML.
```

The two FM endpoints can be called in parallel. The metadata call is needed for **display decisions** (filename, MIME-based element choice, permission gating); the URL call is needed for the **binary fetch** itself. If you only need one of the two, call only that one.

### Performance Notes

- Deduplicate IDs before issuing requests; the same image may appear many times in one text.
- The two calls per file can be issued in parallel.
- Pre-signed URLs are short-lived — fetch them just-in-time, not eagerly at page load if the binary won't be needed immediately.

---

## Complete Examples

For complete, runnable examples, see:

- **Bash/curl:**
  - [`../../examples/file-management/curl/resolve-file-links.sh`](../../examples/file-management/curl/resolve-file-links.sh) — fetch a text, extract every `data-sabio-file-id`, resolve each one to metadata + pre-signed URL.
- **Python:**
  - [`../../examples/file-management/python/resolve_file_links.py`](../../examples/file-management/python/resolve_file_links.py) — same flow with `requests` + `BeautifulSoup`.
