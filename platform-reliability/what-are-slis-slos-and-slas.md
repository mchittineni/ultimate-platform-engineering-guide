---
title: "What are SLIs, SLOs, and SLAs?"
id: 198
category: "Platform Reliability"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-reliability
  - interview-questions
---

# What are SLIs, SLOs, and SLAs?

**Short answer:** A service level indicator (SLI) is a measurement of how well a service is behaving from its user's point of view, usually a ratio of good events to total events. A service level objective (SLO) is the target you set for that indicator over a time window, such as 99.9% of requests succeeding over 28 days. A service level agreement (SLA) is a contract with a consequence, usually financial, if a promised level is missed - and it should always be looser than the SLO so you find out you are in trouble before it costs money.

## Detail

**An SLI is a ratio of good events to valid events.** "Proportion of HTTP requests that returned a non-5xx response in under 300ms" is an SLI. So is "proportion of deploys that reached production within 15 minutes of merge". Expressing it as a ratio between 0 and 100% matters because it makes every indicator comparable and lets you turn it straight into a budget. The common SLI shapes are availability (did it succeed), latency (was it fast enough), freshness (is the data recent enough), and correctness (was the answer right).

**Measure where the user feels it.** CPU utilisation and pod restarts are not SLIs; they are causes. An SLI measures the symptom a user would notice. The closer you measure to the user - at the load balancer rather than inside the process, or with a synthetic probe from outside - the more honest the number is, at the cost of more noise and more work to collect.

**An SLO is the target plus a window.** "99.9% over a rolling 28 days" means that in any 28-day window, at most 0.1% of valid events may be bad. The window matters as much as the number: a rolling window forgives an incident gradually, whereas a calendar month resets on the first. A 28-day window is popular because it always contains the same number of weekends.

**The target should be set by what users need, not by what is possible.** 100% is the wrong target for almost everything, because users cannot tell the difference between 99.99% and 100% through their own flaky Wi-Fi, and chasing the last fraction makes every change terrifying. The right SLO is the level below which users start to complain or leave - which you find by looking at historical data and at support tickets, not by picking a number of nines that sounds impressive.

**An SLA is an SLO with a lawyer attached.** It is an external promise, written into a contract, with a remedy such as service credits if it is breached. Because breaching it has a cost, the SLA target is set below the internal SLO: if the SLO is 99.9%, the SLA might be 99.5%. The gap is your warning zone. Many internal services, including most internal platforms, have SLOs and no SLA at all, and that is normal.

**Who the user is changes what you measure.** For a product service the user is a customer. For an internal developer platform the user is another engineering team, so the SLIs are things like "merged change running in production within N minutes" or "database claim ready within N minutes" rather than "Argo CD pod is up". The [platform-specific version of this question](./how-do-you-define-slos-for-a-platform-rather-than-an-application.md) goes further into that distinction.

**Trade-offs.** More SLOs is not better: every SLO needs an owner, a dashboard, alerting, and a policy for what happens when it is missed, and a service with fifteen of them effectively has none. Start with one or two per service that capture what users care about most. SLOs also only help if someone acts on them - which is what the [error budget](./what-is-an-error-budget.md) is for.

**Tooling.** SLOs are increasingly written as code. The [OpenSLO](https://github.com/OpenSLO/OpenSLO) specification (stable at `openslo/v1`, with a v2 in development) gives a vendor-neutral YAML format, and open-source generators such as Sloth and Pyrra turn a short SLO definition into Prometheus recording and alerting rules.

## Example

```yaml
# An OpenSLO v1 definition: the SLI (good / total), the objective, and the window.
apiVersion: openslo/v1
kind: SLO
metadata:
  name: checkout-availability
  displayName: Checkout API availability
spec:
  description: Proportion of checkout API requests that do not fail with a server error.
  service: checkout
  indicator:
    metadata:
      name: checkout-non-5xx
    spec:
      ratioMetric:
        counter: true
        good:
          metricSource:
            type: Prometheus
            spec:
              query: sum(rate(http_requests_total{service="checkout",code!~"5.."}[5m]))
        total:
          metricSource:
            type: Prometheus
            spec:
              query: sum(rate(http_requests_total{service="checkout"}[5m]))
  timeWindow:
    - duration: 28d
      isRolling: true
  budgetingMethod: Occurrences
  objectives:
    - displayName: Checkout succeeds
      target: 0.999
```

```text
The three layers for one service, and why they are nested:

  SLI   non-5xx responses / all responses, measured at the load balancer
        last 28 days: 99.94%

  SLO   99.9% over a rolling 28 days            (internal target, owned by the team)
        status: met, 40% of error budget remaining

  SLA   99.5% per calendar month                (contract with customers)
        breach remedy: 10% service credit

  SLI 99.94%  >  SLO 99.9%  >  SLA 99.5%
  The SLO is breached long before the SLA, so the team slows down and fixes
  things while it is still an engineering problem rather than a contractual one.
```

## Interview tips

- Define each one in a sentence and then say how they relate: the SLI is the measurement, the SLO is the internal target, the SLA is the external contract. Getting the nesting right - SLA looser than SLO - is what interviewers listen for.
- Express SLIs as good events over valid events. It shows you know how they are actually computed and sets up the error budget follow-up.
- Say where you would measure it and why - at the edge or with a probe rather than inside the process - because "CPU usage" as an SLI is the classic wrong answer.
- Argue against 100% and against too many SLOs. Both show you have operated one rather than read about it.
- Name the user. For a platform team the user is an engineer, and the SLI should be something like deploy or provisioning time rather than component uptime.
- Expect the follow-up "what happens when you miss the SLO?" - the answer is the error budget and its policy.

---

[⬅ Back to Platform Reliability](./README.md) · [All topics](../README.md)
