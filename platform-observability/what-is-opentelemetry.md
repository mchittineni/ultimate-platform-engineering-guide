---
title: "What is OpenTelemetry?"
id: 213
category: "Platform Observability"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-observability
  - interview-questions
---

# What is OpenTelemetry?

**Short answer:** OpenTelemetry (OTel) is a vendor-neutral, open-source standard for producing and moving telemetry - traces, metrics, logs, and now profiles. It defines an API that code instruments against, SDKs that implement it in each language, a wire protocol (OTLP), naming rules called semantic conventions, and a Collector that receives, processes, and exports data. It is a CNCF project and the default instrumentation choice today, because it separates how telemetry is produced from where it is stored.

## Detail

**The problem it solves.** Before OpenTelemetry, instrumenting a service meant using a vendor's agent or library. Changing backend meant re-instrumenting every service, and two libraries in the same process often disagreed on how to propagate trace context. OpenTelemetry was formed in 2019 by merging OpenTracing and OpenCensus, and it has since become the common layer that almost every observability vendor and open-source backend accepts.

**The parts, and what each one does:**

| Component            | What it is                                                     | Who uses it                     |
| -------------------- | -------------------------------------------------------------- | ------------------------------- |
| API                  | Interfaces for creating spans, metrics, and logs               | Application and library authors |
| SDK                  | The per-language implementation: sampling, batching, exporting | Configured by the platform      |
| Instrumentation      | Ready-made libraries and agents for HTTP, gRPC, databases      | Injected automatically          |
| OTLP                 | The wire protocol, over gRPC (port 4317) or HTTP (port 4318)   | Everything that sends telemetry |
| Semantic conventions | Standard attribute names such as `http.route`, `service.name`  | Anyone querying the data        |
| Collector            | A pipeline of receivers, processors, and exporters             | Operated by the platform team   |
| Kubernetes Operator  | Manages Collectors and injects auto-instrumentation into pods  | Operated by the platform team   |

**API and SDK are deliberately separate.** A library such as an HTTP client can depend on the API alone. If the application never installs an SDK, the API calls do nothing and cost almost nothing. When the platform installs and configures the SDK, the same calls start producing data. This is what lets open-source libraries ship with built-in instrumentation without forcing a telemetry backend on anyone.

**Zero-code instrumentation is how most services start.** For Java, .NET, Python, and Node.js, an agent can instrument common frameworks and clients at startup without code changes. For compiled languages and processes you cannot modify, OpenTelemetry eBPF Instrumentation (OBI, donated from Grafana Beyla) observes network protocols from the kernel. Teams then add manual spans and metrics only for business logic the automatic layer cannot understand.

**Semantic conventions are what make data from different teams comparable.** If one service records `http.status` and another `status_code`, no dashboard can span both. The conventions fix the names - `http.request.method`, `http.response.status_code`, `db.system.name`, `service.name` - so queries, dashboards, and alerts work across the whole estate. Several convention groups, including HTTP, are stable; others are still evolving, and renames do happen, so a platform should pin a convention version and plan migrations.

**The Collector is the platform's control point.** Services send OTLP to a Collector, which can add Kubernetes metadata, drop sensitive attributes, sample traces, limit cardinality, and export to one or more backends. Because configuration lives in the Collector rather than in every service, the platform can change backend or policy with a rolling restart instead of a fleet-wide redeploy.

**Signal maturity differs.** Traces, metrics, and logs are stable in the specification and in the major language SDKs. Profiles are the newest signal and entered public alpha in 2026; useful for evaluation, not yet a production default. Individual Collector components also carry their own stability levels, so check before relying on one.

**What it is not.** OpenTelemetry does not store or visualise data. You still need backends - Prometheus or another metrics store, a tracing backend such as Jaeger or Tempo, a log store, or a commercial product that accepts OTLP. It standardises everything up to the point of storage.

**The trade-offs.** The project is large and moves quickly, so configuration keys and attribute names change between releases, and upgrades need managing. Auto-instrumentation adds some startup time and runtime overhead that should be measured. And vendor-neutral does not mean feature-identical: some backends offer extras through their own agents. For a platform, those costs are usually outweighed by instrumenting once and keeping the backend replaceable.

**Why the platform owns it.** Product engineers, the platform's users, should get working telemetry on their first deploy without learning OTel's configuration surface. The platform picks the SDK versions, injects instrumentation, sets the exporter endpoint and resource attributes, and runs the Collectors. The team's job shrinks to adding domain signals.

## Example

```bash
# Standard SDK environment variables - the same names in every language.
# In a platform these are injected by the Operator, not set by teams.
export OTEL_SERVICE_NAME=checkout
export OTEL_RESOURCE_ATTRIBUTES="service.version=1.4.3,deployment.environment.name=production"
export OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-agent.observability:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_TRACES_SAMPLER=parentbased_traceidratio
export OTEL_TRACES_SAMPLER_ARG=0.1

# Zero-code instrumentation for a Python service
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install   # installs instrumentations for detected libraries
opentelemetry-instrument python app.py
```

```yaml
# A minimal Collector: receive OTLP, add Kubernetes metadata, export to a backend.
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }
processors:
  memory_limiter: { check_interval: 1s, limit_percentage: 80, spike_limit_percentage: 20 }
  k8sattributes: {}
  batch: {}
exporters:
  otlp:
    endpoint: tracing-backend.observability:4317
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, k8sattributes, batch]
      exporters: [otlp]
```

## Interview tips

- Name the parts - API, SDK, instrumentation, OTLP, semantic conventions, Collector - and say what each is for. Most candidates only mention the SDK.
- Give the reason it matters: instrument once and keep the backend replaceable. That is the answer to "why not just use the vendor's agent?".
- Explain the API/SDK split; it is why libraries can ship with instrumentation built in at almost no cost.
- Be accurate on maturity: traces, metrics, and logs are stable; profiles are in alpha; Collector components each have their own stability level.
- Say clearly that OpenTelemetry does not store data. Confusing it with a backend is a common slip.
- Close on the platform angle: the platform operates the Collector and injects instrumentation so product teams get telemetry without configuring it. For the operational detail, see [How do you run an OpenTelemetry collector as a platform service?](./how-do-you-run-an-opentelemetry-collector-as-a-platform-service.md).

---

[⬅ Back to Platform Observability](./README.md) · [All topics](../README.md)
