---
title: "How do you make traces useful across team boundaries?"
id: 115
category: "Platform Observability"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-observability
  - interview-questions
---

# How do you make traces useful across team boundaries?

**Short answer:** Standardise the propagation format so context survives every hop, sample consistently so a trace is either kept whole or not at all, agree the attributes that make a span attributable to a team, and give every engineer read access to the full trace regardless of which team's spans it contains. A trace that stops at a boundary or is half-sampled is worse than no trace, because it looks complete and is not.

## Detail

**Standardise the propagation format across the estate.** W3C Trace Context is the interoperable choice, and mixing formats between services is the most common cause of traces breaking at a boundary - one service propagates one header, the next reads a different one, and the trace silently splits into two. Vendor-specific formats can be accepted for compatibility, but one format must be emitted everywhere.

**Sample consistently, or you get partial traces.** If two services independently decide whether to sample, you get traces missing arbitrary middle sections. Two approaches work: head-based sampling where the decision is made once and propagated so every service honours it, or tail-based sampling in the collector where the full trace is buffered and kept or dropped as a unit. Tail sampling is better because the decision can depend on the outcome - keep everything that errored or was slow - and it requires all spans of a trace to reach the same collector instance, which is what drives the collector topology.

**Agree the attribute conventions centrally.** OpenTelemetry semantic conventions cover the standard ones; the platform should add and inject the organisational ones - service, tenant, tier, version, owning team, cluster. Without a consistent owning-team attribute you cannot answer "which team's span is the slow one", which is the entire point of a cross-team trace.

**Give everyone read access to whole traces.** Restricting trace visibility to the owning team means nobody can see across a boundary, which defeats the purpose. Traces are operational data and should be broadly readable; the correct control is redaction at the collector so sensitive values never enter the trace, not access restrictions on the trace afterwards. That distinction is the important one - fix it in the pipeline, not in the permissions.

**The context breaks in predictable places.** Message queues where the producer does not inject context into the message, thread pools and async executors where the context is not carried across the boundary, batch jobs that process a queue of items and start a new trace per item, and custom protocols. Each has a known fix, and the platform should test propagation as a capability rather than trusting it.

**Decide how to handle asynchronous boundaries deliberately.** A queue can be modelled as a continuation of the same trace or as a link between two traces. Continuation gives you the whole flow and can produce very long-lived traces; links keep traces bounded and require a join to follow the flow. Either is defensible, but it must be consistent across the estate or cross-team analysis becomes unreliable.

**Make the trace the shared artefact during incidents.** The practical value of cross-team tracing is that a single trace ID settles the "it is not us" conversation in seconds. That works only if everyone can open it, everyone's spans are present, and each span identifies its owning team - which is why the three requirements above are the substance rather than the tooling.

**Expose the propagation health as a metric.** The proportion of traces that terminate before reaching a known downstream, and the proportion of spans with a missing parent, are direct measures of whether propagation is working. Broken propagation otherwise stays invisible because the traces you look at appear whole.

## Example

```text
The failure that motivates all of this - a trace that looks complete and is not.

  request -> web-bff -> checkout -> pricing -> [orders queue] -> fulfilment -> carrier-api

  WHAT THE TRACE SHOWS
    web-bff        12ms
    checkout      340ms
    pricing         8ms
    (ends)
  -> looks like checkout is slow. Three teams spend two hours on checkout.

  WHAT ACTUALLY HAPPENED
    the queue producer did not inject trace context into the message, so
    fulfilment started a NEW trace. The 4.2s spent in carrier-api is in a
    different trace nobody thought to look for.

  A trace that stops at a boundary is worse than no trace: an absent trace makes
  you look elsewhere, a truncated one makes you look confidently in the wrong place.
```

```python
# The fixes at the two boundaries that break most often.

# 1. QUEUE - inject context into the message on publish, extract on consume.
from opentelemetry import propagate, trace

def publish(topic, payload):
    headers = {}
    propagate.inject(headers)          # W3C traceparent into message headers
    queue.send(topic, payload, headers=headers)

def consume(message):
    ctx = propagate.extract(message.headers)
    # Link, not continuation, for a queue - keeps traces bounded. Chosen
    # deliberately and applied consistently across the estate.
    with trace.get_tracer(__name__).start_as_current_span(
        "process orders", links=[trace.Link(trace.get_current_span(ctx).get_span_context())]
    ):
        handle(message)

# 2. THREAD POOL - the context does not cross the boundary by itself.
from opentelemetry.context import attach, detach, get_current

def submit_with_context(executor, fn, *args):
    ctx = get_current()
    def wrapped():
        token = attach(ctx)
        try:
            return fn(*args)
        finally:
            detach(token)
    return executor.submit(wrapped)
```

```yaml
# Platform-injected attributes so every span identifies its owning team.
# Without a consistent owning-team attribute, "whose span is slow?" is unanswerable.
processors:
  k8sattributes:
    extract:
      labels:
        - { tag_name: platform.tenant, key: platform.example.com/tenant, from: namespace }
        - { tag_name: platform.owner, key: platform.example.com/owner, from: pod }
        - { tag_name: platform.tier, key: platform.example.com/tier, from: pod }

  # Redact in the PIPELINE - so traces can be broadly readable without exposing
  # sensitive values. Fix it here, not in the permissions.
  attributes/redact:
    actions:
      - { key: http.request.header.authorization, action: delete }
      - { key: db.statement, action: delete }
      - { key: user.email, action: hash }
```

```text
Propagation health as a metric - otherwise broken propagation stays invisible,
because the traces you happen to open look whole.

  $ platform trace health

  traces terminating before a known downstream .......... 8.4%   <-- investigate
    by boundary:
      publish to orders queue ........................... 6.1%   context not
                                                                 injected
      async executor in team-search/indexer ............. 1.9%   context not
                                                                 propagated
      custom TCP protocol in team-data/etl .............. 0.4%   no instrumentation
  spans with a missing parent ........................... 7.8%
  services emitting a non-W3C propagation format ........ 2      <-- one format,
                                                                    everywhere
  spans missing the platform.owner attribute ............ 0.3%
  mixed sampling decisions within one trace .............. 0%    ✓ tail sampling
                                                                    keeps traces whole

  The 6.1% row was the cause of the two-hour investigation above. It was
  measurable the whole time; nobody was measuring it.
```

## Interview tips

- Open with the failure: a truncated trace is worse than an absent one, because it makes you look confidently in the wrong place. The queue example makes this vivid.
- Name W3C Trace Context and say that mixed formats are the most common cause of breakage at a boundary.
- Consistent sampling is the second requirement, and tail sampling is the better answer because the decision can depend on the outcome - keep everything that errored. Mention that it requires all spans of a trace at one collector instance.
- The owning-team attribute is what makes a cross-team trace actionable: without it, "whose span is slow" is unanswerable.
- "Redact in the pipeline, not in the permissions" is the sharp point on access - restricting trace visibility per team defeats the purpose of cross-team tracing.
- Deciding continuation versus links for asynchronous boundaries, and applying it consistently, shows you have thought past the happy path.
- Propagation health as a metric is the strongest close: broken propagation is invisible by nature, and measuring termination rates makes it a fixable defect rather than a mystery.

---

[⬅ Back to Platform Observability](./README.md) · [All topics](../README.md)
