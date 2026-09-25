---
title: "What is the difference between multi-cloud and hybrid cloud?"
id: 185
category: "Multi-Cloud and Hybrid Platforms"
difficulty: "Beginner"
tags:
  - platform-engineering
  - multi-cloud-and-hybrid-platforms
  - interview-questions
---

# What is the difference between multi-cloud and hybrid cloud?

**Short answer:** Multi-cloud means running workloads on more than one public cloud provider - say AWS and Google Cloud. Hybrid cloud means running workloads across your own infrastructure (a data centre, a factory floor, a private cloud) and at least one public cloud, connected so they operate as one estate. The two are independent: an organisation can be hybrid, multi-cloud, both, or neither, and each brings a different defining problem - multi-cloud multiplies provider differences, hybrid adds a network link and an estate you operate yourself.

## Detail

**Multi-cloud is about providers.** The defining feature is more than one public cloud vendor, each with its own account model, identity system, networking constructs, and managed services. The hard part is not running containers in two places - Kubernetes makes that straightforward - but that everything around the containers differs: IAM semantics, private connectivity, quotas, billing, and the managed databases your services depend on. Most organisations that call themselves multi-cloud are really one primary provider plus a contained exception, such as a data warehouse elsewhere or an acquired company's estate.

**Hybrid is about ownership and location.** The defining feature is that part of the estate runs on infrastructure you own or control, alongside a public cloud. The usual reasons are regulatory (data that must stay on owned hardware), physical (machines in a factory or hospital that need local compute), or economic (a large existing data-centre investment). The hard part is that the on-premises side has fixed capacity, no managed services, and a network link to the cloud that has finite bandwidth and can fail.

**They combine.** A bank running a mainframe on-premises, its customer apps on Azure, and an analytics platform on Google Cloud is both hybrid and multi-cloud. The problems add up rather than overlap: you inherit provider differences from multi-cloud and link constraints from hybrid.

**The blurred middle: provider hardware on your premises.** All three major providers will run their stack in your building - AWS Outposts and EKS Hybrid Nodes, Azure Local (formerly Azure Stack HCI) managed through Azure Arc, and Google Distributed Cloud. These are hybrid in location but single-provider in control plane. They narrow the capability gap on-premises, at the cost of a provider dependency inside your data centre, and they do not remove the network link.

**Why the distinction matters to a platform team.** The words drive different designs:

| Question               | Multi-cloud                              | Hybrid                                      |
| ---------------------- | ---------------------------------------- | ------------------------------------------- |
| Defining difficulty    | Provider semantics differ                | Link between estates; you operate one side  |
| Typical driver         | Contract, acquisition, unique capability | Regulation, physical location, existing kit |
| Unifying layer         | Kubernetes, IaC, OpenTelemetry, one IdP  | The same, plus careful network design       |
| What does not unify    | IAM, networking, managed data services   | Capacity, managed services, load balancing  |
| Characteristic failure | Lowest-common-denominator abstraction    | Synchronous calls across a link that fails  |
| Who owns the hardware  | The providers                            | You, for the on-premises part               |

**Name the user.** Application teams should not have to care which of these the organisation is. The platform's job is to give them one way to declare and deploy a service, with placement as a property of the service specification, and to state plainly where capabilities differ - "on-premises Postgres is platform-operated and has no point-in-time recovery" - rather than hiding the difference.

**The trade-off in one sentence.** Each additional estate roughly doubles part of the platform team's surface - identity, networking, observability integration, on-call knowledge - without doubling its headcount, so both models should exist because something requires them, not because they sound resilient.

## Example

```text
Three organisations, classified.

  RETAILER
    AWS for everything; Snowflake for analytics (runs on AWS)
    -> single cloud. A SaaS product on the same provider is not multi-cloud.

  INSURER
    claims system on-premises (regulator requires owned infrastructure)
    customer portal and APIs on Azure, linked by ExpressRoute
    -> HYBRID. The link and the on-premises capability gap dominate the design.

  MANUFACTURER
    plant-floor compute in 40 factories (K3s clusters on local hardware)
    ERP and data platform on Google Cloud
    an acquired subsidiary still running on AWS
    -> HYBRID and MULTI-CLOUD. Edge sites add intermittent connectivity;
       the acquisition adds a second provider's IAM and networking.
```

```yaml
# How a platform expresses the difference to teams: placement is a property,
# not a separate deployment mechanism per estate.
apiVersion: platform.example.com/v1
kind: Service
metadata: { name: quote-engine }
spec:
  owner: group:team-pricing
  placement:
    target: cloud # on-premises | cloud | edge
    provider: azure # only meaningful where more than one provider exists
    reason: "customer-facing; no residency constraint"
  runtime:
    image: registry.example.com/quote-engine@sha256:4b1e9c...
```

## Interview tips

- Give crisp definitions first: multi-cloud is more than one public provider, hybrid is your own infrastructure plus a public cloud. Then say they are independent and can combine.
- Name the defining problem of each: provider semantics for multi-cloud, the link and the self-operated estate for hybrid. That shows you understand why the distinction matters.
- Mention the provider-on-your-premises offerings (Outposts, EKS Hybrid Nodes, Azure Arc and Azure Local, Google Distributed Cloud) as hybrid in location but single-provider in control plane.
- Point out that a SaaS product on the same provider, or a small exception, does not make an organisation meaningfully multi-cloud - a common exaggeration.
- Likely follow-up: "When is multi-cloud actually justified?" - see [When is multi-cloud a real requirement rather than a slogan?](./when-is-multi-cloud-a-real-requirement-rather-than-a-slogan.md) and, for hybrid depth, [How do you design a hybrid platform spanning on-premises and cloud?](./how-do-you-design-a-hybrid-platform-spanning-on-premises-and-cloud.md).

---

[⬅ Back to Multi-Cloud and Hybrid Platforms](./README.md) · [All topics](../README.md)
