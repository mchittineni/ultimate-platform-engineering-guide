---
title: "How do you control metric cardinality and observability cost?"
id: 221
category: "Platform Observability"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-observability
  - interview-questions
---

# How do you control metric cardinality and observability cost?

**Short answer:** Cardinality is the product of every label's distinct values, so one unbounded label multiplies your time series count by its cardinality - and observability cost is driven far more by that multiplication than by request volume. Control it by forbidding unbounded labels at the collection point, enforcing limits per tenant, tiering retention and sampling, and attributing spend so teams can see what their telemetry costs.

## Detail

**Understand the multiplication, because it explains everything else.** A metric with labels for method (5 values), endpoint (40), and status (8) produces 1,600 series. Add `user_id` with a million values and it becomes 1.6 billion. The offending change is one line adding a label, made by someone with no visibility into the effect, and the consequence is a storage and query cost increase of several orders of magnitude plus a query performance collapse.

**The unbounded labels to forbid outright:** user or customer identifiers, request or trace identifiers, session identifiers, full URL paths with embedded identifiers, email addresses, IP addresses, timestamps, and error messages. Each is unbounded by nature. They belong in traces and logs, where high cardinality is the point and the storage model is designed for it - the signal choice is the fix, not a smaller label.

**Enforce at the collection point, not in review.** A processor that drops metrics carrying forbidden label keys, plus a per-tenant series limit, means a bad label cannot reach storage regardless of who wrote it. Code review will not catch this reliably, and by the time a dashboard is slow the bill has already changed.

**Give teams the signal-choice guidance explicitly**, because most cardinality mistakes are someone reaching for the wrong signal:

| Want to know                           | Right signal                                          |
| -------------------------------------- | ----------------------------------------------------- |
| How often, how slow, how many errors   | Metrics with bounded labels                           |
| What happened in this specific request | A trace                                               |
| Details of one event                   | A log line with the trace ID                          |
| Behaviour per customer                 | Traces or logs, or a metric on a bounded segment tier |
| Which endpoint is slow                 | Metrics on a normalised route, not the raw path       |

Route normalisation - `/orders/{id}` rather than `/orders/12345` - is the single most valuable specific practice, and it is usually a one-line instrumentation fix.

**Tier retention and sampling from the declared service tier.** Thirteen months of tier-1 metrics is reasonable; the same for a tier-3 batch job is waste. Traces should keep all errors and slow requests and sample the rest, with the baseline rate varying by tier. Deriving both from the tier field means teams get sensible defaults without deciding.

**Sample traces intelligently rather than uniformly.** Keeping 1% of everything discards the errors you needed; keeping 100% of errors and slow requests plus a small baseline gives you the interesting traces at a fraction of the volume. Tail sampling is what enables this, because the decision needs the whole trace.

**Logs are usually the largest line and the least examined.** Debug logging left enabled in production, stack traces on expected errors, and per-request logs at high volume dominate many bills. Structured logs at appropriate levels, with the trace ID for correlation, plus a shorter retention for lower tiers, is where the reduction usually is.

**Attribute cost per team and publish it.** Teams cannot manage what they cannot see, and a team discovering that its telemetry costs more than its compute changes behaviour immediately without any policy. Attribution is also what lets you refuse a request to raise a limit without it being a judgement call.

**Alert on cardinality growth, not just on cost.** A sudden increase in series count for one metric is the leading indicator; the bill is the lagging one. Catching it within an hour is a configuration change, catching it in the monthly invoice is an incident review.

## Example

```text
The multiplication that causes the incident:

  http_requests_total{method, route, status}
    5 methods x 40 routes x 8 statuses ........................ 1,600 series

  someone adds one label to help with debugging:
  http_requests_total{method, route, status, user_id}
    1,600 x ~1,000,000 users .................. up to 1,600,000,000 series

  One line of code. Storage and query cost up by orders of magnitude, dashboards
  time out, and the metrics backend becomes the largest line in the platform bill.
  The person who wrote it had no way to see any of that.

  The fix is not a smaller label - it is the RIGHT SIGNAL:
    "which users are affected?"  -> a trace or a log, queried by user_id
    "how many requests failed?"  -> the metric, without user_id
```

