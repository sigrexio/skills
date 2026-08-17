---
name: sigrex-social
description: Manage Sigrex friends, shared webhooks, shared strategies, and multi-user access safely. Use when sending friend requests, sharing a webhook, collaborating with another Sigrex user, or revoking shared access.
metadata:
  author: sigrex
  version: "1.0"
---

# Sigrex Social And Sharing

Sharing changes who can submit data or connect assets. Confirm the recipient,
asset, and intended permission before sharing. Treat every payload submitted by
another user as untrusted.

## Friends

The Friends feature supports sending, accepting, ignoring, cancelling, and
deleting friend requests, plus blocking users. New friend requests may be
disabled in account settings. A friendship is required before sharing
webhooks or other connected assets.

The public API reference does not document Friends CRUD endpoints. Use the
Sigrex UI or an MCP tool that explicitly exposes the friend operation; do not
invent REST routes.

## Sharing Model

- Shared Bot Webhooks keep the real URL/hash private from the recipient. The
  recipient sees the name and description and can connect the shared webhook to
  their own Signal Bot.
- Shared Data Webhooks allow another user to submit JSON. All attached
  Reactions process the incoming event, regardless of sender.
- Deleting a friendship revokes access to previously shared assets according to
  the product documentation.

Management API sharing routes under `/api/v2`:

```text
GET  /webhook/bot/{id}/shares
POST /webhook/bot/share/{id}        {"userId":"..."}
DELETE /webhook/bot/share/{id}
GET  /webhook/bot/shared
GET  /webhook/bot/shared/with/{id}
GET  /webhook/bot/shared/by/{id}

GET  /webhook/data/{id}/shares
POST /webhook/data/share/{id}       {"userId":"..."}
DELETE /webhook/data/share/{id}
GET  /webhook/data/shared
GET  /webhook/data/shared/with/{id}
GET  /webhook/data/shared/by/{id}
```

These calls require signed API authentication. A share request can fail when
the user is not a friend or an ID is invalid. A shared Data Webhook is a
multi-tenant input boundary; require key protection and validate event schema
inside the attached Reaction.

## Safe Collaboration Workflow

1. Verify the recipient's user ID through a trusted source.
2. Share the smallest required webhook or strategy.
3. Keep the hook inactive or test-only while the recipient verifies it.
4. Review attached bots and reactions before enabling execution.
5. Remove the share when collaboration ends and rotate exposed keys.

## Canonical Docs

- https://docs.sigrex.io/social/friends.md
- https://docs.sigrex.io/api-reference/reference/hooks/bot-hooks.md
- https://docs.sigrex.io/api-reference/reference/hooks/data-hooks.md
