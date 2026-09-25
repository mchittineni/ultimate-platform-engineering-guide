---
title: "How is a VPC on GCP different from one on AWS?"
id: 176
category: "GCP Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - gcp-platform-engineering
  - interview-questions
---

# How is a VPC on GCP different from one on AWS?

**Short answer:** A GCP VPC is a global resource whose subnets are regional, whereas an AWS VPC is regional and its subnets live in a single Availability Zone. That one difference cascades: a single GCP VPC can span every region without peering or a transit hub, firewall rules apply to the whole VPC and target instances by service account or tag rather than being attached to subnets or interfaces, and there are no route tables per subnet, NACLs, or internet gateway resources to manage. Both are private software-defined networks, but GCP's has fewer moving parts and AWS's gives you more places to put controls.

## Detail

**Scope is the root difference.**

| Concept            | GCP                                                                  | AWS                                                                                |
| ------------------ | -------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| VPC                | Global - one VPC can have subnets in every region                    | Regional - one VPC per region; cross-region needs peering or a transit hub         |
| Subnet             | Regional - spans all zones in its region                             | Zonal - one subnet per Availability Zone, so several per tier                      |
| Address space      | Defined per subnet; no VPC-level CIDR block; subnets can be expanded | VPC CIDR block(s) first, subnets carved out of it; subnets cannot be resized       |
| Firewalling        | Stateful firewall rules or policies on the VPC, targeting instances  | Security groups on interfaces, plus stateless NACLs on subnets                     |
| Routing            | VPC-wide routes; no per-subnet route tables                          | Route tables associated with subnets                                               |
| Internet egress    | A default route and an external IP, or Cloud NAT                     | An internet gateway and public subnets, or NAT gateways, conventionally one per AZ |
| Sharing            | Shared VPC: host project shares subnets with service projects        | AWS RAM subnet sharing with other accounts                                         |
| Private API access | Private Google Access per subnet, or Private Service Connect         | VPC endpoints (gateway and interface) per service                                  |

**Global VPC, regional subnets.** In GCP you create a VPC, then add a subnet in `europe-west1` and another in `us-east1`, and instances in both can talk over internal IPs immediately - Google's backbone carries it, with no peering, VPN, or transit gateway. On AWS the same design needs two VPCs and something to connect them. Because a GCP subnet spans every zone in its region, you also need far fewer subnets: one per region per tier rather than one per Availability Zone per tier.

**Firewalls attach to the network, not the subnet.** GCP has no security groups and no NACLs. Firewall rules - or, in newer designs, network firewall policies - are defined on the VPC and choose their targets by service account, secure tag, or network tag. Every VPC has an implied rule that denies all ingress and allows all egress. The AWS model gives you two layers, one stateful on each interface and one stateless on each subnet; GCP gives you one stateful layer that you target by identity, which is simpler but means "put this in a private subnet" is not by itself a security control.

**Internet access is a route plus an address, not a gateway resource.** A GCP VM reaches the internet if it has an external IP and the default route to the internet exists. Instances without external IPs use Cloud NAT, which is configuration on a Cloud Router rather than an appliance in a subnet, so there is no NAT appliance to place and size in each zone. "Public" and "private" subnets are not really a GCP concept - an instance is public if it has an external IP and firewall rules allow traffic to it.

**Sharing across projects or accounts.** GCP's Shared VPC lets a host project own the network while service projects place workloads in its subnets, which is the standard multi-team design - see [How do you design Shared VPC for a multi-team GCP platform?](./how-do-you-design-shared-vpc-for-a-multi-team-gcp-platform.md). AWS's closest equivalent is sharing subnets through Resource Access Manager. VPC peering exists on both clouds and is non-transitive on both.

**The default network trap.** A new GCP project gets an auto-mode `default` network with a subnet in every region and permissive firewall rules. Platforms disable it with the `compute.skipDefaultNetworkCreation` organisation policy and always use custom-mode VPCs, where you choose every range. AWS also creates default VPCs per region, and the advice is similar.

