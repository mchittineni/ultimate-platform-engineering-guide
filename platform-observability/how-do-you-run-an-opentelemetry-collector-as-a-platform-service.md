---
title: "How do you run an OpenTelemetry collector as a platform service?"
id: 112
category: "Platform Observability"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-observability
  - interview-questions
---

# How do you run an OpenTelemetry collector as a platform service?

**Short answer:** Run it in two layers - a per-node agent that receives from workloads and enriches with metadata, and a gateway deployment that batches, samples, controls cardinality, and exports to backends - so the enforcement and cost controls live in one place you operate. The collector is the point where the platform can enforce limits, attribute cost, and change backends without touching a single service, which is the whole reason to run it rather than exporting directly.

## Detail

**Why a collector at all, rather than exporting directly from services.** Three reasons that matter to a platform team. It decouples services from backends, so you can change or add a backend without redeploying anything. It is where you enforce cardinality limits, sampling, and redaction centrally rather than trusting every service. And it can be upgraded by the platform through a rolling restart, escaping the per-language library upgrade treadmill.

**The two-layer topology is the standard for a reason:**

| Layer   | Deployment             | Responsibilities                                                                                         |
| ------- | ---------------------- | -------------------------------------------------------------------------------------------------------- |
| Agent   | DaemonSet, per node    | Receive from local workloads, enrich with Kubernetes metadata, add resource attributes, initial batching |
| Gateway | Deployment, autoscaled | Tail sampling, cardinality limits, redaction, cross-signal routing, export to backends                   |

Agents must be local because enrichment needs node context and because a short network path keeps workload exporters from blocking. Tail sampling must be in the gateway because deciding whether to keep a trace requires seeing all of its spans, which means all spans for a trace must reach the same gateway instance - that requirement drives the load balancing between the layers and is the detail most often missed.

**Enrich in the agent so every signal is attributable.** Tenant, service, tier, version, cluster, region, and node added as resource attributes by the platform, not by the service. That is what makes per-tenant cost attribution, per-tenant limits, and tenant-scoped queries possible at all.

**Enforce limits in the gateway.** Memory limiting so the collector sheds load rather than being killed, cardinality limits on metric label sets, span and attribute limits, and per-tenant rate limits. Without these, a single service emitting a high-cardinality label will degrade the pipeline for everyone and produce a surprising bill.

**Redact in the pipeline.** Personal data and secrets end up in span attributes and log bodies by accident. The collector is a good place to drop or hash known-sensitive attributes, because it applies to every service uniformly and does not depend on each team getting it right.

**Design the failure behaviour explicitly.** The collector must never take down a workload. That means workloads export asynchronously with a timeout and a bounded queue, agents buffer to disk within a limit, and the gateway sheds load under memory pressure rather than crashing. The failure mode you want is losing telemetry, loudly - not blocking application threads. A blocking exporter with no timeout is a genuine outage cause and is worth game-daying.

**Version and roll out like any platform component.** The collector configuration is a fleet-wide artefact; a bad processor configuration can drop all telemetry silently, which is worse than an outage because nobody notices. Stage it, watch export success rates and queue depth, and be able to roll back.

**Monitor the collector with something outside it.** If the pipeline is down, the metrics telling you it is down cannot flow through it. A small independent path for the collector's own health is necessary, and this is a specific instance of the general platform rule about circular dependencies.

**Attribute the cost.** Bytes and data points per tenant, exported as metrics, is what lets you show a team what its telemetry costs. It is also the input to any conversation about reducing it.

## Example

```yaml
# Agent: DaemonSet, per node. Enriches so every signal is attributable, then
# forwards to the gateway with load balancing that keeps a trace together.
apiVersion: opentelemetry.io/v1beta1
kind: OpenTelemetryCollector
metadata: { name: agent, namespace: observability }
spec:
  mode: daemonset
  config:
    receivers:
      otlp: { protocols: { grpc: { endpoint: 0.0.0.0:4317 }, http: {} } }
    processors:
      # Platform-added metadata - NOT the service's responsibility
      k8sattributes:
        extract:
          metadata: [k8s.namespace.name, k8s.pod.name, k8s.deployment.name, k8s.node.name]
          labels:
            - { tag_name: tenant, key: platform.example.com/tenant, from: namespace }
            - { tag_name: tier, key: platform.example.com/tier, from: pod }
      resource:
        attributes:
          - { key: cluster, value: prod-eu-1, action: upsert }
          - { key: region, value: eu-west-1, action: upsert }
      # Shed load rather than being OOMKilled
      memory_limiter: { check_interval: 1s, limit_percentage: 75, spike_limit_percentage: 20 }
      batch: { timeout: 5s, send_batch_size: 8192 }
    exporters:
      # CRITICAL: routes by trace ID so all spans of a trace reach the SAME
      # gateway instance. Tail sampling cannot work otherwise.
      loadbalancing:
        routing_key: traceID
        protocol: { otlp: { tls: { insecure: false } } }
        resolver: { k8s: { service: gateway-collector.observability } }
    service:
      pipelines:
        traces: { receivers: [otlp], processors: [k8sattributes, resource, memory_limiter, batch], exporters: [loadbalancing] }
        metrics: { receivers: [otlp], processors: [k8sattributes, resource, memory_limiter, batch], exporters: [loadbalancing] }
```

