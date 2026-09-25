---
title: "What is least privilege and how does a platform enforce it by default?"
id: 119
category: "Platform Security"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-security
  - interview-questions
---

# What is least privilege and how does a platform enforce it by default?

**Short answer:** Least privilege means every identity - a person, a pipeline, or a running workload - holds only the permissions it needs for its job, for only as long as it needs them. A platform enforces it by generating narrowly scoped identities and roles for every service automatically, applying restrictive runtime defaults such as non-root containers, and making broader access temporary and visible rather than standing. The point is that the secure configuration is the one teams get without asking.

## Detail

**What it protects against.** Least privilege does not stop a compromise; it limits what a compromise achieves. If an attacker gets code execution in one service, the damage is bounded by what that service's identity can do. A service that can only read one bucket and write to one queue is a contained incident. A service running with an administrator role is a breach of everything that role can touch. The measure that matters is blast radius.

**It applies to four kinds of identity, not just people:**

| Identity    | Least privilege looks like                                         |
| ----------- | ------------------------------------------------------------------ |
| Humans      | Read access by default; elevated access time-bound and recorded    |
| Pipelines   | A role per repository and environment, not one shared deploy key   |
| Workloads   | One identity per service, scoped to the resources it actually uses |
| Controllers | Platform automation bounded by resource prefix, tag, or namespace  |

The last row is the one people forget. Platform controllers usually hold the broadest permissions in the organisation, so they deserve the tightest scoping.

**Why teams will not do it on their own.** Writing a narrow policy is harder than writing a broad one, and the cost of getting it wrong is visible (the service breaks) while the cost of being too broad is invisible (until an incident). Left to themselves, teams under deadline pressure reach for wildcards. That is not carelessness; it is a predictable response to the incentives. The platform's job is to change the incentives by making the narrow version the easy one.

**How a platform makes it the default:**

- **Generate identities from declarations.** A team declares "my service reads from this bucket and publishes to this topic", and the platform creates the service account, the federated cloud role, and a policy scoped to exactly those resources. Nobody writes a policy by hand, so nobody writes `"Resource": "*"`.
- **Namespace-scoped roles for tenants.** Teams get a `Role` bound in their own namespace rather than a `ClusterRole` that reaches every tenant.
- **Restrictive runtime defaults.** Enforce the Kubernetes Pod Security Standards `restricted` profile through Pod Security Admission: non-root, no privilege escalation, all Linux capabilities dropped, a seccomp profile set. Workloads that genuinely need more ask for an exemption.
- **No standing human admin.** Engineers get deep read access routinely, and elevated access through a time-bound break-glass mechanism that expires on its own.
- **Guardrails above the account.** In a cloud organisation, service control policies or organisation policies cap what any role can do, so a mistake inside one account cannot exceed the organisation's boundary.

**Measure the gap.** Permissions granted and permissions used drift apart over time. Cloud providers can report which permissions an identity has actually exercised, and comparing the two - then removing the unused ones - is the ongoing half of least privilege. Access that was needed for a one-off migration and never removed is the most common finding.

**The trade-off.** Tight permissions cause friction. A service that needs a new permission fails until someone grants it, and if that takes a ticket and three days, teams will lobby for broad roles to avoid the wait. Least privilege only survives if the path to _more_ privilege is fast and self-service - change the declaration, get a reviewed pull request, have the new permission in minutes.

## Example

```yaml
# A tenant namespace the platform creates. The Pod Security label enforces the
# restricted profile for every Pod in it - no team has to remember.
apiVersion: v1
kind: Namespace
metadata:
  name: team-payments
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
---
# The team's own access: manage workloads in their namespace, nothing else.
# Note there is no access to Secrets, and no cluster-wide scope.
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer
  namespace: team-payments
rules:
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: [""]
    resources: ["pods", "pods/log", "services", "configmaps"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer
  namespace: team-payments
subjects:
  - kind: Group
    name: team-payments-engineers # from the identity provider
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: developer
  apiGroup: rbac.authorization.k8s.io
```

```text
What the platform generated from one service declaration, versus what a team
under deadline pressure tends to write by hand:

  declared:   reads  s3://payments-invoices
              writes sqs://payments-events

  generated IAM policy                      hand-written equivalent
  s3:GetObject  on payments-invoices/*      s3:*   on *
  sqs:SendMessage on payments-events        sqs:*  on *

  If the checkout service is compromised:
    generated -> attacker can read invoices and send events. Contained.
    hand-written -> attacker can read, delete, and exfiltrate every bucket
                    and queue in the account.
```

## Interview tips

- Define it in terms of blast radius: least privilege does not prevent a compromise, it limits what the compromise can reach. That framing shows you understand why it matters.
- Cover all four identity types - humans, pipelines, workloads, and the platform's own controllers. Candidates who only mention human access miss where most privilege actually sits.
- Name the user: application teams get a working, correctly scoped identity without writing IAM policy, which is both safer and less work for them.
- Explain why wildcards happen - narrow policies are harder to write and failures are visible - and that generating policies from declarations removes the incentive.
- Say that least privilege only survives if requesting more access is fast. A slow exception path pushes teams towards broad roles.
- Expect a follow-up on how you find unused permissions; mention comparing granted against used permissions and removing the difference. For the workload side, see [workload identity](./how-does-a-platform-provide-workload-identity-without-long-lived-credentials.md) and [break-glass access](./how-do-you-design-break-glass-access-to-production.md).

---

[⬅ Back to Platform Security](./README.md) · [All topics](../README.md)