**Who uses this, and what the platform gives them.** Product teams mostly should not design networks. On GCP the platform owns a small number of VPCs in host projects, one per environment, and gives each team a subnet grant, a firewall policy generated from declared dependencies, and NAT and DNS that already work. Engineers coming from AWS are the other audience: the platform documentation should translate "public subnet", "security group", and "NAT gateway per AZ" into GCP terms before they rebuild AWS patterns that GCP does not need.

**The trade-off.** A global VPC is simpler, but it is also a larger single fault and policy domain: one overly broad firewall rule applies in every region at once, and address planning has to cover the whole world from the start. AWS's regional VPCs force more plumbing but contain mistakes to a region. For the AWS side in depth, see [What is a VPC and how should a platform design one on AWS?](../aws-platform-engineering/what-is-a-vpc-and-how-should-a-platform-design-one-on-aws.md).

## Example

```bash
# One custom-mode VPC with subnets in two regions - no peering required between them.
gcloud compute networks create shared-prod \
  --project=vpc-host-prod --subnet-mode=custom --bgp-routing-mode=global

gcloud compute networks subnets create snet-europe-west1-app \
  --project=vpc-host-prod --network=shared-prod --region=europe-west1 \
  --range=10.42.0.0/20 --enable-private-ip-google-access

gcloud compute networks subnets create snet-us-east1-app \
  --project=vpc-host-prod --network=shared-prod --region=us-east1 \
  --range=10.52.0.0/20 --enable-private-ip-google-access

# Outbound internet for instances with no external IP: Cloud NAT on a Cloud Router.
gcloud compute routers create rtr-europe-west1 \
  --project=vpc-host-prod --network=shared-prod --region=europe-west1
gcloud compute routers nats create nat-europe-west1 \
  --project=vpc-host-prod --router=rtr-europe-west1 --region=europe-west1 \
  --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges

# Firewall targets IDENTITY, not a subnet: only the checkout service account may
# reach the pricing service account on 8080.
gcloud compute firewall-rules create allow-checkout-to-pricing \
  --project=vpc-host-prod --network=shared-prod --direction=INGRESS \
  --action=ALLOW --rules=tcp:8080 \
  --source-service-accounts=sa-checkout@checkout-prod.iam.gserviceaccount.com \
  --target-service-accounts=sa-pricing@pricing-prod.iam.gserviceaccount.com
```

```text
The same two-region, three-zone app tier on each cloud:

  AWS                                   GCP
  2 VPCs (one per region)               1 VPC (global)
  6 subnets (one per AZ per region)     2 subnets (one per region)
  2+ route tables, 2 NACLs              0 - routes are VPC-wide, no NACLs
  NAT gateways, typically one per AZ    2 Cloud NAT configs (one per region)
  1 peering or Transit Gateway          0 - the backbone connects regions
  security groups per interface         firewall rules targeting service accounts
```

## Interview tips

- Say the root difference first: GCP VPCs are global with regional subnets; AWS VPCs are regional with zonal subnets. Then derive the consequences rather than listing them as trivia.
- Explain that GCP has no security groups or NACLs - firewall rules live on the VPC and target instances by service account or tag - and that "private subnet" is not a security control on GCP.
- Mention Cloud NAT being configuration on a Cloud Router, not a per-zone appliance, and that subnets can be expanded but never shrunk.
- Bring in the default network and `compute.skipDefaultNetworkCreation`; it shows you have run GCP in an organisation, not just a sandbox.
- Offer the trade-off honestly: global simplicity versus a larger blast radius for a bad firewall rule.
- A natural follow-up is multi-team design; be ready to move to Shared VPC and subnet-level `compute.networkUser` grants.

---

[⬅ Back to GCP Platform Engineering](./README.md) · [All topics](../README.md)
