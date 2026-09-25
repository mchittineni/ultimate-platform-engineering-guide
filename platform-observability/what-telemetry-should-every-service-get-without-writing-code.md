---
title: "What telemetry should every service get without writing code?"
id: 217
category: "Platform Observability"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-observability
  - interview-questions
---

# What telemetry should every service get without writing code?

**Short answer:** The golden signals for inbound and outbound traffic, runtime and resource metrics, structured logs with a trace ID, distributed traces across every network hop, and the platform-level context that makes them attributable - service, tenant, tier, version, cluster. All of that is obtainable through auto-instrumentation, sidecars, and platform-injected metadata, so a team should have to write instrumentation only for its own domain logic.

## Detail

**The baseline set, and how each is obtained without application changes:**

| Telemetry                                   | Mechanism                                       |
| ------------------------------------------- | ----------------------------------------------- |
| Request rate, error rate, latency (inbound) | Auto-instrumentation or mesh sidecar            |
| Same for outbound calls                     | Auto-instrumentation of HTTP, gRPC, SQL clients |
| Runtime metrics (heap, GC, threads, pools)  | Language runtime instrumentation                |
| Container resource usage                    | Kubelet and node exporter                       |
| Structured logs with trace ID               | Log shipper plus context injection              |
| Distributed traces with propagation         | Auto-instrumentation plus mesh                  |
| Deployment and version annotations          | Platform injects `service.version`              |
| Ownership and tenancy attributes            | Collector enrichment from Kubernetes metadata   |
| Change events (deploys, flags, infra)       | Platform change feed, annotated onto dashboards |

**Auto-instrumentation covers more than people expect.** Injecting a language agent - via an operator or an init container - instruments the HTTP server, HTTP and gRPC clients, database drivers, and cache clients. That yields inbound and outbound golden signals plus trace propagation with no code change, which is the large majority of what an on-call engineer needs.

**eBPF instrumentation reaches what an agent cannot.** OpenTelemetry eBPF Instrumentation (OBI, donated from Grafana Beyla) runs as a node-level DaemonSet and observes HTTP, gRPC, and common database protocols at the kernel boundary, producing RED metrics and spans for any process - including compiled languages with no injectable agent and third-party binaries you cannot change. It sees less than an in-process agent (no runtime internals, limited business context) and was still pre-1.0 in 2026, so treat it as a floor for everything rather than a replacement for SDK instrumentation where you have it.

**A mesh gives you the same signals from the network side, uniformly.** Where a mesh is already present it produces consistent request metrics for every service regardless of language, which is particularly valuable in a polyglot estate. Auto-instrumentation and a mesh overlap; the mesh sees the network, the agent sees inside the process. Runtime metrics and database client spans come only from the agent.

**Outbound is as important as inbound and is frequently missed.** Most latency problems are a dependency being slow, and without client-side spans and metrics you can see that your service is slow but not why. Auto-instrumented database and HTTP client calls are often the highest-value signal in the whole set.

**Trace context propagation is the piece that most often breaks.** Auto-instrumentation propagates across instrumented libraries, but a custom transport, a message queue, or a thread pool can drop the context - producing traces that stop at a boundary. This is worth testing explicitly as a platform capability rather than assuming, because a broken trace is much less useful than an absent one is honest.

**Platform context is what makes the telemetry usable.** Service name, version, tenant, tier, cluster, and region as resource attributes, injected by the collector rather than configured per service. Without them you cannot filter by tenant, attribute cost, or answer "which version started failing".

**Change annotations are the highest-value cheap addition.** Overlaying deploys, flag flips, infrastructure changes, and policy changes onto every dashboard answers the first question of nearly every incident - what changed - and requires no per-service work at all.

**Be honest about what auto-instrumentation cannot give you.** Business meaning: whether a checkout succeeded in the domain sense, why a request was rejected, which of your own code paths was taken. That is the team's job, and the platform's role is to make adding a domain metric or a span attribute trivial once the baseline exists.

**Watch the overhead, and measure it.** Agents add startup time and some runtime cost, and a mesh sidecar adds latency and resources. Both are usually acceptable and both should be measured rather than assumed, particularly for latency-sensitive services which may want a lighter configuration.

## Example