```yaml
# Gateway: where the enforcement and cost control live.
apiVersion: opentelemetry.io/v1beta1
kind: OpenTelemetryCollector
metadata: { name: gateway, namespace: observability }
spec:
  mode: deployment
  replicas: 6
  config:
    receivers:
      otlp: { protocols: { grpc: {} } }
    processors:
      memory_limiter: { check_interval: 1s, limit_percentage: 80, spike_limit_percentage: 15 }

      # Tier-aware sampling: keep everything interesting, sample the rest
      tail_sampling:
        decision_wait: 10s
        policies:
          - { name: errors, type: status_code, status_code: { status_codes: [ERROR] } }
          - { name: slow, type: latency, latency: { threshold_ms: 1000 } }
          - name: tier1-baseline
            type: and
            and:
              and_sub_policy:
                - { name: t1, type: string_attribute, string_attribute: { key: tier, values: ["1"] } }
                - { name: pct, type: probabilistic, probabilistic: { sampling_percentage: 10 } }
          - { name: default-baseline, type: probabilistic, probabilistic: { sampling_percentage: 1 } }

      # Redaction applied uniformly - does not depend on each team getting it right
      attributes/redact:
        actions:
          - { key: http.request.header.authorization, action: delete }
          - { key: user.email, action: hash }
          - { key: db.statement, action: delete }

      # Cardinality guard: drop the label sets that cause bills, loudly
      filter/cardinality:
        error_mode: ignore
        metrics:
          metric:
            - 'HasAttrKeyOnDatapoint("user_id")'
            - 'HasAttrKeyOnDatapoint("request_id")'
            - 'HasAttrKeyOnDatapoint("session_id")'

      # Per-tenant cost attribution, exported as metrics
      transform/usage:
        metric_statements:
          - context: datapoint
            statements: ['set(attributes["billing_tenant"], resource.attributes["tenant"])']
    exporters:
      otlp/metrics: { endpoint: metrics-backend:4317 }
      otlp/traces: { endpoint: traces-backend:4317 }
    service:
      telemetry:
        # The collector's own health must NOT flow through itself
        metrics: { address: 0.0.0.0:8888 } # scraped by an independent path
      pipelines:
        traces:
          receivers: [otlp]
          processors: [memory_limiter, tail_sampling, attributes/redact]
          exporters: [otlp/traces]
        metrics:
          receivers: [otlp]
          processors: [memory_limiter, filter/cardinality, transform/usage]
          exporters: [otlp/metrics]
```

```text
The failure behaviour to design and then verify:

  workload exporter        async, 5s timeout, bounded queue, drop on full
                           -> NEVER blocks an application thread
  agent unavailable        workload queues briefly then drops. Loudly:
                           otelcol_exporter_send_failed_spans alerts.
  gateway saturated        memory_limiter sheds load; agents retry with backoff
  backend unavailable      gateway queues to disk within a limit, then drops
  collector config bad     WORST CASE - telemetry silently stops. Alert on
                           export success rate and on absence of data per tenant,
                           not just on collector health.

  Game day finding worth knowing: two services used a BLOCKING exporter with no
  timeout. Killing the collector crashed them. The collector was never supposed
  to be a data-plane dependency, and for those two services it was.
```

## Interview tips

- Give the two-layer topology and justify each layer: agents local for enrichment and a short export path, gateway central for the decisions that need a global view.
- The trace-ID load balancing requirement is the detail that marks real experience - tail sampling needs all spans of a trace at one instance, and that drives the topology.
- Frame the collector as the platform's enforcement point: limits, redaction, sampling, and cost attribution in one place you operate, changeable without touching services.
- Backend replaceability is the honest reason for the abstraction, and it matters because observability contracts get renegotiated.
- The failure behaviour discussion, especially that the collector must never block an application thread, is what makes this a reliability answer as well as an observability one. The blocking-exporter finding is a strong concrete example.
- A bad collector configuration silently dropping all telemetry is worse than an outage because nobody notices - so alert on data absence per tenant, not on collector health.
- Monitoring the collector via an independent path is the circular-dependency rule applied here, and it is a good closing detail.

---

[⬅ Back to Platform Observability](./README.md) · [All topics](../README.md)
