---
title: "What is the shared responsibility model for a platform?"
id: 122
category: "Platform Security"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-security
  - interview-questions
---

# What is the shared responsibility model for a platform?

**Short answer:** The shared responsibility model says who secures which layer. Cloud providers popularised it: they secure the physical data centres, hypervisors, and managed service internals, and the customer secures what they build on top. An internal platform adds a middle layer - the platform team takes over a large slice of the customer's side (clusters, base images, identity plumbing, network defaults), and application teams keep what only they can own: their code, their dependencies, their data, and how their service is configured. Writing that split down explicitly is what prevents gaps nobody owns.

## Detail

**The original cloud version.** With infrastructure as a service, the provider secures the hardware and virtualisation; you secure the operating system, network rules, identities, and data. With a managed service, such as a managed Kubernetes control plane or a managed database, the line moves up: the provider runs and patches more, and you configure less. A common phrase is that the provider is responsible for security _of_ the cloud, and the customer for security _in_ the cloud. The customer never gives away responsibility for identity and access, or for their own data.

**A platform adds a third party to the split.** From an application team's point of view, the internal platform is a provider too. The model becomes three layers:

| Layer                 | Cloud provider         | Platform team                                    | Application team                            |
| --------------------- | ---------------------- | ------------------------------------------------ | ------------------------------------------- |
| Physical, hypervisor  | Owns                   | -                                                | -                                           |
| Managed control plane | Runs and patches       | Configures, upgrades versions, audits            | -                                           |
| Nodes and base images | Supplies images        | Patches, rebuilds, hardens                       | Rebuilds when asked (ideally automated)     |
| Identity              | Provides the mechanism | Wires federation, generates scoped roles         | Declares what the service needs             |
| Network               | Provides primitives    | Default-deny policies, ingress, TLS              | Declares which services it talks to         |
| Supply chain          | -                      | Build templates, signing, admission verification | Keeps dependencies current                  |
| Application code      | -                      | Offers scanning in the golden path               | Owns vulnerabilities and fixes              |
| Data                  | Encryption primitives  | Encryption on by default, backups available      | Classification, retention, access decisions |
| Incident response     | For its own services   | Platform-level detection and fleet-wide response | Their service's response and fixes          |

The exact split varies. What must not vary is that every row has an owner.

**Why the platform team takes on so much.** A platform exists so that each team does not solve the same problem forty times. Patching nodes, wiring workload identity, and verifying image signatures are the same work for everyone, done better once by a specialist team. Taking them over is also a security gain: a control applied by the platform to every workload is more reliable than the same control requested from forty teams.

**What the platform cannot take over.** It cannot fix a SQL injection in a team's code, decide how long customer data is kept, or know that a service handles payment card data unless the team says so. Those responsibilities stay with the team that understands the business context. A platform that implies otherwise creates false confidence.

**Where it goes wrong: the gaps between layers.** Incidents tend to happen in rows nobody wrote down. Typical examples:

- The platform provides a secrets store, but nobody owns rotating the secrets in it.
- The platform patches base images, but a team pinned an old base and nobody noticed.
- A team is given an escape hatch - their own cluster or a raw cloud account - and assumes the platform still covers it. It does not.
- Third-party images such as vendor agents fall between the platform and the team that asked for them.

**Make it explicit and visible.** Write the matrix down, publish it in the developer portal, and make it part of onboarding. Where possible, turn it into data: each service in the catalogue records its owner, its data classification, and which platform defaults it has opted out of. An opt-out is fine, but it moves that row's responsibility to the team, and the record should say so.

**Trade-off.** The more the platform owns, the more it is on the hook, and the more a single platform mistake affects every tenant. The benefit - consistent controls everywhere - is worth it, but it means the platform team's own changes need the same rigour as production changes.

## Example

```yaml
# A service's catalogue entry records the split for that service, including
# the defaults it has opted out of - which moves responsibility to the team.
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: checkout
  annotations:
    platform.example.com/data-classification: confidential-pci
    platform.example.com/base-image: platform-managed # platform patches it
    platform.example.com/network-policy: platform-default-deny
    platform.example.com/opt-outs: "read-only-root-filesystem"
    platform.example.com/opt-out-owner: team-payments # their row now
    platform.example.com/opt-out-review: "2027-03-31"
spec:
  type: service
  lifecycle: production
  owner: team-payments
```

```text
The questions that reveal a gap, asked per service:

  who patches the OS in this image? ............ platform (managed base)   ok
  who rotates the payment-provider API key? ... ???                          <-- gap
  who is paged if the WAF blocks real traffic? . platform on-call           ok
  who decides the retention of order data? ..... team-payments              ok
  who owns the vendor fraud agent image? ....... ???                         <-- gap

  Two unowned rows. Neither is a technology problem; both are how incidents
  start.
```

## Interview tips

- Start with the cloud version in one sentence - security of the cloud versus in the cloud - then show how an internal platform inserts a third layer. That is the platform-specific insight.
- Name the user: application teams get a smaller, clearer set of things to own, and they need to know exactly where that set starts.
- Give concrete examples of what the platform cannot own: application vulnerabilities, data retention decisions, business context.
- Focus on gaps between layers - secrets rotation, pinned base images, escape hatches, third-party images. Interviewers are testing whether you think about the seams.
- Say the matrix must be written down and visible, and that opting out of a platform default moves responsibility to the team.
- A good follow-up link is [threat modelling a platform](./how-do-you-threat-model-a-platform.md) and [keeping base images patched](./how-do-you-keep-base-images-patched-across-every-team.md).

---

[⬅ Back to Platform Security](./README.md) · [All topics](../README.md)
