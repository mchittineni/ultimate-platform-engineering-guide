---
title: "What is a blameless postmortem?"
id: 200
category: "Platform Reliability"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-reliability
  - interview-questions
---

# What is a blameless postmortem?

**Short answer:** A blameless postmortem is a written review of an incident that asks how the system - the code, tooling, processes, and incentives - allowed the failure, rather than who made the mistake. It assumes everyone acted reasonably given what they knew at the time, which is what makes people willing to tell the whole truth. The output is a shared understanding of what happened and a short list of owned, dated actions that make the same class of failure less likely or less damaging.

## Detail

**Why blame makes systems less reliable.** If an engineer expects to be punished for the command that triggered an outage, they will describe it vaguely, leave out the confusing parts, or avoid owning up at all. The organisation then loses exactly the information it needs: why the command looked safe, why nothing stopped it, and why recovery took so long. Blamelessness is not kindness for its own sake; it is how you get accurate data.

**"Human error" is where the investigation starts, not where it ends.** If one person could delete a production database with a single mistyped command, the real findings are that the command had no confirmation, the credentials had more access than they needed, and the backups had never been restored. A useful test: if you replaced the person with a different, equally competent engineer, would the incident still have been possible? If yes, the problem is in the system.

**Blameless does not mean accountability-free.** People are still accountable for participating honestly, for completing their actions, and for raising risks they see. What changes is that the question "who do we punish?" is replaced by "what do we change?". Deliberate negligence or malice is a separate, rare matter handled outside the postmortem process.

**The usual structure.** A summary a non-specialist can read, the impact in user terms (who was affected, for how long, and how badly), a timeline with timestamps, contributing factors, what went well, what went badly, where you got lucky, and action items. "Where we got lucky" is worth including because luck is an unplanned control: it will not be there next time.

**Look for contributing factors, not a single root cause.** Real incidents almost always need several things to go wrong at once - a latent bug, a missing alert, a deploy at a busy time, a runbook that was out of date. Naming one "root cause" encourages fixing one thing and declaring victory. Techniques such as "five whys" are useful prompts, but asking "what else had to be true for this to happen?" usually finds more.

**Action items are the output that matters.** Each one should have an owner, a date, and a type: prevent (stop it happening), detect (find it faster), or mitigate (reduce the damage). Keep the list short. Fifteen actions nobody completes teach the organisation that postmortems are theatre; three that ship change behaviour. Tracking completion rate across postmortems is one of the simplest reliability metrics there is.

**When to write one.** Agree triggers in advance - for example, any user-visible impact beyond a threshold, any SLO breach, any data loss, or any page that needed escalation. Near misses are worth reviewing too, because they give you the same learning without the damage.

**For a platform team, the audience is other engineers.** A platform incident affects many teams, so publish the postmortem to them, say plainly what they experienced, and say what the platform is changing. Consuming teams trust a platform that explains its failures far more than one that goes quiet. Platform postmortems should also review the response path - whether dashboards, runbooks, and deploy tooling were available - as described in the [platform incident question](./how-do-you-run-an-incident-when-the-platform-itself-is-the-incident.md).

**Trade-offs.** Postmortems take real time, often a day or more of several people's effort, so writing one for every minor alert is wasteful. Language matters more than people expect: "Alice ran the wrong command" and "the runbook's command targeted production by default" describe the same moment with very different effects. Facilitators who were not involved in the incident help keep the review neutral.

## Example

```markdown
# Postmortem: pod creation failed cluster-wide (INC-2291)

**Status:** actions in progress · **Severity:** SEV-1 · **Duration:** 14 min of impact

## Summary

For 14 minutes no new pods could start in the prod-eu-1 cluster. Running
services kept serving traffic; deploys, autoscaling, and restarts failed.

## Impact

- 41 teams could not deploy; 3 services could not scale up during a traffic peak.
- No customer requests failed; checkout latency p99 rose from 280ms to 900ms.

## Timeline (UTC)

- 02:14 Policy admission webhook starts timing out during a node group scale-up.
- 02:15 Page fires. 02:17 On-call finds the in-cluster dashboard unavailable.
- 02:26 Webhook configuration removed (rehearsed mitigation). 02:28 Pods create again.

## Contributing factors

- The webhook's replica count was fixed and was not scaled with the cluster.
- `failurePolicy: Fail` applied to every namespace, including the webhook's own.
- Triage dashboards ran inside the cluster that was failing.

## What went well / where we got lucky

- The mitigation was documented and worked first time.
- Lucky: the peak was short; a longer one would have exhausted running capacity.

## Action items

| Action                                       | Type     | Owner | Due        |
| -------------------------------------------- | -------- | ----- | ---------- |
| Autoscale the webhook and add a PDB          | Prevent  | Priya | 2026-10-09 |
| Exclude platform namespaces from the webhook | Mitigate | Tom   | 2026-10-02 |
| Move triage dashboards outside the cluster   | Detect   | Sam   | 2026-10-30 |
```

## Interview tips

- Define it by its question: "how did the system allow this?" rather than "who did this?". Then explain why - blame destroys the information you need.
- Use the "replace the person" test or the "human error is the start of the investigation" line; both show you understand the idea rather than the slogan.
- Say explicitly that blameless is not accountability-free. Interviewers often probe this.
- Prefer contributing factors over a single root cause, and give the action-item types: prevent, detect, mitigate.
- Mention tracking action-item completion. A postmortem culture with open actions from last year is the most common way this goes wrong.
- For a platform role, name the audience: publish to the consuming teams, and review the response path as well as the cause.

---

[⬅ Back to Platform Reliability](./README.md) · [All topics](../README.md)
