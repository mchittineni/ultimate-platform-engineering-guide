---
title: "How do you connect networks across clouds?"
id: 192
category: "Multi-Cloud and Hybrid Platforms"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - multi-cloud-and-hybrid-platforms
  - interview-questions
---

# How do you connect networks across clouds?

**Short answer:** Start with a single, non-overlapping address plan, then choose the transport: IPsec VPN over the internet for low volume, or private interconnects - either via a colocation or network-as-a-service provider, or the newer provider-to-provider managed interconnects - for predictable bandwidth and latency. Terminate each cloud's side in a hub (Transit Gateway, Virtual WAN, or Network Connectivity Center), exchange routes with BGP, and solve DNS as a first-class problem. Just as important is deciding what should _not_ cross: many cross-cloud needs are better served by private service endpoints or public APIs with strong identity than by flat network reachability.

## Detail

**Address planning comes first, because it is the one thing you cannot fix later.** Every VPC, VNet, on-premises range, and acquired estate needs a non-overlapping CIDR allocation from one plan. Overlaps force NAT between clouds, which breaks source-IP-based policy, complicates troubleshooting, and is extremely painful to remediate once workloads exist. Keep the plan in version control or an IPAM tool (AWS VPC IPAM, Azure Virtual Network Manager IPAM, or a neutral IPAM) and allocate from it automatically in account or subscription vending.

**Transport options, from simplest to most robust:**

| Option                                    | Bandwidth and latency                 | Setup                           | Good for                                  |
| ----------------------------------------- | ------------------------------------- | ------------------------------- | ----------------------------------------- |
| Site-to-site IPsec VPN                    | Internet-dependent; per-tunnel limits | Hours                           | Low volume, control traffic, a first link |
| Interconnect via colocation or NaaS       | Dedicated, predictable                | Weeks (physical cross-connects) | Steady, high-volume traffic               |
| Provider-to-provider managed interconnect | Dedicated, provisioned in minutes     | Console or API                  | Supported cloud pairs                     |

The traditional private path is each provider's dedicated connection - AWS Direct Connect, Azure ExpressRoute, Google Cloud Interconnect - landed in a shared colocation facility or through a network-as-a-service partner that routes between them. Google's Cross-Cloud Interconnect provisions a dedicated link from Google Cloud to other providers. The newer option is a jointly managed link: AWS Interconnect - multicloud reached general availability in April 2026 with Google Cloud as the first partner, giving a private, encrypted Layer 3 connection provisioned without physical cross-connects, with further provider partners announced. Check which pairs and regions are supported before designing around it.

**Hubs keep the topology manageable.** Connect each cloud's hub rather than meshing individual networks: AWS Transit Gateway or Cloud WAN, Azure Virtual WAN or a hub VNet, and Google Cloud Network Connectivity Center. The hubs exchange routes over BGP, so adding a spoke VPC does not mean editing static routes in three places. Keep route tables deliberately small - advertise summaries, not every subnet - and remember that each provider has route limits per table and per BGP session.

**DNS is where cross-cloud networking usually breaks.** Each cloud has private DNS zones that only its own networks can resolve. Cross-cloud resolution needs explicit forwarding: Route 53 Resolver endpoints, Azure DNS Private Resolver, and Cloud DNS forwarding or peering zones, with a clear rule for which zone is authoritative for which name. Private endpoints add a trap: a managed service's name resolves to a private IP in one cloud and a public IP elsewhere, so a caller in the other cloud may silently take the public path.

**Encryption and trust.** IPsec encrypts VPN traffic. Private interconnects are not encrypted by default unless you enable MACsec (where supported) or run IPsec over them; the managed multicloud interconnects encrypt the link. Either way, treat the network as untrusted and use TLS with workload identity for service-to-service traffic - network reachability should never be the authorisation.

