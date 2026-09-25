---
title: "How do you use events to integrate platform components?"
id: 35
category: "Platform Architecture"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-architecture
  - interview-questions
---

# How do you use events to integrate platform components?

**Short answer:** Have each component publish facts about what happened - "image built", "deployment succeeded", "database provisioned" - to a broker in a shared envelope such as CloudEvents, and let other components subscribe instead of calling each other directly. That decouples the producer from every consumer, so adding a new integration (a scorecard, a cost record, a Slack notification) no longer means changing the CI system. The price is that you must design for at-least-once delivery, out-of-order arrival, schema evolution, and debugging a flow nobody can see in one call stack.

## Detail

**The problem events solve.** A platform is a dozen systems - CI, registry, GitOps reconciler, catalogue, provisioning controllers, incident tooling, cost reporting - that all want to know what the others did. Wiring them with direct calls produces a mesh where the CI pipeline has to know about the catalogue, the scorecard service, and the change log, and a new consumer means editing the producer. Events invert this: the producer announces a fact once, and any number of consumers react, owned by different teams, added without coordination.

**Events are facts, not commands.** `deployment.succeeded` states something that happened; `please.update.catalogue` is a command dressed as an event and recreates the coupling you were trying to remove. Name events in the past tense, put enough data in them for most consumers to act without calling back, and let consumers decide what to do.

**Use a standard envelope.** CloudEvents (a CNCF graduated project) defines the common attributes - `id`, `source`, `type`, `specversion`, `time`, `subject` - and bindings for HTTP, Kafka, NATS, and others. That lets any router filter on `type` without understanding the payload. For delivery pipelines specifically, the CD Foundation's CDEvents specification builds on CloudEvents with a shared vocabulary for builds, artefacts, and deployments, so tools from different vendors can interoperate.

**The transport depends on the need.**

| Need                                   | Typical choice                                |
| -------------------------------------- | --------------------------------------------- |
| Durable log, replay, high volume       | Kafka, or a managed equivalent                |
| Lightweight pub/sub, simple fan-out    | NATS, cloud pub/sub (SNS/SQS, Pub/Sub)        |
| Kubernetes-native routing and triggers | Knative Eventing, Argo Events                 |
| Reacting to Kubernetes object changes  | The API server's watch - it is already events |
| Cloud control-plane changes            | EventBridge, Event Grid, Eventarc             |

Inside a cluster, remember that controllers already integrate through events of a kind: they watch objects and reconcile. You do not need a broker for a controller to react to a custom resource - a broker is for crossing system boundaries.

**The four properties you must design for.**

- **At-least-once delivery.** Brokers redeliver on timeout, so every consumer must be idempotent - typically by recording processed event `id`s or by making the effect an upsert.
- **Ordering is not guaranteed across partitions.** `deployment.succeeded` for version 1.4.3 can arrive before 1.4.2's. Carry a version or timestamp and discard stale events, or partition by the entity (`subject`) so per-entity order is preserved.
- **Schema evolution.** Events are an API with unknown consumers. Add fields, never repurpose them, version the `type` (`...deployment.succeeded.v2`) for breaking changes, and keep a schema registry or at least published JSON Schemas.
- **Publishing reliably.** If the CI system writes to its database and then publishes, a crash in between loses the event. The transactional outbox pattern - write the event to an outbox table in the same transaction, relay it afterwards - closes that gap.

**Who benefits.** Platform engineers get integrations that can be added and removed without touching core systems. Application developers get a platform where their deployment automatically appears in the catalogue, the change log, and the incident timeline - without a manual step - and they can subscribe their own automation to the same stream.

**When not to use events.** If the caller needs an answer to proceed - "is this image allowed?" - that is a synchronous request, not an event. Events also make flows harder to follow: nobody can see the whole chain from one log. Propagate a trace context (CloudEvents has a distributed tracing extension) and keep a catalogue of event types with their producers and consumers, or you will be debugging by guesswork. And if two components always change together, an event bus between them is ceremony.

## Example

```json
{
  "specversion": "1.0",
  "id": "8d6f2c1e-4b7a-4f3e-9a51-2c0e7d3b9f14",
  "source": "/platform/argocd/prod-eu-1",
  "type": "com.example.platform.deployment.succeeded.v1",
  "subject": "service/checkout",
  "time": "2026-09-24T14:32:08Z",
  "datacontenttype": "application/json",
  "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
  "data": {
    "service": "checkout",
    "owner": "group:team-payments",
    "environment": "production",
    "version": "1.4.2",
    "image": "ghcr.io/example/checkout@sha256:9b2c...e41a",
    "commit": "a41f9c2",
    "revision": 1187
  }
}
```

```text
One fact, four independent consumers. The GitOps reconciler knows about none
of them.

  deployment.succeeded.v1
    |
    +--> catalogue updater      sets "current version" on the service page
    |                           idempotent: upsert keyed on (service, env)
    |                           stale check: ignore if revision < stored revision
    +--> change log             appends a row for the incident timeline
    |                           idempotent: unique constraint on event id
    +--> DORA metrics           computes lead time from commit to deploy
    +--> team's own automation  subscribed by team-payments to run smoke tests

  Adding a fifth consumer (cost attribution, next quarter) is a new
  subscription. Nobody edits the reconciler or its notification config.
```

## Interview tips

- Lead with decoupling: producers publish facts, consumers subscribe, and new integrations stop requiring producer changes. That is the architectural reason to use events.
- Say "facts, not commands" and name events in the past tense. It is a small point that signals you have seen command-shaped events recreate coupling.
- Cover the four hard properties - at-least-once, ordering, schema evolution, reliable publishing with an outbox. Missing idempotent consumers is the most common gap in candidates' answers.
- Mention CloudEvents as the envelope and CDEvents for delivery pipelines; it shows you would not invent a format.
- Be ready for "when would you not use events?" - when the caller needs an answer, or when the observability cost of an invisible chain outweighs the decoupling.

---

[⬅ Back to Platform Architecture](./README.md) · [All topics](../README.md)
