---
title: "What is admission control and how do you use it as a platform lever?"
id: 59
category: "Kubernetes Platform"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - kubernetes-platform
  - interview-questions
---

# What is admission control and how do you use it as a platform lever?

**Short answer:** Admission control is the point in the API server's request path where a request can be modified or rejected after authentication and authorisation but before persistence. For a platform team it is the most powerful lever available, because it is the one place where a rule applies to every object regardless of how it arrived - through the platform interface, a pipeline, or `kubectl` by hand. Mutating webhooks inject defaults; validating webhooks enforce requirements.

## Detail

**Where it sits, and why order matters.** A request passes authentication, then authorisation, then mutating admission, then schema validation, then validating admission, then persistence. Mutating runs before validating, which is exactly what you want: inject the defaults first, then check the result. A rule that injects resource requests and a rule that rejects Pods without them therefore work together rather than conflicting.

**The two kinds, and what each is for:**

| Kind       | Can change the object | Platform use                                                           |
| ---------- | --------------------- | ---------------------------------------------------------------------- |
| Mutating   | Yes                   | Inject sidecars, defaults, labels, security context, tolerations       |
| Validating | No - accept or reject | Require ownership labels, signed images, resource limits, no `:latest` |

**Why it beats every other enforcement point.** Policy in a pipeline is bypassable by anyone who applies directly. Policy in a template only applies to things created from the template. Policy in review depends on a human noticing. Admission control is in the API server's path, so nothing reaches etcd without passing it. That is why security and compliance controls belong here and not in CI alone - though CI checks are still valuable for giving fast feedback before the change reaches a cluster.

**The failure policy decision is the most consequential setting.** `failurePolicy: Ignore` means requests proceed if the webhook is unreachable - the policy is silently not enforced. `failurePolicy: Fail` means requests are rejected - and if that webhook covers Pods, an outage of it prevents every Pod in the cluster from starting, including the ones that would repair it. Both choices are defensible, and `Fail` is right for controls you must never bypass, but only with the webhook made genuinely highly available, its own namespace excluded via `namespaceSelector`, and a documented break-glass procedure to remove the configuration.

**Scope narrowly.** A webhook matching every resource and every operation adds latency to every API call and enlarges the blast radius enormously. Match only the resources, operations, and namespaces you need, and set a short timeout - the API server waits for you, so a slow webhook is a slow cluster.

**Prefer built-in policy engines over custom webhooks.** Kyverno and Gatekeeper are mature, expose policies as declarative resources, and support audit-before-enforce and generation of resources. Kubernetes also has native ValidatingAdmissionPolicy using CEL (GA since 1.30), which runs in-process - no webhook to keep available, so no fail-closed outage risk. Its mutating counterpart, MutatingAdmissionPolicy, reached GA in 1.36, so common defaulting - labels, security context, tolerations - no longer needs a webhook either. For anything expressible in CEL, native policy is now the lowest-risk option and worth naming. The engines are converging on the same model: Kyverno now offers CEL-based policy types alongside its classic `ClusterPolicy`, and Gatekeeper can generate native policies from its templates.

**Always audit before enforcing.** Run a new policy in audit mode, count the violations, fix or exempt them, then switch to enforce. Turning on a policy that instantly rejects a quarter of existing workloads is a self-inflicted outage, and it is the most common way platform teams lose credibility with tenants.

## Example

```yaml
# Native Validating Admission Policy - CEL, in-process, no webhook to keep
# highly available. The lowest-risk enforcement point for anything expressible
# this way, because there is no fail-closed outage mode.
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata: { name: require-owner-and-resources }
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps"]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["deployments", "statefulsets"]
  validations:
    - expression: "has(object.metadata.labels) && 'platform.example.com/owner' in object.metadata.labels"
      message: "every workload must carry a platform.example.com/owner label"
      reason: Invalid
    - expression: >
        object.spec.template.spec.containers.all(c,
          has(c.resources) && has(c.resources.requests) &&
          'memory' in c.resources.requests && 'cpu' in c.resources.requests)
      message: "every container must set cpu and memory requests"
    - expression: >
        object.spec.template.spec.containers.all(c, !c.image.endsWith(':latest'))
      message: "image tags must be immutable - :latest is not deployable"
---
# A policy does nothing until bound. The binding is also where audit-before-
# enforce lives: start with [Audit], switch to [Deny] once violations are zero.
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata: { name: require-owner-and-resources-tenants }
spec:
  policyName: require-owner-and-resources
  validationActions: [Deny] # was [Audit] for the first three weeks
  matchResources:
    namespaceSelector:
      matchLabels: { platform.example.com/tenant: "true" }
```

```yaml
# Mutating: inject the defaults so tenants do not have to know them.
# Runs BEFORE validation, so the policy above sees the injected values.
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: inject-platform-defaults }
spec:
  rules:
    - name: harden-pod-security
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
      # `+()` adds only when absent - a team that deliberately set a value keeps
      # it, and the deviation is then visible in review rather than overwritten.
```

```text
The rollout that avoids a self-inflicted outage:

  Week 1  policy in Audit. 218 workloads scanned.
            violations: 41 missing owner label, 63 missing resource requests,
                        7 using :latest
  Week 2  mutating policy injects defaults -> resource-request violations 63 -> 4
          owner label backfilled from the catalogue -> 41 -> 0
  Week 3  11 remaining violations: PRs raised, 9 merged, 2 exempted with expiry
  Week 4  switch to Enforce. New violations impossible; existing ones are zero.

  The alternative - enabling Enforce in week 1 - rejects 111 workloads on their
  next deploy, and the platform team spends a month rebuilding trust.
```

## Interview tips

- Place it precisely in the request path and note that mutating runs before validating. That ordering is a favourite follow-up.
- The argument that admission control is unbypassable - unlike pipeline checks, templates, or review - is why it is the platform's strongest lever. Say it explicitly.
- The `failurePolicy` discussion is where seniority shows. Describe the fail-closed outage scenario, then the three mitigations: high availability, excluding its own namespace, and a documented break-glass.
- Naming native ValidatingAdmissionPolicy with CEL, and why in-process evaluation removes the fail-closed risk, is current and high signal - as is knowing that MutatingAdmissionPolicy went GA in 1.36, and that a policy needs a binding before it does anything.
- Always volunteer audit-before-enforce with numbers. It is the difference between a policy rollout and an incident.

---

[⬅ Back to Kubernetes Platform](./README.md) · [All topics](../README.md)
