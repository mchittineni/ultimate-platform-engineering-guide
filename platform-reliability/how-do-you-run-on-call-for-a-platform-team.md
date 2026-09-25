---
title: "How do you run on-call for a platform team?"
id: 203
category: "Platform Reliability"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-reliability
  - interview-questions
---

# How do you run on-call for a platform team?

**Short answer:** Page only on platform-owned symptoms that a human must act on now, route everything else to a queue, and be explicit about the boundary between the platform's on-call and the consuming teams' on-call - because the default failure is that the platform rotation becomes the first responder for every problem in the organisation. A small team also needs a sustainable rotation, which is often the binding constraint on what you can promise.

## Detail

**The distinctive problem is boundary, not volume.** When something breaks, the affected team frequently cannot tell whether the cause is their code or the platform, so the platform rotation receives everything. Without a stated boundary and a triage path, the platform team becomes a help desk for the whole organisation and its own work stops.

**Define the boundary and publish it.** The platform's on-call owns platform capabilities failing their SLOs and platform components in the data path. The service's on-call owns their service's own errors, their own resource exhaustion, and their own bad deploys. The genuinely ambiguous cases - is this the mesh or the application? - need a documented first-triage step so the question can be answered in minutes rather than escalated.

**Page on symptoms, not on causes.** A controller restarting is not a page if reconciliation is still within its SLO. Reconciliation lag exceeding the objective is a page. A single node failing is not a page; capacity falling below the level needed to reschedule is. Alerting on component health rather than on consumer-visible symptoms is how platform rotations become unsustainable.

**Burn-rate alerts should be the primary page source.** They fire when the SLO is genuinely threatened, which is the definition of something worth waking someone for, and they naturally suppress the noise of transient component failures that consumers never noticed.

**Every page needs a runbook that assumes no context.** The person paged may not have built the capability. The runbook should state how to confirm the symptom, the first three diagnostic steps, the mitigations available including any break-glass, and who to escalate to. A page with no runbook is a design defect, and it is reasonable to treat adding one as part of shipping the capability.

**Rotation size is a real constraint.** A four-person rotation is one week in four, which is sustainable if pages are rare and brutal if they are not. If your page volume needs more people than you have, the honest options are reducing the page volume, lowering a target you cannot sustain, or getting more people - not quietly accepting attrition. Being able to say that plainly is a sign of maturity.

**Measure the rotation, not just the incidents.** Pages per shift, out-of-hours pages, actionable versus noise, and time to acknowledge. A rotation with more than a couple of out-of-hours pages per week is degrading, and the fix is almost always eliminating a recurring alert rather than tuning its threshold.

**Follow-the-sun only if you genuinely have the geography.** Splitting a small team across time zones to avoid night pages leaves too few people per region. It works when you have real teams in each region and not otherwise.

**Feed pages back into the roadmap.** The same page three times is a missing capability, a missing automation, or a wrong default. This is the same product-feedback loop as break-glass activations and policy exceptions, and it is the mechanism that makes the rotation get quieter over time rather than louder.

## Example

```text
The published boundary - so the ambiguous case has an answer in minutes.

  PLATFORM ON-CALL OWNS
    ingress, DNS, mesh data path returning platform errors
    deploy capability breaching its SLO (reconciliation lag, pipeline stuck)
    provisioning capability failing or breaching its SLO
    cluster-wide problems: control plane, CNI, CSI, admission webhooks
    platform-managed datastore and secret delivery failures
    capacity insufficient to reschedule workloads

  SERVICE ON-CALL OWNS
    their service's 5xx and latency
    their own OOMKills, crash loops, and failed migrations
    their own bad deploy (rollback is theirs; the mechanism is ours)
    their own quota exhaustion within their granted quota
    their own dependency failures on other product services

  AMBIGUOUS - documented first triage, answerable in minutes
    "requests to my service are failing"
      1. is the error a platform error or an application error?
         -> check the ingress and mesh error classification dashboard
      2. are OTHER services in the same cluster affected?
         -> yes: platform. no: service.
      3. did a deploy or a flag flip precede it?
         -> check the change feed (deploys, flags, infra, policy in one place)
      4. still unclear after 5 minutes -> page platform on-call, and the
         retrospective adds whatever signal would have answered it faster.
```

```yaml
# Page on consumer-visible symptoms, not on component health.
groups:
  - name: platform-pages
    rules:
      # PAGE: the deploy capability is failing its objective
      - alert: DeployCapabilityFastBurn
        expr: |
          platform:deploy_slo_burn_rate:1h > 14.4
          and platform:deploy_slo_burn_rate:5m > 14.4
        labels: { severity: page, capability: deploy }
        annotations:
          summary: "Deploy capability burning error budget 14.4x - merges are not reaching production"
          runbook: "https://docs.example.internal/runbooks/deploy-capability"

      # PAGE: capacity insufficient to survive a node loss
      - alert: InsufficientReschedulingCapacity
        expr: |
          platform:allocatable_after_largest_node_loss:ratio < 1.0
        for: 10m
        labels: { severity: page }
        annotations:
          runbook: "https://docs.example.internal/runbooks/capacity"

      # NOT A PAGE: a controller restarting while reconciliation is healthy.
      # Ticket only - the consumer experienced nothing.
      - alert: ControllerRestarting
        expr: increase(kube_pod_container_status_restarts_total{namespace="platform"}[1h]) > 3
        labels: { severity: ticket }
```

```text
Rotation health - the numbers that decide whether it is sustainable:

  $ platform oncall report --last 90d

  rotation size ......................... 5 engineers (1 week in 5)
  pages per shift (median) .............. 2
  OUT-OF-HOURS pages per week ........... 4.1     <-- degrading. Target < 2.
  actionable ............................ 61%     <-- 39% noise. Fix the alerts.
  median time to acknowledge ............ 4m
  median time to mitigate ............... 22m

  TOP RECURRING PAGES - the roadmap, not the rota
    "reconciliation lag on prod-eu-2" ..... 11x   root cause: repo-scale
                                                 reconciliation; sharding needed
    "preview env stuck provisioning" ...... 8x    root cause: quota exhaustion in
                                                 the preview namespace; needs
                                                 auto-reap on quota pressure
    "webhook timeout during node scale" ... 6x    root cause: webhook not scaled
                                                 with the cluster
    -> 25 of the last 90 days' pages are three fixable causes. Fixing them takes
       out-of-hours pages from 4.1/week to roughly 1. That is the work.
```

## Interview tips

- Lead with the boundary problem, because it is what distinguishes platform on-call from service on-call: the affected team often cannot tell whose fault it is, so everything arrives at the platform rotation.
- Publishing the boundary plus a documented first-triage path for ambiguous cases is the concrete answer, and the "are other services affected?" step is a good, cheap discriminator.
- "Page on symptoms, not on causes" with the controller-restart example - not a page if reconciliation is healthy - shows you have tuned a real rotation.
- Burn-rate alerts as the primary page source ties on-call to the SLOs and naturally suppresses invisible component churn.
- Be candid about rotation size as a constraint on what you can promise, and give the honest options: reduce pages, lower the target, or add people.
- Measuring out-of-hours pages per week as the sustainability metric, and treating recurring pages as roadmap items, is the senior close - it is how a rotation gets quieter rather than louder.

---

[⬅ Back to Platform Reliability](./README.md) · [All topics](../README.md)
