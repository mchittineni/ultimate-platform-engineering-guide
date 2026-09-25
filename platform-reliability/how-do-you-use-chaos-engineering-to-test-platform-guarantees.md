---
title: "How do you use chaos engineering to test platform guarantees?"
id: 204
category: "Platform Reliability"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-reliability
  - interview-questions
---

# How do you use chaos engineering to test platform guarantees?

**Short answer:** Start from a promise the platform makes - "a node failure does not affect a tier-1 service", "a control-plane outage does not stop serving traffic" - state it as a hypothesis with a measurable steady state, then remove the thing and see whether the promise held. For a platform team there are two distinct uses: verifying your own degradation behaviour, and offering fault injection as a capability so consuming teams can verify theirs.

## Detail

**A hypothesis, not an experiment for its own sake.** The format is: given this steady state, when I remove this, I expect the following to remain true. Without a written hypothesis and a defined steady state you are breaking things and observing, which produces anecdotes rather than findings. And the interesting result is a falsified hypothesis - the value is in what you believed and were wrong about.

**Start with the promises you have already made.** Your SLOs and your degradation table are a ready-made list of experiments. "Deploys pause but traffic is unaffected when the reconciler is down" is a claim in your degradation table; the experiment is scaling the reconciler to zero and confirming it.

**The platform-specific experiments** are the ones nobody else can run, because only the platform team can remove these components:

| Experiment                                 | Verifies                                                 |
| ------------------------------------------ | -------------------------------------------------------- |
| Scale the reconciler to zero               | Deploys pause; running workloads unaffected              |
| Make the policy webhook unreachable        | Correct failure policy behaviour; no pod-creation outage |
| Block egress to the flag provider          | Cached ruleset serves; no mass flip to defaults          |
| Kill the telemetry collector               | Workloads unaffected; buffering behaves                  |
| Drain a whole node group                   | Disruption budgets hold; rescheduling capacity exists    |
| Fail a zone                                | Topology spread and failover actually work               |
| Make the secret store unreachable          | Running pods fine; new pods fail clearly                 |
| Sever the link to on-premises              | Both sides degrade as designed                           |
| Exhaust API server capacity for one tenant | Priority and fairness protects the others                |

**Offer fault injection as a capability, not only as an exercise you run.** Teams should be able to inject latency into a dependency, return errors from a downstream service, or kill a replica of their own workload, within their own namespace, with a blast radius the platform enforces. That turns resilience from something the platform asserts into something each team can verify - and it is a genuinely valuable platform capability rather than a one-off event.

**Constrain blast radius by construction.** Namespace-scoped, a maximum affected proportion, a time limit, an automatic abort on SLO burn, and a hard stop anyone can trigger. Without those, an experiment becomes an incident and chaos engineering loses organisational support permanently after the first bad one.

**Start in non-production, but do not stay there.** Non-production is where you find the obvious failures and build confidence in the tooling. Production is where the interesting findings are, because non-production differs in scale, traffic, and configuration. Move there deliberately, with a small blast radius, during business hours, with the owning team present.

**Game days are the higher-value format for a platform.** A scheduled exercise with a scenario, participants, and observers tests the response path as well as the system - whether the runbook is correct, whether dashboards are reachable, whether the on-call engineer can find the mitigation. Many of the most valuable findings are about the response, not the failure.

**Use a maintained injector rather than scripts.** For Kubernetes, Chaos Mesh and LitmusChaos are both CNCF incubating projects that express faults as custom resources, which makes them easy to wrap in a platform-owned API with enforced limits; the managed cloud services, AWS Fault Injection Service and Azure Chaos Studio, add cloud-level faults such as zone or API failures with IAM-scoped stop conditions. The tool matters less than the hypothesis, steady state, and blast-radius controls around it.

**Regulation increasingly expects this evidence.** For EU financial entities, the Digital Operational Resilience Act (DORA), in application since 17 January 2025, requires a risk-based digital operational resilience testing programme and, for entities designated by their supervisors, threat-led penetration testing at least every three years. A chaos programme with written hypotheses, results, and closed findings is exactly the kind of record that satisfies an auditor, whereas ad hoc experiments are not.

**Record and act on findings, or it becomes theatre.** Each experiment produces either a confirmed hypothesis or a defect, and the defects need owners and dates. A programme that runs experiments and does not close findings is worse than none, because it produces false confidence.

