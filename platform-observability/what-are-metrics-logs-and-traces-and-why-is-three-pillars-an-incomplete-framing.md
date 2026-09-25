---
title: What are metrics, logs, and traces, and why is "three pillars" an incomplete framing?
id: 212
category: "Platform Observability"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-observability
  - interview-questions
---

# What are metrics, logs, and traces, and why is "three pillars" an incomplete framing?

**Short answer:** Metrics are numeric measurements aggregated over time, logs are timestamped records of individual events, and traces record the path of one request across services as a tree of timed spans. "Three pillars" is incomplete because it presents them as three separate stores to be collected, when the value comes from correlating them - and because it leaves out other signals, notably profiles, and the shared context that links everything together.

## Detail

**Metrics: cheap, aggregated, good for "how much" and "how often".** A metric is a number with a name, a timestamp, and a small set of labels - request count, latency histogram, queue depth, memory in use. Because they are aggregated, metrics are cheap to store and fast to query over long periods, which makes them ideal for dashboards, SLOs, and alerts. The cost of that efficiency is detail: a latency histogram tells you the p99 went up, not which request was slow or why. Labels must also stay bounded, because every unique combination is a separate time series.

**Logs: detailed, per event, good for "what exactly happened".** A log line records one event - an error, a state change, a decision. Logs can carry arbitrary detail, which makes them the richest signal and usually the most expensive. Unstructured text is hard to query at scale, which is why platforms push structured logs with consistent fields. On their own, logs from different services describing the same request are hard to join.

**Traces: causal, per request, good for "where did the time go".** A trace follows one request through the system. Each unit of work is a span with a start time, a duration, attributes, and a parent, so the trace forms a tree showing which service called which and how long each step took. Traces are what make distributed systems debuggable, because they show causality across process boundaries. They are usually sampled, because keeping every span for every request is expensive.

| Signal   | Unit                    | Best for                                   | Main limitation                       |
| -------- | ----------------------- | ------------------------------------------ | ------------------------------------- |
| Metrics  | Aggregated number       | Trends, alerting, SLOs, capacity           | No per-request detail; bounded labels |
| Logs     | Individual event        | Detail of what happened and why            | Volume and cost; hard to join         |
| Traces   | Request as span tree    | Latency breakdown, cross-service causality | Sampling means not every request      |
| Profiles | Stack samples over time | Which code is burning CPU or memory        | Newer; tooling still maturing         |

**Why "three pillars" misleads.** Pillars stand apart, and that is exactly how many organisations ended up building observability: a metrics tool, a logging tool, and a tracing tool, bought separately, with different query languages and no way to move between them. During an incident the engineer then copies timestamps between three browser tabs and guesses. The pillars framing counts the data types and misses what makes them useful.

**What matters is correlation and shared context.** The useful version looks like this: an alert fires on a metric; the metric carries an exemplar pointing at a trace ID; the trace shows the slow span; the logs for that span are found by the same trace ID; and a profile for that service and time window shows the hot function. That journey works only when every signal carries the same identifying context - `service.name`, `service.version`, deployment environment, and trace and span IDs. OpenTelemetry's resource attributes and context propagation exist precisely to make that shared context consistent.

**It also leaves out signals.** Continuous profiling is now recognised as a fourth OpenTelemetry signal, entering public alpha in 2026. Other useful inputs - change events such as deploys and flag flips, real-user monitoring from browsers, and Kubernetes events - do not fit neatly into three pillars either, yet "what changed?" is the first question of most incidents.

**Some argue the pillars are really one thing.** A popular view is that the underlying unit is the wide structured event - one record per unit of work with many attributes - and metrics, logs, and traces are views derived from it. You do not need to adopt that view fully, but it is a useful corrective: the signals are different shapes of the same underlying facts, not three independent systems.

**Why the platform cares.** Correlation cannot be added by one team in isolation. It depends on every service propagating trace context, emitting the same resource attributes, and writing the trace ID into its logs. That consistency is a platform capability: the platform injects instrumentation and enrichment so that product engineers get connected signals by default, rather than three disconnected piles of data.

## Example

```text
One request, four signals, one shared context.

  shared context on every signal:
    service.name=checkout  service.version=1.4.3  deployment.environment.name=prod
    trace_id=4bf92f3577b34da6a3ce929d0e0e4736

  METRIC   http_server_request_duration_seconds{route="/pay"} p99 = 2.8s
           exemplar -> trace_id=4bf92f35...
  TRACE    checkout /pay 2.81s
             pricing.quote            12ms
             postgres SELECT orders 2.71s   <-- the slow step
  LOG      {"level":"warn","msg":"slow query","db.query.summary":"SELECT orders",
            "duration_ms":2710,"trace_id":"4bf92f35...","span_id":"00f067aa0ba902b7"}
  PROFILE  checkout, 14:02-14:03: 38% CPU in json.Marshal of the order history

  Pillars view: four tools, four queries, timestamps copied by hand.
  Correlated view: click from the metric to the trace to the log to the profile.
```

```json
{
  "timestamp": "2026-09-25T14:02:17.412Z",
  "severity_text": "WARN",
  "body": "slow query",
  "attributes": { "db.system.name": "postgresql", "duration_ms": 2710 },
  "resource": { "service.name": "checkout", "service.version": "1.4.3" },
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7"
}
```

## Interview tips

- Define each signal by its unit and what question it answers best - metrics for how much, logs for what happened, traces for where the time went - and give one limitation each.
- The critique is the point of the question: pillars suggest three separate systems, but the value is in correlation through shared context and trace IDs.
- Mention exemplars as the concrete link from a metric to a trace, and trace IDs in logs as the link from a trace to its logs.
- Bring up profiles as the fourth OpenTelemetry signal and change events as a missing input; it shows you are current.
- Frame correlation as a platform responsibility, because it only works when every service emits the same context - which is exactly what a platform can make the default.
- If asked for further reading, the monitoring-versus-observability distinction is a natural companion: [What is the difference between monitoring and observability?](./what-is-the-difference-between-monitoring-and-observability.md).

---

[⬅ Back to Platform Observability](./README.md) · [All topics](../README.md)