**Ask whether the networks should be joined at all.** Flat routing between clouds expands the blast radius: a compromised workload in one cloud can now scan the other. Often the actual need is one service calling one API. Private service endpoints (AWS PrivateLink, Azure Private Link, Google Private Service Connect) expose a single service rather than a network, and a public API behind strong OIDC-federated identity may be simpler still. Join networks when many services need many paths; expose services when a few do.

**Operational concerns people forget:** MTU differences across tunnels (fragmentation shows up as mysterious hangs), asymmetric routing when there are two paths, egress charges for traffic leaving each provider, and monitoring each link's utilisation so a bulk transfer does not starve interactive traffic.

**Name the user.** Application teams should request connectivity as intent - "service A in Azure calls service B in AWS on 443" - through the service specification or a pull request, not by filing tickets for firewall rules. The platform team owns the address plan, the hubs, DNS forwarding, and the policy that decides whether a flow gets network reachability or a private endpoint.

## Example

A first link between AWS and Azure: an IPsec VPN with BGP from an AWS Transit Gateway to an Azure VPN gateway, using the address plan below.

```yaml
# ipam/plan.yaml - single source of truth, consumed by account and subscription vending
supernet: 10.0.0.0/8
allocations:
  onprem-dc1: 10.0.0.0/14
  aws:
    eu-west-1: 10.16.0.0/12 # carved into /20 per VPC by AWS VPC IPAM
  azure:
    westeurope: 10.32.0.0/12 # carved into /20 per spoke VNet
  gcp:
    europe-west1: 10.48.0.0/12
reserved:
  acquisitions: 10.64.0.0/10 # never allocate; for estates arriving later
bgp:
  aws-tgw-asn: 64512
  azure-vpngw-asn: 65515
  onprem-asn: 65010
```

```hcl
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}

# Azure's VPN gateway public IP and ASN, as seen from AWS.
resource "aws_customer_gateway" "azure_westeurope" {
  bgp_asn    = 65515
  ip_address = "203.0.113.10"
  type       = "ipsec.1"
  tags       = { Name = "azure-westeurope-vpngw" }
}

resource "aws_vpn_connection" "to_azure" {
  customer_gateway_id = aws_customer_gateway.azure_westeurope.id
  transit_gateway_id  = aws_ec2_transit_gateway.hub.id
  type                = "ipsec.1"
  static_routes_only  = false # exchange routes with BGP

  # Azure accepts BGP peer addresses from the 169.254.21.0 - 169.254.22.255 range
  tunnel1_inside_cidr = "169.254.21.0/30"
  tunnel2_inside_cidr = "169.254.22.0/30"
}
```

```text
Resolution path for a pod in AKS calling orders.aws.internal.example.com:

  AKS pod -> CoreDNS -> Azure DNS Private Resolver (outbound endpoint)
          -> forwarding rule: aws.internal.example.com -> 10.16.0.10, 10.16.16.10
          -> Route 53 Resolver inbound endpoint in the AWS hub VPC
          -> private hosted zone aws.internal.example.com -> 10.16.34.21
  traffic -> Azure hub -> VPN tunnel (BGP learned 10.16.0.0/12) -> TGW -> VPC

  Checks worth automating: both tunnels up, BGP routes present, the resolver
  forwarding rule answers, and the link utilisation stays under 70 per cent.
```

## Interview tips

- Lead with the address plan - non-overlapping, allocated automatically, with a reserved range for acquisitions. It signals experience.
- Compare transports by bandwidth, predictability, and setup time, and mention the newer managed provider-to-provider interconnects without overstating their coverage.
- Hubs plus BGP instead of a mesh of peerings; advertise summaries.
- Call out DNS forwarding and the private-endpoint resolution trap - that is where real cross-cloud projects stall.
- Challenge the premise: exposing one service privately, or using federated identity over a public API, is often better than joining networks. See [How do you design private networking for Azure PaaS services?](../azure-platform-engineering/how-do-you-design-private-networking-for-azure-paas-services.md) for private endpoints in depth.

---

[⬅ Back to Multi-Cloud and Hybrid Platforms](./README.md) · [All topics](../README.md)