**Do not run experiments during an error budget freeze.** Chaos spends reliability deliberately, which is legitimate when there is budget and irresponsible when there is not. Tying the programme to the error budget policy is the discipline that keeps it defensible.

## Example

```yaml
# A hypothesis, not a fault injection. Steady state, abort criteria, and blast
# radius are all part of the definition.
apiVersion: platform.example.com/v1
kind: ChaosExperiment
metadata: { name: reconciler-outage }
spec:
  hypothesis: >
    Given tier-1 services serving normally, when the GitOps reconciler is
    unavailable for 15 minutes, then production traffic is unaffected, deploys
    queue rather than fail, and the queued deploys apply automatically on
    recovery.
  steadyState:
    - { metric: tier1_availability, condition: "> 99.9%" }
    - { metric: tier1_latency_p99, condition: "< 300ms" }
    - { metric: pod_creation_success_rate, condition: "> 99%" }
  method:
    action: scale-to-zero
    target: { namespace: argocd, deployment: argocd-application-controller }
    duration: 15m
  blastRadius:
    environment: production
    scope: platform-component # affects change, not traffic - by hypothesis
    maxAffectedTenants: all # this is a platform-wide component; that is the point
    businessHoursOnly: true
    onCallPresent: required
  abort:
    - { metric: tier1_availability, condition: "< 99.5%", action: restore }
    - { metric: pod_creation_success_rate, condition: "< 95%", action: restore }
    - manual: true # anyone can stop it
  requires:
    errorBudgetRemaining: "> 40%" # never during a freeze
```

```yaml
# Fault injection as a self-service capability - a team verifying ITS OWN
# resilience, with a blast radius the platform enforces.
apiVersion: platform.example.com/v1
kind: FaultInjection
metadata: { name: pricing-latency, namespace: team-payments }
spec:
  owner: alice@example.com
  # Platform-enforced: cannot exceed this namespace, cannot exceed 25% of
  # traffic, cannot run longer than 10 minutes, aborts on the team's own SLO burn.
  target:
    service: pricing # a dependency of checkout
    percentage: 20
  fault:
    type: latency
    delay: 2s
  duration: 10m
  abortOnSloBurn: true
  hypothesis: >
    Checkout's 2s timeout and fallback to cached pricing hold, so checkout's
    availability SLO is unaffected when pricing is slow for 20% of calls.
```

```text
A game day - and note that most findings were about the RESPONSE, not the system.

  SCENARIO  "The policy webhook becomes unreachable during a node group scale-up."
  PARTICIPANTS  on-call engineer (did not build it), incident commander, 2 observers
  DURATION  90 minutes

  FINDINGS
    SYSTEM
      ✓ failurePolicy: Ignore meant pods continued to create
      ✓ alert fired within 40s
      ✗ the alert's runbook link 404'd - the page had been renamed
    RESPONSE PATH
      ✗ on-call could not find how to confirm whether policy was being enforced;
        no dashboard showed enforcement state, only webhook health
      ✗ 6 minutes spent determining whether this was consumer-visible; the
        degradation table was not linked from the alert
      ✓ mitigation procedure was correct and worked first time
    COMMUNICATION
      ✗ no template for "a control is temporarily unenforced" - the commander
        wrote one under pressure and it was ambiguous about impact

  4 of 5 findings are about the response, not the failure. That ratio is typical,
  and it is the argument for game days over automated experiments alone.
  All 4 have owners and dates.
```

## Interview tips

- Insist on the hypothesis format with a measurable steady state. "We break things in production" is the answer that suggests you have not run a programme.
- Point out that your SLOs and degradation table are a ready-made experiment list. That connects chaos work to commitments you already made rather than treating it as a separate activity.
- The two distinct uses - verifying your own degradation, and offering fault injection as a self-service capability - is the platform-specific framing and a strong differentiator.
- Blast radius constrained by construction, with automatic abort on SLO burn, is what keeps the programme alive. One bad experiment ends organisational support permanently.
- Say you would start in non-production and deliberately move to production, because non-production differs in scale, traffic, and configuration.
- Game days as the higher-value format, with the observation that most findings concern the response path rather than the system, is the most memorable point available here.
- Tying experiments to error budget availability - never during a freeze - shows the programme is disciplined rather than enthusiastic.

---

[⬅ Back to Platform Reliability](./README.md) · [All topics](../README.md)