```yaml
# Enforce at collection, because review will not catch it reliably.
processors:
  # 1. Forbidden label keys - dropped before they reach storage
  filter/forbidden_labels:
    error_mode: ignore
    metrics:
      metric:
        - 'HasAttrKeyOnDatapoint("user_id")'
        - 'HasAttrKeyOnDatapoint("customer_id")'
        - 'HasAttrKeyOnDatapoint("request_id")'
        - 'HasAttrKeyOnDatapoint("trace_id")'
        - 'HasAttrKeyOnDatapoint("session_id")'
        - 'HasAttrKeyOnDatapoint("email")'
        - 'HasAttrKeyOnDatapoint("ip")'

  # 2. Route normalisation - the single highest-value practice
  transform/normalise_routes:
    metric_statements:
      - context: datapoint
        statements:
          - 'replace_pattern(attributes["http.route"], "/[0-9]+", "/{id}")'
          - 'replace_pattern(attributes["http.route"], "/[0-9a-f]{8}-[0-9a-f-]+", "/{uuid}")'

  # 3. Per-tenant series limit - a noisy tenant cannot degrade everyone
  #    (enforced in the gateway; exceeding it drops and alerts, loudly)
  #    plus tier-aware tail sampling: keep everything interesting
  tail_sampling:
    decision_wait: 10s
    policies:
      - { name: all-errors, type: status_code, status_code: { status_codes: [ERROR] } }
      - { name: all-slow, type: latency, latency: { threshold_ms: 1000 } }
      - { name: tier1-baseline, type: probabilistic, probabilistic: { sampling_percentage: 10 } }
      - { name: default, type: probabilistic, probabilistic: { sampling_percentage: 1 } }
```

```text
Cost attribution, published monthly - the report that changes behaviour:

  $ platform observability cost --by team --month 2026-07

  TEAM             METRICS   LOGS     TRACES   TOTAL    SERIES     NOTE
  team-payments    $2,100   $3,400   $1,200   $6,700   410k
  team-search      $1,400   $8,900   $  600  $10,900   280k       <-- LOGS. Debug
                                                                      level left on
                                                                      in production.
  team-data        $  900   $2,100   $  300   $3,300   190k
  team-web         $4,800   $1,900   $  900   $7,600  1,840k      <-- SERIES. Raw
                                                                      URL paths as
                                                                      a label.
  ------------------------------------------------------------------------------
  total           $9,200  $16,300   $3,000  $28,500  2,720k

  Two findings, two one-line fixes:
    team-search: set log level to info in production        -> ~$7,000/month
    team-web:    normalise routes in instrumentation        -> ~$4,000/month and
                                                               dashboards stop
                                                               timing out

  Note that LOGS are the largest line overall - usually true, usually least
  examined, and usually the cheapest thing to fix.

Leading indicator, so you catch it in an hour rather than in the invoice:
  ALERT  series count for a single metric increased >10x in 1h
         -> fires within minutes of a bad deploy, not at month end
```

## Interview tips

- Explain the multiplication with numbers. Going from 1,600 series to 1.6 billion with one label is the clearest possible illustration and immediately establishes that you understand the mechanism.
- Emphasise that the person who added the label had no visibility into the effect. That reframes it from carelessness to a missing platform control.
- The signal-choice table is the real fix: high cardinality belongs in traces and logs, and the answer to "which users are affected" is never a metric label.
- Route normalisation is the single most valuable specific practice and it is usually a one-line change - worth naming explicitly.
- Enforce at the collection point rather than in review, because review will not catch it and the bill changes before the dashboard slows.
- Note that logs are usually the largest line and the least examined. Debug logging left on in production is a very common and very cheap fix.
- Cost attribution per team changes behaviour without policy, and alerting on cardinality growth catches the problem in an hour instead of in the monthly invoice.

---

[⬅ Back to Platform Observability](./README.md) · [All topics](../README.md)
