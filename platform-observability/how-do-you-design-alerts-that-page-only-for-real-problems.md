---
title: "How do you design alerts that page only for real problems?"
id: 219
category: "Platform Observability"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-observability
  - interview-questions
---

# How do you design alerts that page only for real problems?

**Short answer:** Page on symptoms users feel, not on causes; express those symptoms as SLOs and page on error-budget burn rate over multiple windows, so short blips are ignored and real, sustained damage is caught quickly. Everything else - high CPU, a single pod restarting, slow budget burn - becomes a ticket or a dashboard, not a page. Every page must be actionable, owned, and linked to a runbook, and the alert set itself should be reviewed against what actually woke people up.

## Detail

**Start from the definition of a page.** A page interrupts a person, possibly at 3am. It is justified only when three things are true: users are being hurt or will be soon, a human needs to act now, and the person paged can do something about it. An alert that fails any of those tests should not page. Stating that rule explicitly, and applying it to every alert, removes most of the noise before any tooling is involved.

**Symptoms, not causes.** CPU at 95%, a pod restarting, or a replica down are causes that may or may not matter. If users are served well, nobody needs waking. Symptom alerts - error rate, latency, availability as the user sees them - are fewer, cover failure modes you did not predict, and are directly tied to user impact. Cause-based signals still have value, as dashboards for diagnosis and tickets for capacity work.

**Why static thresholds page too often and too late.** "Error rate above 1% for 5 minutes" fires on a brief spike that consumed almost no error budget, and stays silent for a 0.8% error rate that burns the month's budget in four days. The threshold measures the wrong thing: what matters is how fast the service is spending its allowed unreliability.

**Burn-rate alerting fixes that.** With a 99.9% SLO over 30 days, the error budget is 0.1% of requests. A burn rate of 1 spends it exactly over 30 days; a burn rate of 14.4 spends 2% of the monthly budget in one hour. The approach popularised by the Google SRE Workbook uses a small number of windows:

| Severity | Burn rate | Long window | Short window | Budget spent at trigger | Action         |
| -------- | --------- | ----------- | ------------ | ----------------------- | -------------- |
| Page     | 14.4x     | 1 hour      | 5 minutes    | 2%                      | Page on-call   |
| Page     | 6x        | 6 hours     | 30 minutes   | 5%                      | Page on-call   |
| Ticket   | 1x        | 3 days      | 6 hours      | 10%                     | Ticket to team |

The long window makes the alert significant - it has to be real, sustained damage. The short window makes it reset quickly once the problem is fixed, so the page does not keep firing for an hour after recovery.

**Handle low traffic deliberately.** At a few requests per minute, a single failure can look like a huge burn rate. Options include a minimum request count in the alert expression, synthetic traffic to give a steady baseline, or grouping small endpoints into one SLO.

**Route to the owner, with context.** Each alert should carry the owning team from the service catalogue, the SLO it protects, a dashboard link, and a runbook. An alert that pages a shared rotation for a service nobody on it owns produces a handoff, not a fix. Group related alerts and use inhibition - if the whole cluster is down, suppress the hundred service alerts it caused and page once.

**Some cause alerts do deserve pages.** A few conditions predict certain user impact before any symptom exists: a certificate expiring in 24 hours, a disk that will be full in two hours at current growth, a backup that has failed repeatedly. These are fine to page on when the lead time is short and the fix is clear. Keep the list short and justify each one.

**Measure the alert set.** Track pages per on-call shift, the fraction that led to action, the fraction out of hours, and any alert that fired and was acknowledged without anything being done. An alert that is repeatedly ignored is either tuned wrongly or should not exist. Review this at every on-call handover, and delete alerts rather than muting them.

**Where the platform fits.** Product teams, the platform's users, should not hand-write burn-rate expressions. The platform generates SLO recording rules and multi-window alerts from the SLO in the service declaration, routes them using catalogue ownership, and provides the paging integration. Teams choose the objective; the platform makes the alerting correct by default. The platform team also applies the same rules to its own capabilities - see [How do you define SLOs for a platform rather than an application?](../platform-reliability/how-do-you-define-slos-for-a-platform-rather-than-an-application.md) and [How do you run on-call for a platform team?](../platform-reliability/how-do-you-run-on-call-for-a-platform-team.md).

**Trade-offs.** Burn-rate alerting depends on good SLIs; if the SLI does not reflect user experience, the alert will be precise about the wrong thing. It is also slower than a raw threshold for catastrophic failures at very low traffic, which is why teams often keep a simple "service returning no successful requests" alert alongside it.

## Example

```yaml
# Prometheus rules for a 99.9% availability SLO on checkout.
# Generated by the platform from the service declaration.
groups:
  - name: slo-checkout-availability
    rules:
      - record: slo:sli_error:ratio_rate5m
        expr: |
          sum(rate(http_server_request_duration_seconds_count{service_name="checkout", http_response_status_code=~"5.."}[5m]))
          / sum(rate(http_server_request_duration_seconds_count{service_name="checkout"}[5m]))
        labels: { service: checkout, slo: availability }
      # ...equivalent recording rules for 30m, 1h, 6h windows...

      - alert: CheckoutErrorBudgetFastBurn
        expr: |
          slo:sli_error:ratio_rate1h{service="checkout"} > (14.4 * 0.001)
          and
          slo:sli_error:ratio_rate5m{service="checkout"} > (14.4 * 0.001)
        labels:
          severity: page
          team: team-payments
        annotations:
          summary: "checkout is burning its 30-day error budget at over 14x"
          runbook_url: "https://runbooks.example.com/checkout/availability"
          dashboard: "https://grafana.example.com/d/slo-checkout"

      - alert: CheckoutErrorBudgetSlowBurn
        expr: |
          slo:sli_error:ratio_rate6h{service="checkout"} > (6 * 0.001)
          and
          slo:sli_error:ratio_rate30m{service="checkout"} > (6 * 0.001)
        labels: { severity: page, team: team-payments }
        annotations:
          runbook_url: "https://runbooks.example.com/checkout/availability"
```

```text
Alert review at on-call handover - the data that drives deletions:

  ALERT                          FIRED   ACTIONED   OUT OF HOURS   VERDICT
  CheckoutErrorBudgetFastBurn        2          2              1   keep
  NodeCPUHigh                       31          0             12   delete - cause, not symptom
  PodRestarted                      18          1              7   convert to ticket
  CertificateExpiresIn24h            1          1              0   keep - predictive, clear fix
  QueueLagHigh (static 1000)         9          2              4   replace with lag-age SLO

  pages this shift: 61 -> projected after changes: 4
```

## Interview tips

- State the test for a page first: user impact, needs a human now, and the person paged can act. It frames everything else.
- Explain symptoms versus causes with an example, and say where cause signals go instead - dashboards and tickets.
- Show why static thresholds fail with numbers, then explain burn rate. Knowing the 14.4x over 1 hour with a 5-minute short window is a strong signal.
- Explain why there are two windows: the long one for significance, the short one so the alert clears quickly after recovery.
- Mention low-traffic handling, routing to owners with a runbook, and inhibition during large outages - these are where real alerting schemes go wrong.
- Close with measurement: pages per shift and the fraction actioned, and deleting alerts rather than muting them. Then tie it back to the platform generating the rules from the SLO declaration.

---

[⬅ Back to Platform Observability](./README.md) · [All topics](../README.md)
