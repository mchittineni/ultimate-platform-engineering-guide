---
title: "What is idempotency and why do platform APIs need it?"
id: 30
category: "Platform Architecture"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-architecture
  - interview-questions
---

# What is idempotency and why do platform APIs need it?

**Short answer:** An operation is idempotent if doing it once and doing it many times leave the system in the same state. Platform APIs need it because everything that calls them retries - CI jobs, GitOps reconcilers, controllers, CLIs on flaky networks, and AI agents - and a retry of a non-idempotent "create database" produces two databases. Idempotency is what makes retrying safe, and safe retries are what make automation reliable.

## Detail

**The definition, precisely.** Idempotency is about the resulting state, not the response. Deleting a resource twice is idempotent even if the second call returns "not found", because the world ends up the same. Incrementing a counter is not idempotent: every call changes the state again.

**Why retries are unavoidable.** A client sends "create a Postgres instance" and the connection drops before the response arrives. Did it succeed? The client cannot know. Its only safe options are to retry or to give up, and automation always retries. If the API is not idempotent, the platform's users - developers running a pipeline, a reconciler acting on their behalf - get duplicated infrastructure, double billing, or conflicting resources, and usually find out much later.

**How APIs achieve it - four common mechanisms.**

- **Client-chosen names.** If the caller names the resource (`name: orders-db`), a second create finds the name already taken and can return the existing resource. This is why Kubernetes objects have names and why `generateName` - which picks a random suffix - is not idempotent.
- **Idempotency keys.** For operations without a natural name, the client sends a unique key with the request, and the server stores the key with the result. A repeat with the same key returns the stored result rather than acting again. Stripe popularised the `Idempotency-Key` HTTP header; the IETF has a draft standardising it; AWS APIs such as EC2 `RunInstances` accept a `ClientToken` for the same purpose.
- **Put, not post.** `PUT /databases/orders-db` with the full desired state is naturally idempotent - "make it look like this". `POST /databases` - "make a new one" - is not, unless combined with a key.
- **Declarative reconciliation.** A controller that compares desired and observed state and only acts on the difference is idempotent by construction. Applying the same manifest ten times does nothing after the first. See [declarative versus imperative configuration](./what-is-the-difference-between-declarative-and-imperative-configuration.md).

**The subtle part: the key must cover the whole operation.** If a platform API creates a database and then a DNS record and then a secret, and fails between step two and three, the retry must resume rather than start again. That means each step is itself idempotent (create-if-not-exists, update-to-match) or the workflow records its progress. This is where many hand-written platform APIs break.

**Same key, different request.** A good implementation rejects a repeated key whose request body differs from the original, instead of silently returning the old result. Otherwise a client bug that reuses keys looks like success.

**Trade-offs.** Idempotency keys need storage and an expiry policy - keeping them forever grows without bound, expiring them too early reopens the duplicate window. Name-based idempotency means users must choose names, which is a small burden but also good practice. And idempotency does not make an operation safe to run concurrently; two different requests racing for the same name still need a conflict rule, such as optimistic concurrency via a resource version.

## Example

```text
A platform API for provisioning, with an idempotency key. The CLI generates
the key once per user action and reuses it on every retry.

  POST /v1/databases
  Idempotency-Key: 5f1c9a2e-3d44-4b8e-9d0a-7e2f6c1b8a90
  Content-Type: application/json

  { "name": "orders-db", "owner": "group:team-payments", "size": "small" }

  -> connection reset (client never sees a response)

  POST /v1/databases                         <- automatic retry, same key
  Idempotency-Key: 5f1c9a2e-3d44-4b8e-9d0a-7e2f6c1b8a90

  <- 202 Accepted
     { "id": "db-7c1e", "name": "orders-db", "status": "provisioning" }
     Idempotent-Replayed: true              <- stored result, no second database
```

```python
# Server side, minimal: look up the key before acting, store the result after.
# The unique constraint on (key) makes concurrent duplicates fail safely.
def create_database(key: str, body: dict) -> dict:
    existing = db.fetch_one("SELECT request_hash, response FROM idempotency WHERE key = %s", key)
    if existing:
        if existing.request_hash != hash_body(body):
            raise Conflict("Idempotency-Key reused with a different request")
        return existing.response

    resource = provisioner.ensure_database(name=body["name"], size=body["size"])  # create-if-absent
    response = {"id": resource.id, "name": resource.name, "status": resource.status}
    db.execute(
        "INSERT INTO idempotency (key, request_hash, response, expires_at) "
        "VALUES (%s, %s, %s, now() + interval '24 hours')",
        key, hash_body(body), response,
    )
    return response
```

## Interview tips

- Define it by resulting state, not by response code - "delete twice is idempotent even though the second returns 404" is a crisp way to show you know the difference.
- Explain why it matters with the lost-response scenario: the client cannot know whether the create happened, so it must be safe to retry.
- Name at least two mechanisms: client-chosen names and idempotency keys, plus the observation that reconciliation is idempotent by design.
- Mention multi-step operations. Idempotency of the whole workflow, not just the first call, is where real platform APIs fail.
- Name the consumers who retry - pipelines, controllers, and now AI agents calling platform tools. It shows you think about who uses the API.

---

[⬅ Back to Platform Architecture](./README.md) · [All topics](../README.md)
