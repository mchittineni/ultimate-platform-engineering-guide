---
title: "What is the difference between audit mode and enforce mode for a policy?"
id: 136
category: "Policy as Code and Governance"
difficulty: "Beginner"
tags:
  - platform-engineering
  - policy-as-code-and-governance
  - interview-questions
---

# What is the difference between audit mode and enforce mode for a policy?

**Short answer:** In audit mode a policy is evaluated and its violations are recorded, but the change is allowed through. In enforce mode the same violation blocks the change. Audit mode is how you learn what a policy would break before it breaks anything, and most engines add a third option, warn, which allows the change but shows the violation to the person making it. A new policy should almost always start in audit, move through warn, and reach enforce only once the violation count is close to zero.

## Detail

**It is one policy with two outcomes.** The rule, the match scope, and the evaluation are identical in both modes. Only the action on failure changes: record it, or reject it. That is what makes audit mode a reliable rehearsal. The number of violations you see in audit is the number of rejections you would get in enforce.

**The same idea goes by different names in each tool:**

| Tool                                 | Audit          | Warn         | Enforce         |
| ------------------------------------ | -------------- | ------------ | --------------- |
| Kubernetes ValidatingAdmissionPolicy | `Audit`        | `Warn`       | `Deny`          |
| Kubernetes Pod Security Admission    | `audit` label  | `warn` label | `enforce` label |
| Kyverno (CEL policy types)           | `Audit`        | `Warn`       | `Deny`          |
| Gatekeeper                           | `dryrun`       | `warn`       | `deny`          |
| Azure Policy                         | `audit` effect | n/a          | `deny` effect   |

**Where audit results go matters, because a finding nobody sees is worthless.** A native ValidatingAdmissionPolicy with the `Audit` action writes the failure into the Kubernetes API server audit log as an annotation, so you only see it if you collect and query that log. Kyverno writes PolicyReport resources you can list with `kubectl`. Gatekeeper records violations in each constraint's status. Before switching anything on, decide where the findings will be read and by whom.

**Warn is the underused middle step.** With `Warn`, `kubectl` and most deploy tools print the violation to the developer at apply time, but the change still succeeds. It tells the team directly, in their own terminal or pipeline log, weeks before enforcement. It is the cheapest form of communication a platform team has.

**Admission audit is not the same as auditing existing resources.** Audit at admission only sees objects as they are created or updated. A deployment that has not changed in a year never passes through admission and never appears in the count. To size a rollout properly you also need a background scan of everything that already exists. Kyverno and Gatekeeper both run one; for native policies you need a separate tool or a CLI run against the live cluster. See [preventive and detective controls](./what-is-the-difference-between-preventive-and-detective-controls.md).

**Who this protects.** Application teams, first. Enforcing a new rule on day one means some team's next production deploy fails for a reason nobody told them about. Starting in audit lets the platform team find those workloads, fix the ones it can automatically, and contact the owners of the rest, so enforcement is a non-event. It also protects the platform team from its own mistakes: audit mode is where you discover that a policy has a false positive against a system component.

**The trade-off.** Audit mode is not a control. A policy left in audit indefinitely documents a problem without stopping it, and "audit for now" can quietly become permanent. Give every audit-mode policy a target enforcement date and an owner, and track the violation count towards zero. The reverse risk also exists: an enforce-mode policy needs a fast way back to audit if it starts rejecting things nobody predicted, and that switch should be a normal, reviewed configuration change.

## Example

```yaml
# A native Kubernetes policy (admissionregistration.k8s.io/v1, GA since 1.30).
# The policy defines the rule; the binding defines the mode. Changing the mode is
# a one-line change to the binding.
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: require-memory-requests
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps"]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["deployments"]
  validations:
    - expression: >-
        object.spec.template.spec.containers.all(c,
          has(c.resources) && has(c.resources.requests) &&
          'memory' in c.resources.requests)
      messageExpression: >-
        'Deployment ' + object.metadata.name + ' has a container with no memory
        request, so it can be evicted first under node pressure. Set
        resources.requests.memory - see go/platform-resources.'
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: require-memory-requests
spec:
  policyName: require-memory-requests
  # Phase 1: [Audit]          record only, in the API server audit log
  # Phase 2: [Warn, Audit]    also show the developer at apply time
  # Phase 3: [Deny]           enforce (Deny and Warn cannot be combined)
  validationActions: [Warn, Audit]
  matchResources:
    namespaceSelector:
      matchLabels:
        platform.example.com/tenant: "true"
```

```text
What the developer sees in phase 2 - the change succeeds, but they have been told:

$ kubectl apply -f deploy.yaml
Warning: Validation failed for ValidatingAdmissionPolicy 'require-memory-requests'
with binding 'require-memory-requests': Deployment reporting-api has a container
with no memory request, ...
deployment.apps/reporting-api configured
```

```text
A typical progression for one policy:

  week 1   Audit       41 violations at admission, plus 63 found by a background
                       scan of existing workloads
  week 2   Audit       platform mutation adds defaults; 104 -> 12
  week 3   Warn+Audit  12 owning teams see the warning on their next deploy
  week 5   Warn+Audit  2 left, both with dated exceptions
  week 6   Deny        enforced; zero unexpected rejections
```

## Interview tips

- Say clearly that it is the same rule with a different action on failure. That is why audit mode is an accurate rehearsal for enforcement.
- Mention the third mode, warn, and why it is valuable: it tells the developer directly, at apply time, without blocking them.
- Point out that admission audit only sees changes, so you also need a background scan of existing resources to size a rollout properly. This is the detail most candidates miss.
- Know where each tool puts audit results: API server audit log annotations for native policies, PolicyReports for Kyverno, constraint status for Gatekeeper.
- Warn that audit mode is not a control. Every audit-mode policy needs an owner and an enforcement date, or it becomes permanent documentation of a problem.
- For the full sequence at scale, see [rolling out a new policy without breaking every team](./how-do-you-roll-out-a-new-policy-without-breaking-every-team.md).

---

[⬅ Back to Policy as Code and Governance](./README.md) · [All topics](../README.md)
