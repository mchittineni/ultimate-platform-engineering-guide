---
title: "What is policy as code and where does it belong in a platform?"
id: 74
category: "Policy as Code and Governance"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - policy-as-code-and-governance
  - interview-questions
---

# What is policy as code and where does it belong in a platform?

**Short answer:** Policy as code means expressing organisational rules as versioned, tested, executable artefacts rather than as documents people are expected to follow. In a platform it belongs at three points that do different jobs: in the editor and CI for fast feedback, at admission for unbypassable enforcement, and as a continuous audit of what is already running. Only the admission point actually enforces; the other two exist so that enforcement is rarely the thing that stops someone.

## Detail

**The problem it solves.** A written standard - "all production data must be encrypted at rest", "every workload must declare an owner" - is only as good as the reviewer who remembers to check it. Expressed as code, it is checked identically every time, cannot be forgotten, and produces evidence automatically. That last property is why compliance programmes care about it as much as security teams do.

**The three enforcement points and their division of labour:**

| Point               | Speed of feedback | Bypassable | Role                                     |
| ------------------- | ----------------- | ---------- | ---------------------------------------- |
| Editor / pre-commit | Instant           | Yes        | Teach, catch typos                       |
| CI / pull request   | Minutes           | Yes        | Fail the build with a good error message |
| **Admission**       | At apply time     | **No**     | The actual enforcement boundary          |
| Continuous audit    | After the fact    | n/a        | Find what predates the policy or drifted |

**Fast feedback and enforcement are not the same job, and you need both.** Admission control is unbypassable but gives feedback late and in a context - a rejected apply during a deploy - where it is most disruptive. CI checks are bypassable but tell a developer at review time, with room to explain. Running the same policy bundle at both points means the CI failure is a reliable predictor of the admission decision, which is what makes the guardrail feel helpful rather than obstructive.

**Continuous audit covers what enforcement cannot.** Admission only sees new and updated objects. Everything created before the policy existed, and anything that drifted, needs a scheduled evaluation of live state. Without it, "the policy is enforced" is true only of recent changes.

**Guardrail versus gate is the design distinction worth naming.** A guardrail prevents a bad state - it applies automatically and does not require anyone to decide. A gate stops progress until someone acts. Prefer guardrails: mutate the workload to add the missing security context rather than rejecting it. Reserve rejection for things you genuinely cannot fix automatically, and reserve human gates for the small set of decisions that need judgement.

**Policies are code and need the discipline of code.** Version control, review, unit tests with allowed and denied fixtures, and staged rollout. An untested policy is a production change with cluster-wide reach, and a policy that rejects a valid manifest is an outage of your deployment path.

**The error message is part of the policy.** "Denied by policy require-resources" produces a support ticket. "Container `api` has no memory request, so it runs as BestEffort and is evicted first under pressure - add `resources.requests.memory` (the platform default is 128Mi)" produces a fix. Insisting on this is one of the highest-return, lowest-effort practices available.

**Keep policy about properties the platform can assert.** Encryption, ownership labels, image provenance, resource requests, no public exposure. Policies encoding taste - naming conventions beyond what tooling needs, preferred libraries - generate friction disproportionate to their value.

## Example

```yaml
# One policy, evaluated at three points. The same bundle in CI and at admission
# means a CI pass reliably predicts the admission decision.
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-owner-label
  annotations:
    policies.kyverno.io/description: >
      Every workload maps to a team that exists, so alerts route, costs
      attribute, and CVE response has someone to contact.
spec:
  validationFailureAction: Enforce
  background: true # ALSO evaluate existing resources - the continuous audit
  rules:
    - name: owner-label-present
      match:
        any: [{ resources: { kinds: [Deployment, StatefulSet, CronJob] } }]
      validate:
        # The message is part of the policy: it names the field and the fix.
        message: >-
          Missing `platform.example.com/owner`. Alerts cannot be routed and cost
          cannot be attributed without it. Set it to your team's group, e.g.
          `group:team-payments`. The golden path scaffold adds this for you.
        pattern:
          metadata:
            labels:
              platform.example.com/owner: "group:team-*"
```

```yaml
# Guardrail, not gate: fix it rather than rejecting it. `+()` adds only when
# absent, so a team's deliberate value survives and remains visible in review.
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: default-security-context }
spec:
  rules:
    - name: harden-by-default
      match:
        any: [{ resources: { kinds: [Pod], namespaces: ["team-*"] } }]
      mutate:
        patchStrategicMerge:
          spec:
            securityContext:
              +(runAsNonRoot): true
              +(seccompProfile): { type: RuntimeDefault }
            containers:
              - (name): "*"
                securityContext:
                  +(allowPrivilegeEscalation): false
                  +(readOnlyRootFilesystem): true
                  +(capabilities): { drop: ["ALL"] }
```

```yaml
# Policies are code: fixtures for both outcomes, run in CI before any rollout.
# policies/tests/require-owner-label_test.yaml
apiVersion: cli.kyverno.io/v1alpha1
kind: Test
metadata: { name: require-owner-label }
policies: [../require-owner-label.yaml]
resources: [fixtures/deployments.yaml]
results:
  - policy: require-owner-label
    rule: owner-label-present
    resources: [checkout] # has a valid owner label
    result: pass
  - policy: require-owner-label
    rule: owner-label-present
    resources: [no-owner] # missing entirely
    result: fail
  - policy: require-owner-label
    rule: owner-label-present
    resources: [malformed-owner] # "payments" - does not match group:team-*
    result: fail
```

## Interview tips

- Give the three enforcement points and be explicit that only admission actually enforces. Candidates who name only one point are usually missing either the feedback or the audit side.
- "The same bundle in CI and at admission" is the practical detail that makes guardrails feel helpful: a CI pass predicts the admission outcome.
- Continuous audit for pre-existing resources is the gap most people forget - admission only ever sees new and changed objects.
- Guardrail versus gate, with mutation preferred over rejection, is the design principle interviewers are listening for. Fix it rather than refusing it.
- Insist that the error message is part of the policy, and give a before-and-after. It is the cheapest way to make policy popular rather than resented.
- Policies need tests with both allowed and denied fixtures. An untested policy is a cluster-wide production change and can take out your deployment path.

---

[⬅ Back to Policy as Code and Governance](./README.md) · [All topics](../README.md)
