---
title: "What is a guardrail and how does it differ from a gate?"
id: 133
category: "Policy as Code and Governance"
difficulty: "Beginner"
tags:
  - platform-engineering
  - policy-as-code-and-governance
  - interview-questions
---

# What is a guardrail and how does it differ from a gate?

**Short answer:** A guardrail is a control that keeps you out of a bad state automatically, without anyone having to stop and decide: it fixes the problem, supplies a safe default, or rejects the change instantly with a clear reason. A gate is a checkpoint where progress waits until a person, or a slow process, says yes. Guardrails scale with the number of teams and gates do not, so a platform uses guardrails for almost everything and keeps gates for the few decisions that really need human judgement.

## Detail

**The metaphor is accurate.** A guardrail on a mountain road does not slow you down or ask you where you are going. It only matters if you are about to go over the edge. A toll gate stops every car, whatever the driver intends. Platform controls work the same way. A guardrail is invisible on the happy path. A gate costs every change some time.

**What counts as a guardrail.** Four forms, from gentlest to strongest:

| Mechanism         | What happens                                           | Example                                                     |
| ----------------- | ------------------------------------------------------ | ----------------------------------------------------------- |
| Safe default      | The platform supplies the right value if none is given | A `LimitRange` fills in memory requests                     |
| Automatic fix     | The platform corrects the change as it arrives         | Admission mutation adds `runAsNonRoot: true`                |
| Instant refusal   | The change is rejected at once, with the fix spelt out | Admission rejects a public load balancer in a PCI namespace |
| (Not expressible) | The interface has no way to ask for the bad state      | The database template has no "disable encryption" field     |

The last row is the strongest guardrail of all: if the self-service interface cannot express a public bucket, no policy ever has to reject one.

**What counts as a gate.** A manual change-approval board, a security review ticket before a new service can deploy, a required sign-off before production promotion, a waiting period. What they have in common is that the change sits in a queue, and the queue grows with the number of teams while the reviewers do not.

**Why the distinction matters to the users of the platform.** The people who meet these controls are application developers trying to ship. A guardrail costs them nothing when they are doing the right thing and gives them an immediate, actionable answer when they are not. A gate costs them waiting time on every change, including the ninety-nine changes that were fine, and teaches them that the platform is something to get around. That is how shadow infrastructure starts.

**Gates are not always wrong.** Some decisions need judgement that a rule cannot encode: accepting a risk exception, launching a service that handles a new category of personal data, approving a large capacity commitment. The skill is keeping gates rare, putting them on decisions and not on routine changes, and making them fast. A gate that approves 100% of requests is a delay dressed up as a control, and should be turned into a guardrail or removed.

**Rejection is a guardrail only if it is instant and explains itself.** A policy that rejects a deploy with "denied by policy" behaves like a gate in practice, because the developer now has to find someone who can explain it. The same rejection with "container `api` has no memory request; add `resources.requests.memory` (platform default 128Mi)" is a guardrail: the developer fixes it in a minute without talking to anyone.

**A useful ordering when designing a control:** can the platform make the bad state impossible? If not, can it fix it automatically? If not, can it reject instantly with a good message? Only if none of those work, and the decision really needs a human, add a gate. This is the same thinking as a [golden path versus a mandate](../platform-engineering-fundamentals/what-is-a-golden-path-and-how-does-it-differ-from-a-mandate.md): make the right thing the easy thing instead of policing the wrong thing.

**The trade-off.** Guardrails push the work onto the platform team. Someone has to write, test, and maintain the mutation, the default, and the error messages, and an automatic fix can hide a problem the team should have understood. Gates are cheap to create and expensive to run, which is exactly why organisations have too many of them.

## Example

```text
One requirement, "production workloads must not run as root", implemented both ways.

AS A GATE
  1. Team opens a security review ticket before first production deploy
  2. Reviewer reads the manifests by hand (queue: 4 working days)
  3. Reviewer approves; team deploys
  4. Six months later a chart upgrade removes the securityContext.
     Nobody reviews it, because the gate only ran once.
  Cost: 4 days per new service, and it still misses drift.

AS A GUARDRAIL
  1. The golden-path template sets runAsNonRoot: true   (safe default)
  2. Admission mutation adds it if a manifest omits it   (automatic fix)
  3. Admission rejects runAsUser: 0 explicitly set, with a message
     explaining how to use a non-root image              (instant refusal)
  4. A background scan reports any running pod that predates the policy
  Cost: zero for teams on the happy path, and it applies to every change,
  forever, including the chart upgrade.
```

```yaml
# The "instant refusal" layer, as a native Kubernetes policy (GA since 1.30).
# The message is what makes it a guardrail rather than a gate.
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: disallow-root-user
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
      - apiGroups: [""]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["pods"]
  validations:
    - expression: >-
        object.spec.?securityContext.?runAsUser.orValue(1) != 0 &&
        object.spec.containers.all(c,
          c.?securityContext.?runAsUser.orValue(1) != 0)
      message: >-
        The pod or a container sets runAsUser: 0 (root). Remove the field to use the
        platform default (non-root), or switch to a non-root base image -
        see go/platform-nonroot.
```

## Interview tips

- Give a crisp definition of each: a guardrail keeps you out of a bad state automatically, a gate makes you wait for a decision. Then say that guardrails scale with the number of teams and gates do not.
- Walk through the ordering: make it impossible, fix it automatically, reject it instantly with a clear message, and only then add a gate. It shows a design method, not just vocabulary.
- Point out that a rejection with a useless error message behaves like a gate, because the developer has to go and find a human.
- Do not claim gates are always bad. Name the decisions that deserve one, such as risk acceptance or a new category of sensitive data, and say gates should be rare, fast, and on decisions, not on routine changes.
- A likely follow-up is "how would you remove an existing gate?" A good answer is to measure its approval rate, encode what reviewers actually check as policy, run it in audit mode alongside the gate, then retire the gate.
- Related: [where policy as code belongs in a platform](./what-is-policy-as-code-and-where-does-it-belong-in-a-platform.md) and [admission control as a platform lever](../kubernetes-platform/what-is-admission-control-and-how-do-you-use-it-as-a-platform-lever.md).

---

[⬅ Back to Policy as Code and Governance](./README.md) · [All topics](../README.md)
