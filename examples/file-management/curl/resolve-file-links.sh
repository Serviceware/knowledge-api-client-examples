#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Fetch a knowledge text, extract every data-sabio-file-id reference from its
# HTML content, and resolve each one to FM metadata + pre-signed URL.
#
# Usage:
#   ./resolve-file-links.sh
#
# Prerequisites:
#   - curl and jq must be installed
#   - The user must have TEXT_READ and FILE_READ permissions
# ---------------------------------------------------------------------------

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration -- replace placeholders with values for your environment.
# ---------------------------------------------------------------------------
BASE_URL="https://<your-instance>/sabio-web/services"
USERNAME="<username>"
PASSWORD="<password>"

TEXT_ID="<text-id>"

# ---------------------------------------------------------------------------
# Step 1: Authenticate
# ---------------------------------------------------------------------------
echo "Authenticating as '${USERNAME}'..."

LOGIN_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/authentication/credentials" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "{
    \"login\": \"${USERNAME}\",
    \"key\": \"${PASSWORD}\"
  }")

TOKEN=$(echo "${LOGIN_RESPONSE}" | jq -r '.data.key')

if [ -z "${TOKEN}" ] || [ "${TOKEN}" = "null" ]; then
  echo "ERROR: Authentication failed. Response:"
  echo "${LOGIN_RESPONSE}" | jq .
  exit 1
fi

# ---------------------------------------------------------------------------
# Step 2: Fetch the text
# ---------------------------------------------------------------------------
echo "Fetching text ${TEXT_ID}..."

TEXT_JSON=$(curl -s -G \
  "${BASE_URL}/text/${TEXT_ID}" \
  -H "sabio-auth-token: ${TOKEN}" \
  --data-urlencode "mode=view")

# Collect the HTML content of all fragments into one blob for scanning.
CONTENT=$(echo "${TEXT_JSON}" | jq -r '[.data.result.fragments[].content] | join("\n")')

# ---------------------------------------------------------------------------
# Step 3: Extract data-sabio-file-id values
#
# We use a grep regex rather than a real HTML parser because this script
# stays dependency-free. For production use, prefer a proper HTML parser
# (see the Python example).
# ---------------------------------------------------------------------------
FILE_IDS=$(echo "${CONTENT}" \
  | grep -oE 'data-sabio-file-id="[^"]+"' \
  | sed -E 's/data-sabio-file-id="([^"]+)"/\1/' \
  | sort -u)

if [ -z "${FILE_IDS}" ]; then
  echo "No file references found in this text."
  exit 0
fi

echo "Found $(echo "${FILE_IDS}" | wc -l | tr -d ' ') unique file reference(s)."
echo

# ---------------------------------------------------------------------------
# Step 4: Resolve each ID
# ---------------------------------------------------------------------------
for FILE_ID in ${FILE_IDS}; do
  echo "----- ${FILE_ID} -----"

  # Metadata
  META=$(curl -s -G \
    "${BASE_URL}/fm/${FILE_ID}" \
    -H "sabio-auth-token: ${TOKEN}")

  echo "${META}" | jq '{
    id:       .data.result.id,
    filename: .data.result.filename,
    mimeType: .data.result.mimeType,
    size:     .data.result.size,
    permission: .data.result.userPermission
  }'

  # Pre-signed URL (inline; pass download=true to force download)
  URLS=$(curl -s -G \
    "${BASE_URL}/fm/url/${FILE_ID}" \
    -H "sabio-auth-token: ${TOKEN}" \
    --data-urlencode "download=false")

  echo "${URLS}" | jq '{
    url:     .data.result.url,
    preview: .data.result.preview
  }'

  echo
done