```yaml
# Auto-instrumentation injected by annotation. No application code changes.
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata: { name: platform-default, namespace: observability }
spec:
  # Java agent 2.x and most SDKs default to OTLP over HTTP/protobuf, so port 4318
  exporter: { endpoint: http://agent-collector.observability:4318 }
  propagators: [tracecontext, baggage] # W3C - the interoperable choice
  sampler: { type: parentbased_traceidratio, argument: "0.1" }
  resource:
    # Platform context - injected, never configured per service
    resourceAttributes:
      deployment.environment.name: production # renamed from deployment.environment
  java:
    env:
      - { name: OTEL_INSTRUMENTATION_JDBC_ENABLED, value: "true" } # outbound SQL
      - { name: OTEL_INSTRUMENTATION_JAVA_HTTP_CLIENT_ENABLED, value: "true" } # outbound HTTP
      - { name: OTEL_INSTRUMENTATION_RUNTIME_TELEMETRY_ENABLED, value: "true" } # heap, GC
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: checkout, namespace: team-payments }
spec:
  template:
    metadata:
      annotations:
        # This one line is the entire integration. The platform adds it from the
        # service declaration's language field - the team writes nothing.
        instrumentation.opentelemetry.io/inject-java: "observability/platform-default"
      labels:
        app: checkout
        platform.example.com/version: "1.4.2" # -> service.version
        platform.example.com/tier: "1"
```

```text
What an on-call engineer can answer with the baseline alone - no team
instrumentation involved:

  "is checkout erroring?"              inbound error rate by endpoint      ✓
  "is it slow?"                        inbound latency p50/p95/p99          ✓
  "is it slow because of a dependency?" OUTBOUND latency per dependency     ✓
                                        (the most valuable signal, and the
                                         one most often missing)
  "which dependency?"                   client spans: pricing 8ms,
                                        postgres 1,840ms  <-- there it is
  "what did the slow query do?"         db.query.text on the span           ✓
  "did something change?"               change annotations on the dashboard:
                                        deploy 1.4.2 at 09:14, flag flip at
                                        13:47                               ✓
  "is it one version or all of them?"   filter by service.version           ✓
  "is it one tenant?"                   filter by tenant attribute          ✓
  "show me a slow request end to end"   trace from an exemplar              ✓

  "did the customer's payment actually succeed in business terms?"          ✗
  -> that is domain knowledge. The team must instrument it, and the platform's
     job is to make adding one metric or span attribute trivial.
```

```text
The two things to verify rather than assume:

  1. TRACE CONTEXT PROPAGATION - test it as a platform capability
     $ platform trace verify --service checkout
       inbound HTTP ................. context received     ✓
       outbound HTTP to pricing ...... context propagated   ✓
       outbound SQL .................. span emitted         ✓
       publish to orders queue ....... context propagated   ✗  BROKEN
         -> the queue client is not auto-instrumented; traces stop at the
            producer and the consumer starts a new trace. A broken trace is
            worse than an absent one, because it looks complete.
       async thread pool ............. context propagated   ✗  BROKEN
         -> executor not wrapped; spans lose their parent

  2. OVERHEAD - measure, do not assume
     agent injected:   startup +1.9s, p99 latency +3ms, memory +45Mi
     mesh sidecar:     p99 latency +2ms, 0.1 CPU, 60Mi per pod
     -> acceptable for almost everything; for one latency-critical service a
        lighter sampling configuration was used, recorded as an exception.
```

## Interview tips

- Give the baseline as a table of telemetry paired with the mechanism that provides it. That structure shows you know how each item is actually obtained rather than just that it is desirable.
- Outbound signals are the point most candidates miss, and they are the most valuable: your service being slow is visible, why it is slow requires client-side spans.
- Trace context propagation breaking at queues and thread pools is the specific, real failure. "A broken trace is worse than an absent one" is a good line.
- Platform-injected resource attributes - tenant, tier, version, cluster - are what make the telemetry filterable and attributable, and they should never be per-service configuration.
- Change annotations on every dashboard are cheap and answer the first question of nearly every incident. Volunteering this is a strong practical signal.
- Distinguish auto-instrumentation from the mesh and from eBPF: the mesh and eBPF see the network and syscalls for any process, the agent sees inside the process, and only the agent gives you runtime detail.
- Be honest that business meaning cannot be auto-instrumented, and say the platform's job is to make adding it trivial. And measure overhead rather than asserting it is negligible.

---

[⬅ Back to Platform Observability](./README.md) · [All topics](../README.md)
