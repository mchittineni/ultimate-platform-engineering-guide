---
title: "How do you provide observability as a platform capability?"
id: 111
category: "Platform Observability"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-observability
  - interview-questions
---

# How do you provide observability as a platform capability?

**Short answer:** Give every service its telemetry pipeline, its dashboards, its SLO rules, and its alert routing by default, generated from the service declaration - so a team gets working observability without configuring anything. The platform owns collection, transport, storage, retention, and cost control; teams own the domain-specific signals only they can know about. The measure of success is that a new service is observable on its first deploy without anyone opening a dashboard editor.

## Detail

**What "by default" has to mean.** Not a documented convention. On the first deploy a service should already have: metrics collected, logs shipped and parsed, traces sampled and correlated, a dashboard covering request rate, errors, and latency, an SLO with burn-rate alerts, alerts routed to its owning team's rotation, and cost attribution. If any of those requires a team to configure something, most teams will not have it, and the ones who do will each do it differently.

**Generate from the declaration.** The service specification already names the owner, the tier, and the SLO target. That is enough to generate the recording rules, the dashboard, the alert routing, and the retention policy. Generated observability also improves for everyone at once when you improve the template, which hand-built dashboards never do.

**Draw the ownership line clearly:**

| Platform owns                                      | Team owns                                |
| -------------------------------------------------- | ---------------------------------------- |
| Collection agents and the collector pipeline       | Domain metrics and their meaning         |
| Transport, buffering, and backpressure             | Log content and structure                |
| Storage, retention, and query backends             | Span attributes specific to their domain |
| Default dashboards and SLO rules                   | Custom dashboards beyond the defaults    |
| Alert routing and escalation plumbing              | Alert thresholds for domain conditions   |
| Cardinality limits and cost controls               | Staying within them                      |
| Instrumentation libraries and auto-instrumentation | Instrumenting business logic             |

**Standardise on OpenTelemetry for instrumentation.** A vendor-neutral API and a collector between your workloads and your backend means the backend is replaceable without touching services - which matters because observability backends are expensive and you will renegotiate or migrate eventually. This is one of the clearest cases where the abstraction is worth having.

**Correlation is what makes the three signals useful together.** A trace ID present in logs and exemplars linking metrics to traces is what lets someone move from "latency is up" to "here is a slow request" to "here is what it logged". Making that correlation automatic - injected by the platform's libraries and sidecars - delivers more practical value than any individual signal.

**Own the cost, because teams cannot see it.** Observability spend is driven by cardinality, retention, and volume, and a team adding a label with high cardinality has no visibility into the effect. The platform must set limits, attribute spend, and make the cost of a signal visible at the point someone adds it.

**Tier the retention and the sampling.** A tier-1 service's traces are worth more than a tier-3 batch job's, and uniform retention either wastes money or discards what you need. Deriving both from the declared tier is the same one-fact-drives-many-decisions pattern that makes the rest of the platform work.

**Provide the runbook link path.** An alert that fires without a link to a runbook is a page with no starting point. The generated alerts should carry the runbook URL from the catalogue entry, which also creates useful pressure to have one.

## Example

```yaml
# What a team writes. Four lines about observability, and one of them is optional.
apiVersion: platform.example.com/v1
kind: Service
metadata: { name: checkout }
spec:
  owner: group:team-payments
  tier: 1
  observability:
    slo: { availability: 99.9, latency: { threshold: 300ms, percentile: 99 } }
    # Optional: domain signals only the team can know about
    customMetrics:
      - { name: checkout_abandoned_total, type: counter, help: "Carts abandoned at payment" }
```

```text
What the platform generates from that - none of it configured by the team:

  COLLECTION
    OTel SDK auto-instrumentation injected (HTTP, gRPC, SQL, cache clients)
    collector sidecar/agent configured with the tenant's resource attributes
    log shipping with parsing, and trace_id extracted into a log field
    scrape config for the custom metric

  CORRELATION  (the part that makes the signals useful together)
    trace_id injected into every log line
    exemplars linking latency histograms to sampled traces
    resource attributes: service.name, tenant, tier, version, cluster, region

  DASHBOARDS
    RED dashboard (rate, errors, duration) with per-endpoint breakdown
    dependency view built from the declared dependsOn graph
    resource + cost panel
    "recent changes" annotations: deploys, flag flips, infra changes, policy changes

  SLO
    SLI recording rules for availability and latency from the declaration
    multi-window multi-burn-rate alerts (page on fast burn, ticket on slow)
    error budget panel and monthly report

  ROUTING
    alerts -> pagerduty:team-payments (from spec.owner, via the catalogue)
    runbook URL attached to every alert (from the catalogue annotation)

  POLICY DERIVED FROM TIER
    tier 1 -> traces: 100% of errors + 10% baseline, retained 30d
              logs retained 30d, metrics 13 months
    tier 3 -> traces: 100% of errors + 1% baseline, retained 7d
              logs retained 7d, metrics 90d
```

```text
The measure of whether this works - onboarding, not feature count:

  new service, first deploy, nothing configured by the team

  ✓ appears in the service list with an owner
  ✓ RED dashboard populated within 60s of first traffic
  ✓ traces visible and correlated with logs
  ✓ SLO recording rules active; error budget accruing
  ✓ a synthetic alert test routes to the right rotation
  ✓ cost attributed to team-payments

  Time for a team to get all of the above: 0 minutes of work.
  If any row required configuration, most services would not have it - and the
  ones that did would each have done it differently.
```

## Interview tips

- Define "by default" concretely with the list, and make the argument for why: anything requiring configuration will be missing on most services and inconsistent on the rest.
- Generating from the declaration is the mechanism, and the compounding benefit - improving the template improves every service at once - is what hand-built dashboards can never do.
- Draw the ownership line explicitly. Platform owns the pipeline and the defaults; teams own domain meaning. Vagueness here is where observability programmes stall.
- OpenTelemetry as the instrumentation standard, with the reason stated as backend replaceability, is a well-justified abstraction rather than portability for its own sake.
- Correlation - trace IDs in logs, exemplars from metrics to traces - delivers more practical value than any single signal, and saying so shows you have debugged with these tools rather than just collected them.
- Owning cost because teams cannot see it, and tiering retention and sampling from the declared tier, are the two operational points that keep this affordable.
- The zero-minutes onboarding test is the best close: it turns a vague capability into a measurable outcome.

---

[⬅ Back to Platform Observability](./README.md) · [All topics](../README.md)
