---
title: "What is a VPC and how should a platform design one on AWS?"
id: 149
category: "AWS Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - aws-platform-engineering
  - interview-questions
---

# What is a VPC and how should a platform design one on AWS?

**Short answer:** A Virtual Private Cloud is a logically isolated network in one AWS region, with an IP address range you choose, divided into subnets that each live in a single availability zone. Route tables decide where traffic goes, gateways connect it to the internet or other networks, and security groups filter traffic to each network interface. A platform should design VPCs as a standard product: address ranges allocated centrally so they never overlap, the same subnet tiers across three zones in every account, private placement for workloads by default, and egress and connectivity handled centrally rather than rebuilt by each team.

## Detail

**The building blocks.**

| Component        | What it does                                                                                   |
| ---------------- | ---------------------------------------------------------------------------------------------- |
| CIDR block       | The VPC's address range, for example `10.42.16.0/20`; secondary ranges can be added later      |
| Subnet           | A slice of that range in one availability zone; "public" or "private" is decided by its routes |
| Route table      | Per-subnet rules: local traffic, a default route to an internet or NAT gateway, TGW routes     |
| Internet gateway | Lets subnets with a route to it reach the internet and be reached from it                      |
| NAT gateway      | Lets private subnets make outbound connections without being reachable inbound                 |
| Security group   | Stateful allow-list attached to network interfaces; can reference other security groups        |
| Network ACL      | Stateless allow/deny rules at the subnet boundary; a coarse backstop                           |
| VPC endpoint     | Private path to AWS services: gateway endpoints for S3 and DynamoDB, interface endpoints else  |

A subnet is public only because its route table sends `0.0.0.0/0` to an internet gateway. That is the single most useful fact for reasoning about VPC exposure.

**Why the platform owns this, not each team.** A product team deploying a service should not have to choose a CIDR, work out subnet sizes, or decide how egress works - and if they do, every account ends up different. The users of the VPC product are the product teams who deploy into it and the platform's own automation (clusters, databases, load balancers) that needs predictable subnets to target. They should get a working network with their account, not a design exercise.

**Design principles that hold up.**

- **Allocate address space centrally.** Every VPC that may ever connect to another - through a transit gateway, peering, or a VPN - must have a non-overlapping range. Use Amazon VPC IPAM or an equivalent pool and let automation assign ranges; never let people pick. Overlaps are extremely painful to fix once workloads exist.
- **Size for Kubernetes.** With the default Amazon VPC CNI, every Pod gets a real VPC IP address, so an EKS cluster consumes addresses far faster than the node count suggests. Give workload subnets generous ranges, and know the escape valves: prefix delegation, and a secondary CIDR (often from `100.64.0.0/10`) used only for Pods.
- **Use consistent tiers across three zones.** Public subnets hold only load balancers and NAT; private subnets hold workloads; isolated subnets (no internet route at all) hold databases. Three availability zones is the usual default for zonal resilience.
- **Default to private.** Workloads never get public IPs. Inbound traffic arrives through load balancers in public subnets; outbound goes through NAT or, better, VPC endpoints.
- **Centralise egress and connectivity.** A transit gateway connects account VPCs to a shared network account with central NAT, inspection, and hybrid connectivity. This avoids a NAT gateway in every account and gives one place to filter outbound traffic.
- **Add endpoints for heavy AWS traffic.** Gateway endpoints for S3 and DynamoDB are cheap to add and keep that traffic off NAT. Interface endpoints for ECR, STS, and CloudWatch help private clusters and reduce NAT data processing.
- **Turn on flow logs** so that "is traffic even arriving?" has an answer during an incident.

**Security groups are the day-to-day control.** They are stateful, so allowing inbound 443 automatically allows the reply. Their most useful feature is referencing another security group rather than an IP range: "the database accepts 5432 from the checkout service's security group" survives scaling and IP changes.

**The trade-offs.** A centralised network is cheaper and more governable but introduces a shared dependency: a mistaken transit gateway route can affect many accounts, so changes need review and staged rollout. Large subnets waste address space; small ones run out during a scale event. And cross-zone traffic and NAT processing are metered, which is why endpoint and topology choices show up on the bill. For the shared-network alternative on another cloud, compare [GCP Shared VPC](../gcp-platform-engineering/how-do-you-design-shared-vpc-for-a-multi-team-gcp-platform.md).

## Example

```text
The standard VPC every workload account receives (eu-west-1, /20 from IPAM).

  VPC checkout-prod   10.42.16.0/20        secondary 100.64.0.0/16 (pods only)

               eu-west-1a        eu-west-1b        eu-west-1c
  public       10.42.16.0/26     10.42.16.64/26    10.42.16.128/26   ALB/NLB only
  private      10.42.20.0/22     10.42.24.0/22     10.42.28.0/22     nodes, services
  isolated     10.42.17.0/26     10.42.17.64/26    10.42.17.128/26   databases
  pods         100.64.0.0/18     100.64.64.0/18    100.64.128.0/18   VPC CNI custom networking

  routes
    public    0.0.0.0/0 -> internet gateway
    private   0.0.0.0/0 -> transit gateway -> network-prod central NAT + inspection
    isolated  no default route
  endpoints   gateway: S3, DynamoDB   interface: ECR api/dkr, STS, logs
  flow logs   on, to the log-archive account
```

```hcl
# Most of that expressed with the community VPC module. In the platform it is
# wrapped in an account-vending customisation, so no team writes this file.
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.0"

  name = "checkout-prod"
  cidr = "10.42.16.0/20" # assigned from IPAM by the vending pipeline

  azs              = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
  public_subnets   = ["10.42.16.0/26", "10.42.16.64/26", "10.42.16.128/26"]
  private_subnets  = ["10.42.20.0/22", "10.42.24.0/22", "10.42.28.0/22"]
  database_subnets = ["10.42.17.0/26", "10.42.17.64/26", "10.42.17.128/26"]

  enable_nat_gateway = false # egress is central, via the transit gateway
  enable_flow_log    = true

  # Lets the load balancer controller discover where to place load balancers.
  public_subnet_tags  = { "kubernetes.io/role/elb" = 1 }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = 1 }
}
```

## Interview tips

- Start with the definition - regional, isolated, subnets per zone - then say "public" is just a route to an internet gateway. It shows you reason from mechanism.
- Central, non-overlapping address allocation is the detail that marks experience. Say why: overlaps break transit gateway routing and cannot be fixed cheaply later.
- Mention the EKS address-consumption issue and the remedies (prefix delegation, secondary CIDR). It is a common production surprise.
- Distinguish security groups (stateful, per interface, can reference each other) from network ACLs (stateless, per subnet).
- Frame the VPC as a platform product delivered with the account, and connect it to [account vending](./what-is-account-vending-and-how-do-you-automate-it.md) and [network isolation between tenants](../multi-tenancy-and-isolation/how-do-you-isolate-tenants-at-the-network-layer.md).

---

[⬅ Back to AWS Platform Engineering](./README.md) · [All topics](../README.md)
