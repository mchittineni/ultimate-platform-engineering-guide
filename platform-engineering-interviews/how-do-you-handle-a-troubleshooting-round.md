---
title: "How do you handle a troubleshooting round?"
id: 134
category: "Platform Engineering Interviews"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-engineering-interviews
  - interview-questions
---

# How do you handle a troubleshooting round?

**Short answer:** Establish the scope before touching anything - is it one service or all of them, one cluster or all, when did it start, what changed - then work the layers from the outside in, stating what each observation rules out. The round is testing method rather than recall, so narrating your reasoning matters more than naming the right command, and asking "what changed" early is the highest-yield question available.

## Detail

**Scope first, because it eliminates most of the search space in one question.** One service failing and every service failing have almost no diagnostic overlap. One cluster versus all cluster points at the platform or at a workload. One region versus all points at infrastructure. Two or three scoping questions typically remove ninety percent of the possibilities, and asking them is the single clearest signal of experience in this round.

**Ask what changed, early.** Deploys, flag flips, infrastructure changes, policy changes, certificate expiries, quota changes, and scale events. Most incidents follow a change, and in a platform context the change may not be the affected team's - a policy rollout or a platform component upgrade is a common cause. Candidates who never ask this are guessing.

**Work the layers from where the user is, inward.** DNS resolves, then the load balancer has healthy targets, then the service has endpoints, then pods are running and ready, then the container is healthy, then its dependencies respond. Each step either localises the problem or eliminates a layer, and saying which is what demonstrates method.

**Say what each observation rules out.** "Pods are running and ready, so this is not a scheduling or startup problem - which points at either the service selector or something upstream" is much stronger than silently moving on. The interviewer cannot see your reasoning unless you speak it, and the reasoning is what is being assessed.

**Distinguish mitigation from diagnosis, and mitigate first if there is impact.** If production is affected, restoring service comes before understanding - roll back, fail over, remove the offending component, disable the flag. Saying "before I continue diagnosing, if this is affecting production I would roll back the deploy from twenty minutes ago" is a strong, senior move and is often what the interviewer is waiting for.

**Have a small set of high-yield checks ready** rather than a long tool list. For a platform-shaped problem: recent changes, events in the affected namespace, whether other tenants are affected, control-plane health, admission webhook status, quota and capacity, and certificate expiry. Knowing why each one is high-yield matters more than the exact command.

**Expect the deliberately underspecified prompt.** "Deploys are stuck. Nothing is alerting." The missing information is the point - the interviewer wants to see which questions you ask. Treat silence as an invitation to ask rather than a requirement to guess.

**Do not fixate.** If two or three observations contradict your hypothesis, say so and form a new one out loud. Interviewers frequently plant a red herring specifically to see whether you abandon a theory that stops fitting.

**Say when you would escalate or ask for help.** "At this point I would pull in whoever owns the network path, because I have ruled out everything above it" is a good answer, not an admission of weakness. Nobody wants a colleague who spends four hours alone on someone else's layer.

**Finish with prevention.** How would this have been caught earlier, what alert was missing, what would you add to the runbook. A candidate who ends at the root cause has answered half the question.

## Example

```text
"Teams report that deploys are stuck. Nothing is alerting. Go."

  SCOPE FIRST - three questions that remove most of the search space
    "Is it every team or some teams?"                     -> every team
    "Every cluster, or one?"                              -> all three production
    "When did it start, and is anything still deploying?" -> ~40 min ago; nothing
    "Are RUNNING services affected, or only deployments?" -> running is fine

    -> already enormous progress: every team, every cluster, running workloads
       healthy. This is a control-plane problem, not a workload problem. It is
       almost certainly a single shared component.

  WHAT CHANGED - the highest-yield question
    "What changed in the last hour - platform deploys, policy rollouts, component
     upgrades, certificate renewals?"
    -> "the platform team rolled out a policy bundle update about 45 minutes ago"
    -> strong hypothesis immediately, and note it is OUR change, not a team's.

  MITIGATE BEFORE DIAGNOSING FURTHER
    "Deploys being stuck is not customer-facing, so I have some room. If this were
     affecting production traffic I would roll the bundle back now and diagnose
     afterwards. Here I would still prepare the rollback so it is one command away,
     then spend ten minutes confirming, because rolling back blind can lose the
     evidence."

  WORK THE LAYERS, saying what each rules out
    1. Is the reconciler healthy?
       "argocd application controller pods running, no restarts, no errors in
        logs. So this is not the reconciler being down - it is being PREVENTED
        from doing something."
    2. What do the Applications say?
       "OutOfSync, and the sync operation is failing. The message would tell me
        what is rejecting it."
    3. Is admission rejecting it?
       "This is where I would look hardest, given the policy rollout. I would
        check the webhook's own health and whether it is timing out, and I would
        look at API server logs for admission denials."
       -> the new bundle added a policy requiring a label that 200 existing
          workloads do not have, in Enforce mode with no audit period.
    4. RULED OUT along the way: not the reconciler, not the API server generally
       (other operations work), not capacity, not certificates, not networking.

  ROOT CAUSE AND MITIGATION
    "A policy went to Enforce without an audit period, so every existing workload
     fails admission on its next sync. Mitigation: revert the bundle version -
     that is a one-command rollback and it restores deploys immediately. Then
     re-introduce the policy in Audit, measure how many workloads violate it, fix
     or exempt them, then Enforce."

  IF THE HYPOTHESIS HAD NOT FIT - say so out loud
    "If the webhook were healthy and no denials appeared, I would abandon the
     policy theory. Next candidates: the reconciler cannot reach the Git provider,
     or repository-scale reconciliation is backed up rather than failing - those
     look similar from a team's perspective and are distinguished by whether sync
     is failing or simply queued."

  PREVENTION - the half of the answer candidates skip
    "Two things. First, no policy reaches Enforce without an audit period and a
     violation count - that is a process gap, and it is the actual root cause.
     Second, nothing alerted for 40 minutes, which means we have no SLO on the
     deploy capability. Deploy latency exceeding its objective should page. I
     would add a burn-rate alert on reconciliation lag, and a check that fails a
     bundle release if a new policy is in Enforce with unresolved violations."
```

## Interview tips

- Open with scoping questions, always. One service versus all, one cluster versus all, when it started, and whether running workloads are affected - those four typically eliminate most of the search space.
- Ask what changed early. In a platform context, remember the change may be yours rather than the affected team's, and saying that shows you understand the role.
- Narrate what each observation rules out. Silent correct steps score far less than spoken reasoning, because the reasoning is the thing being assessed.
- Separate mitigation from diagnosis, and offer to mitigate first when there is impact. Also worth saying that rolling back blind can destroy the evidence - that nuance reads as experienced.
- Keep a small set of high-yield platform checks and know why each is high-yield: recent changes, events, other tenants affected, control-plane health, webhook status, quota, certificates.
- Abandon a hypothesis out loud when observations stop fitting. Red herrings are often deliberate.
- Say when you would escalate. It is a strength, not a weakness.
- Always finish with prevention - the missing alert and the process gap. Ending at the root cause answers half the question.

---

[⬅ Back to Platform Engineering Interviews](./README.md) · [All topics](../README.md)
