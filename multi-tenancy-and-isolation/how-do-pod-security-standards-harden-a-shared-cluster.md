---
title: "How do Pod Security Standards harden a shared cluster?"
id: 48
category: "Multi-Tenancy and Isolation"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - multi-tenancy-and-isolation
  - interview-questions
---

# How do Pod Security Standards harden a shared cluster?

**Short answer:** Pod Security Standards define three profiles - `privileged`, `baseline`, and `restricted` - that say which pod settings are allowed, and the built-in Pod Security Admission controller enforces them per namespace through labels, in `enforce`, `audit`, or `warn` mode. In a shared cluster they close the most direct routes from one tenant's pod to the node and therefore to every other tenant: privileged containers, host namespaces, hostPath mounts, and root with added capabilities. They are a floor, not a complete policy, so platforms pair them with an admission policy engine for everything else.

## Detail

**Why pod specs are a tenancy problem.** Tenants in one cluster share nodes and the Linux kernel. A pod that runs privileged, mounts the host filesystem, or joins the host's network or PID namespace is effectively running on the node, and from the node it can reach other tenants' containers, secrets mounted into them, and the kubelet's credentials. RBAC does not help here: a tenant with ordinary `create pods` permission can ask for any of those settings unless admission stops it.

**The three profiles:**

| Profile      | Intended for                             | What it blocks (highlights)                                                                                                                                                                                                        |
| ------------ | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `privileged` | Trusted system components only           | Nothing                                                                                                                                                                                                                            |
| `baseline`   | Most workloads with minimal changes      | Privileged containers, hostNetwork/hostPID/hostIPC, hostPath volumes, host ports, adding capabilities beyond the default set, unsafe sysctls, custom `/proc` mount                                                                 |
| `restricted` | Security-sensitive and multi-tenant work | Everything in baseline, plus: must run as non-root, `allowPrivilegeEscalation: false`, drop `ALL` capabilities (only `NET_BIND_SERVICE` may be added back), seccomp `RuntimeDefault` or `Localhost`, a limited set of volume types |

`baseline` is the minimum for any tenant namespace. `restricted` is the right default for new application namespaces, because most well-built containers already comply and the few settings it demands are cheap to add in a golden-path template.

**How enforcement works.** Pod Security Admission is built into the API server and has been stable since Kubernetes 1.25, when it replaced the removed PodSecurityPolicy. You opt a namespace in with labels:

- `pod-security.kubernetes.io/enforce: <profile>` rejects violating pods.
- `pod-security.kubernetes.io/audit: <profile>` records violations in the audit log.
- `pod-security.kubernetes.io/warn: <profile>` returns a warning to the client - including when a Deployment's pod template would violate, which enforce alone does not report because enforce only checks pods.
- A matching `-version` label pins the profile to a Kubernetes minor version, so a cluster upgrade does not silently tighten the rules before you have tested them.

A cluster-wide default for unlabelled namespaces, and exemptions for specific users, runtime classes, or namespaces, can be set in the API server's admission configuration. On managed clusters where you cannot touch that file, the platform labels every namespace at creation instead.

**Rolling it out without breaking tenants.** Set `warn` and `audit` to `restricted` first while `enforce` stays at `baseline`. Teams see warnings on every `kubectl apply` and in CI, the audit log shows who is non-compliant, and a server-side dry run (`kubectl label --dry-run=server`) reports which existing pods would fail. Once warnings are gone, raise `enforce`. This is the same audit-then-enforce pattern used for any guardrail.

**What Pod Security Standards do not cover.** They are deliberately a fixed, small set of checks. They do not verify image provenance or signatures, require resource requests, forbid `latest` tags, restrict which registries are allowed, or enforce labels. They also cannot express fine-grained exceptions such as "this one DaemonSet may use hostPath `/var/log`". For those, platforms use ValidatingAdmissionPolicy (GA since Kubernetes 1.30) or an engine such as Kyverno or Gatekeeper - and keep Pod Security Admission as the always-on, zero-dependency floor, because it does not rely on a webhook that could fail open or be unavailable. See [What is admission control and how do you use it as a platform lever?](../kubernetes-platform/what-is-admission-control-and-how-do-you-use-it-as-a-platform-lever.md).

**Where it sits in the isolation picture.** Restricted pods make a container escape much harder, but they do not make the kernel a hard boundary. For genuinely untrusted code, pair restricted with a sandboxed runtime (gVisor or Kata Containers through a RuntimeClass) or dedicated nodes. User namespaces (`hostUsers: false`) are a further layer that maps root in the container to an unprivileged user on the host, and are worth enabling where your Kubernetes version and runtime support them.

**Who the user is.** Tenant teams, who mostly never see Pod Security except as a warning when a template is wrong - which is the goal. The golden-path templates should already satisfy `restricted`, so compliance is the default rather than a migration. The platform team owns the few namespaces that must run `privileged`, such as CNI or node agents, and keeps that list short and reviewed.

**The trade-off.** `restricted` breaks some off-the-shelf images that expect root or write to their own filesystem, and some third-party charts need patching. The exemption list is where hardening erodes, so every `privileged` or `baseline` namespace needs an owner and a reason.

## Example

```yaml
# Tenant namespace, generated at creation. Enforce restricted, pinned to a
# tested version; warn and audit track the latest rules ahead of upgrades.
apiVersion: v1
kind: Namespace
metadata:
  name: team-checkout
  labels:
    tenant: team-checkout
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.34
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
```

```yaml
# A container spec that passes restricted - what the golden-path template emits.
apiVersion: apps/v1
kind: Deployment
metadata: { name: api, namespace: team-checkout }
spec:
  replicas: 3
  selector: { matchLabels: { app: api } }
  template:
    metadata: { labels: { app: api } }
    spec:
      securityContext:
        runAsNonRoot: true
        seccompProfile: { type: RuntimeDefault }
      containers:
        - name: api
          image: registry.example.com/checkout/api:1.14.2
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true # not required by restricted, but cheap
            capabilities: { drop: ["ALL"] }
          resources:
            requests: { cpu: 200m, memory: 256Mi }
            limits: { memory: 512Mi }
```

```text
Testing a tightening before enforcing it:

$ kubectl label --dry-run=server --overwrite ns team-analytics \
    pod-security.kubernetes.io/enforce=restricted
Warning: existing pods in namespace "team-analytics" violate the new PodSecurity enforce level "restricted:latest"
Warning: notebook-6d9f8: allowPrivilegeEscalation != false, unrestricted capabilities, runAsNonRoot != true, seccompProfile
namespace/team-analytics labeled (server dry run)
```

## Interview tips

- Name the three profiles and the three modes, and say that Pod Security Admission replaced PodSecurityPolicy, which was removed in Kubernetes 1.25. Mentioning PSP as current is an instant dating signal.
- Explain why it matters for tenancy specifically: pod settings are the path from a tenant's container to the shared node.
- Describe the rollout - warn and audit at `restricted`, enforce at `baseline`, then raise - and the server-side dry run. That shows you have done it without an outage.
- Be clear that it is a floor. Anything beyond the fixed checks belongs in ValidatingAdmissionPolicy, Kyverno, or Gatekeeper.
- For untrusted code, say restricted is necessary but not sufficient, and add sandboxed runtimes or dedicated nodes.

---

[⬅ Back to Multi-Tenancy and Isolation](./README.md) · [All topics](../README.md)
