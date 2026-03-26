<p align="center"><img src="../../resources/images/Serviceware-horizon-logo-rgb.svg" alt="Serviceware" width="350"></p>

# Exporting a Content View as HTML

The Serviceware Knowledge REST API allows you to export a content view as a self-contained ZIP archive of static HTML files. The export includes all texts, the full tree structure, attached documents and images, and the content view's theme. The resulting archive can be hosted on any web server or opened locally in a browser — no running Knowledge instance required.

This guide walks you through the API calls needed to automate this export.

## Prerequisites

- **`BRANCH_EXPORT` permission** — Your user account must have the `BRANCH_EXPORT` permission assigned via its role. Without it, the export endpoint returns `403 Forbidden`.
- **Content view ID** — You need the numeric ID of the content view you want to export. If you do not know it, Step 2 below shows how to look it up.
- **Authentication token** — A valid session token obtained by logging in via the API. See the [Authentication](../getting-started/authentication.md) guide for full details on session tokens, API keys, and OAuth2 bearer tokens.

## Step 1: Authenticate

Obtain a session token by sending your credentials to the login endpoint:

```bash
curl -s -X POST \
  "https://<your-instance>/sabio-web/services/authentication/credentials" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{
    "login": "<username>",
    "key": "<password>"
  }'
```

The response contains the token in `data.key`:

```json
{
  "success": true,
  "data": {
    "key": "abc123-session-token"
  }
}
```

Use this token value in the `sabio-auth-token` header for all subsequent requests.

> **Note:** For a detailed explanation of all authentication methods (credentials, API keys, OAuth2), see the [Authentication](../getting-started/authentication.md) guide.

## Step 2: Find the Content View ID

If you already know the content view ID, skip to Step 3. Otherwise, list all content views available to your user:

```bash
curl -s \
  "https://<your-instance>/sabio-web/services/branch" \
  -H "sabio-auth-token: <your-token>"
```

The response contains a list of content views. Each entry includes an `id` and a `title`:

```json
{
  "success": true,
  "data": {
    "result": [
      {
        "id": "42",
        "title": "Product Documentation",
        "description": "Public product docs"
      },
      {
        "id": "87",
        "title": "Internal Knowledge Base",
        "description": "Internal support articles"
      }
    ]
  }
}
```

Note the `id` of the content view you want to export.

## Step 3: Export the Content View

Call the export endpoint with the content view ID and `type=html`:

```bash
curl -s \
  "https://<your-instance>/sabio-web/services/branch-export/<content-view-id>?type=html" \
  -H "sabio-auth-token: <your-token>" \
  -o export.zip
```

The server streams the response as a binary ZIP file with `Content-Type: application/zip`. The `Content-Disposition` header contains a generated filename following the pattern `sabio_{viewId}_{userId}.zip`.

## Step 4: Save and Verify the File

If you used `-o export.zip` as shown above, curl writes the response body directly to that file. You can verify the archive is valid:

```bash
unzip -t export.zip
```

To extract the HTML site:

```bash
unzip export.zip -d exported-site
```

Open `exported-site/index.html` in a browser to view the exported content view.

> **Note:** The exported archive is fully self-contained. All documents, images, stylesheets, and JavaScript files are included. No network access to the Knowledge instance is needed to view the exported site.

## Available Export Formats

The `type` query parameter accepts the following values:

| Type | Format | MIME Type | Extension |
|------|--------|-----------|-----------|
| `csv` | Semicolon-separated CSV | `text/csv` | `.csv` |
| `xml` | XML document | `application/xml` | `.xml` |
| `msword` | Word document | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `.docx` |
| `html` | ZIP archive with static HTML | `application/zip` | `.zip` |

## Error Responses

| Status Code | Meaning |
|-------------|---------|
| `400 Bad Request` | The `type` query parameter is missing or invalid. |
| `403 Forbidden` | The authenticated user does not have the `BRANCH_EXPORT` permission. |
| `501 Not Implemented` | The requested export type is recognized but no service implementation is available on the server. |

## Complete Examples

For complete, runnable examples that combine all the steps above into a single script or program, see:

- **Bash/curl:** [`../../examples/content-view-export/curl/export-html.sh`](../../examples/content-view-export/curl/export-html.sh)
- **Java (HttpClient):** [`../../examples/content-view-export/java/ExportContentViewHtml.java`](../../examples/content-view-export/java/ExportContentViewHtml.java)
