<p align="center"><img src="../../resources/images/Serviceware-horizon-logo-rgb.svg" alt="Serviceware" width="350"></p>

# Authentication

All requests to the Serviceware Knowledge REST API require authentication, with the sole exception of the login endpoint itself. The API supports three authentication methods, each suited to different use cases.

---

## 1. Session Token (Interactive Use)

Session tokens are short-lived credentials obtained by exchanging a username and password. They are well suited for interactive use, manual testing, and short-lived scripts.

### Obtaining a Session Token

Send a `POST` request to the credentials login endpoint with your username and password:

```
POST /authentication/credentials
Content-Type: application/json; charset=utf-8
```

**Request body:**

```json
{
  "login": "your-username",
  "key": "your-password"
}
```

The response contains the authentication token in the `data.key` field:

```json
{
  "success": true,
  "data": {
    "key": "your-session-token"
  }
}
```

### Using the Session Token

Include the token in the `sabio-auth-token` header of all subsequent requests:

```
sabio-auth-token: your-session-token
```

> **Note:** Session tokens expire after the configured session timeout. Once expired, you must log in again to obtain a new token.

### Complete curl Example

```bash
# Step 1: Log in and extract the session token
BASE_URL="https://knowledge.example.com/sabio-web/services"

TOKEN=$(curl -s -X POST "$BASE_URL/authentication/credentials" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"login": "your-username", "key": "your-password"}' \
  | jq -r '.data.key')

echo "Session token: $TOKEN"

# Step 2: Use the token in a subsequent request
curl -s -X GET "$BASE_URL/content-view" \
  -H "sabio-auth-token: $TOKEN" \
  -H "Accept: application/json; charset=utf-8"
```

> **Note:** The request body uses `login` for the username and `key` for the password. An optional `realm` field can be provided to target a specific realm by name.

---

## 2. API Key (Programmatic Access)

API keys are long-lived tokens designed for programmatic access. They do not expire unless an explicit `validTo` date is set, making them ideal for integrations and automated workflows.

### Creating an API Key

Create an API key by sending a `POST` request to the API key management endpoint (requires an existing authenticated session):

```
POST /api-key
Content-Type: application/json; charset=utf-8
sabio-auth-token: your-session-token
```

**Request body:**

```json
{
  "name": "CI/CD Pipeline"
}
```

The response includes the generated `token` value:

```json
{
  "success": true,
  "data": {
    "result": {
      "id": "key-id",
      "name": "CI/CD Pipeline",
      "token": "your-api-key-token"
    }
  }
}
```

> **Important:** The full token value is only returned once, at creation time. Store it securely -- it cannot be retrieved again.

### Using an API Key

API keys use the same `sabio-auth-token` header as session tokens:

```
sabio-auth-token: your-api-key-token
```

### curl Example

```bash
BASE_URL="https://knowledge.example.com/sabio-web/services"
API_KEY="your-api-key-token"

curl -s -X GET "$BASE_URL/content-view" \
  -H "sabio-auth-token: $API_KEY" \
  -H "Accept: application/json; charset=utf-8"
```

### Managing API Keys

The API provides full CRUD operations for API key management:

| Operation | Endpoint | Description |
|-----------|----------|-------------|
| List keys | `GET /api-key` | List all API keys accessible to the current user |
| Create key | `POST /api-key` | Create a new API key |
| Get key | `GET /api-key/{id}` | Retrieve an API key by ID |
| Update key | `PUT /api-key/{id}` | Update an API key's name, description, or expiration |
| Delete key | `DELETE /api-key/{id}` | Delete and immediately revoke an API key |

Refer to the **ApiKey** section in the [API documentation](https://knowledge.example.com/sabio-web/services/api-docs) for full details.

---

## 3. Bearer Token (OAuth2 / Keycloak)

For environments with a Keycloak identity provider configured, the API accepts standard OAuth2 bearer tokens.

### Using a Bearer Token

Include the JWT obtained from your Keycloak token endpoint in the `Authorization` header:

```
Authorization: Bearer your-jwt-token
```

> **Note:** The specifics of obtaining a JWT (token endpoint URL, client ID, scopes) depend on your organization's Keycloak configuration. Consult your identity provider administrator for details.

---

## Comparison

| Method | Use Case | Expiration | Header |
|--------|----------|------------|--------|
| Session Token | Interactive use, testing | Session timeout (short-lived) | `sabio-auth-token: <token>` |
| API Key | Scripts, CI/CD, integrations | None (unless `validTo` is set) | `sabio-auth-token: <token>` |
| Bearer Token | Enterprise SSO (Keycloak) | JWT expiration (configured in IdP) | `Authorization: Bearer <token>` |

---

## Which Method Should I Use?

- **Interactive use and testing** -- Use a **session token**. It is the simplest way to get started: log in with your credentials and use the returned token. The token expires automatically after the session timeout, which limits exposure if it is inadvertently shared.

- **Automation and integration** -- Use an **API key**. API keys are purpose-built for long-running, unattended processes such as CI/CD pipelines, monitoring scripts, and third-party integrations. They do not require periodic re-authentication and can be scoped to a specific service account.

- **Enterprise SSO environments** -- Use a **bearer token**. If your organization uses Keycloak (or another OpenID Connect provider) for single sign-on, bearer tokens let you leverage your existing identity infrastructure without managing separate credentials.
