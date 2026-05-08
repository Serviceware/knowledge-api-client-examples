#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Retrieve all relations of an entity via GET /relation/{type}/{id}.
#
# Authenticates with username/password, then fetches the relations of the
# configured entity and prints a compact summary grouped by relation type.
#
# Usage:
#   ./get-relations.sh
#
# Prerequisites:
#   - curl and jq must be installed
#   - The user must have read permission on the requested entity
# ---------------------------------------------------------------------------

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL="https://<your-instance>/sabio-web/services"
USERNAME="<username>"
PASSWORD="<password>"

# Entity to query relations for.
ENTITY_TYPE="textelement"
ENTITY_ID="<entity-id>"

# Set to "true" to only return relations originating from the entity (one direction).
BASE_ONLY="false"

# ---------------------------------------------------------------------------
# Step 1: Authenticate and obtain a session token
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
# Step 2: Fetch relations
# ---------------------------------------------------------------------------
echo "Fetching relations of ${ENTITY_TYPE}/${ENTITY_ID} (baseOnly=${BASE_ONLY})..."

curl -s -G \
  "${BASE_URL}/relation/${ENTITY_TYPE}/${ENTITY_ID}" \
  -H "sabio-auth-token: ${TOKEN}" \
  --data-urlencode "baseOnly=${BASE_ONLY}" \
  | jq '{
      total: .data.total,
      byType: (.data.result | group_by(.relationType) | map({
        relationType: .[0].relationType,
        count: length,
        targets: map({id, entityType, title: .entityDetails.title})
      }))
    }'
