---
title: "What is the difference between monitoring and observability?"
id: 211
category: "Platform Observability"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-observability
  - interview-questions
---

# What is the difference between monitoring and observability?

**Short answer:** Monitoring is watching for conditions you decided in advance were important - a dashboard of known metrics and alerts on known thresholds. Observability is a property of a system: how well you can work out what is happening inside it from the telemetry it emits, including for questions nobody thought to ask beforehand. Monitoring answers "is the thing I expected to go wrong going wrong?"; observability answers "why is this behaving strangely?" - and a platform needs both.

## Detail

**Monitoring is built on known failure modes.** Someone decides that CPU above 90%, error rate above 1%, or disk above 85% matters, writes a check, and puts it on a dashboard or behind an alert. This works well for problems you have seen before or can predict. It is cheap, it is easy to reason about, and it is what should wake someone up at night. Its limit is built in: a check can only detect what its author imagined.

**Observability is about the unknown unknowns.** The term comes from control theory, where a system is observable if its internal state can be inferred from its outputs. In software it means your telemetry is rich enough - high-cardinality attributes, request-level detail, correlation between signals - that you can ask a new question during an incident without shipping new code first. "Why are only Android users in one region seeing slow checkouts since 14:00?" is not something anyone built a dashboard for, but with traces carrying the device, region, and version attributes it is a query, not a redeploy.

**The practical difference is the questions you can ask after the fact:**

| Aspect             | Monitoring                             | Observability                                     |
| ------------------ | -------------------------------------- | ------------------------------------------------- |
| Starting point     | A question decided in advance          | A question that arose during the incident         |
| Typical data       | Aggregated metrics, health checks      | Traces, structured events, metrics with exemplars |
| Cardinality        | Deliberately low                       | High where it helps (per request, per tenant)     |
| Output             | Dashboards and alerts                  | Exploratory queries and drill-down                |
| Failure it catches | Known failure modes                    | Novel failure modes, emergent behaviour           |
| Main risk          | Silence on anything nobody anticipated | Cost and noise if collected without limits        |

**They are not competitors.** Monitoring tells you something is wrong; observability helps you find out why. An alert on a burning error budget is monitoring, and it should still exist in a highly observable system. What changes with observability is what happens after the page: instead of guessing from a wall of graphs, the on-call engineer clicks from the alert to an exemplar trace to the logs of that exact request.

**Why distributed systems forced the change.** In a monolith on three servers, a handful of host metrics and a log file told you most of what you needed. In a system of two hundred services, where one user request crosses fifteen of them and the failure is an interaction between a retry policy and a slow dependency, host metrics look fine while users suffer. The failure modes multiplied faster than anyone could write checks for them.

**Why this is a platform concern.** Observability is only as good as the least-instrumented service in the request path. If each team chooses its own libraries, attribute names, and sampling, a trace breaks at the first team that did something different. The platform's job is to make the observable path the default: instrumentation injected automatically, consistent attributes such as service, version, tenant, and owning team added centrally, and correlation between signals wired up so that the product engineers - the users of the platform - can ask new questions without first becoming telemetry experts.

**The trade-off is cost.** Observability data is richer and therefore larger. High-cardinality attributes, request-level traces, and verbose logs can easily cost more than the workloads they describe. A mature platform keeps monitoring cheap and focused, and spends its observability budget where it earns its keep: tail-sampled traces that keep every error, bounded metric labels, and shorter retention for lower-tier services.

## Example

```text
The same incident, handled with monitoring only and then with observability.

  ALERT  checkout error-budget burn rate 14x over 1h   (monitoring: known condition)

  MONITORING ONLY
    dashboards: CPU normal, memory normal, pod restarts 0, error rate 2.1%
    -> "something is failing, nothing obvious is wrong"
    -> add logging, redeploy, wait for it to happen again         45+ minutes

  WITH OBSERVABILITY
    1. click the exemplar on the error-rate panel -> a failing trace
    2. trace shows: checkout -> pricing -> currency-api, 30s timeout
    3. group failing traces by attribute:
         app.version     = 1.4.3     100% of failures   (deployed 13:58)
         cloud.region    = eu-west-1 100% of failures
         currency.code   = CHF       100% of failures
    4. the new version calls a currency endpoint only served in us-east-1
                                                                   6 minutes

  Nobody built a dashboard for "failures by currency code". The attribute was
  on the span, so the question could be asked when it mattered.
```

```promql
# Monitoring: a question decided in advance, cheap and reliable.
sum(rate(http_server_request_duration_seconds_count{service_name="checkout", http_response_status_code=~"5.."}[5m]))
  /
sum(rate(http_server_request_duration_seconds_count{service_name="checkout"}[5m]))
  > 0.01
```

## Interview tips

- Lead with the one-line distinction: monitoring answers questions decided in advance, observability lets you answer new ones from existing telemetry. Then say you need both.
- Avoid saying observability "replaces" monitoring. Alerts on known symptoms are still how people get paged; observability is what makes the investigation fast.
- Mention that the term comes from control theory - inferring internal state from outputs - which shows you know it is a property of the system, not a product category.
- Tie it to the platform: consistent instrumentation and attributes across teams are what make a system observable end to end, and one uninstrumented hop breaks it.
- Expect the follow-up "isn't it just metrics, logs, and traces?" - the honest answer is that signals are inputs, and observability depends on correlation and context between them. See [What are metrics, logs, and traces, and why is "three pillars" an incomplete framing?](./what-are-metrics-logs-and-traces-and-why-is-three-pillars-an-incomplete-framing.md).
- Name the cost trade-off unprompted. Richer telemetry is more expensive, and controlling that is part of the job.

---

[⬅ Back to Platform Observability](./README.md) · [All topics](../README.md)
