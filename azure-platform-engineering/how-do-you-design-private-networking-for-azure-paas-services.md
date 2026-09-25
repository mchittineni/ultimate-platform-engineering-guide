---
title: "How do you design private networking for Azure PaaS services?"
id: 170
category: "Azure Platform Engineering"
difficulty: "Advanced"
tags:
  - platform-engineering
  - azure-platform-engineering
  - interview-questions
---

# How do you design private networking for Azure PaaS services?

**Short answer:** Use private endpoints so each PaaS resource gets an address inside your VNet, disable public network access on the resource, and centralise the private DNS zones in the connectivity subscription with links to every spoke - because DNS is what actually makes private endpoints work and is where almost all the failures are. The characteristic symptom of getting it wrong is a connection that resolves to a public address and is then refused.

## Detail

**Private endpoint versus service endpoint, and know the difference.** A service endpoint keeps traffic on the Azure backbone but the resource still has a public address and is reached by its public name; access control is by VNet rule on the resource. A private endpoint gives the resource a private IP in your subnet, so it is reachable by address from your network and from on-premises over your gateway, and the resource's public access can be turned off entirely. For a platform standardising on private connectivity, private endpoints are the answer; service endpoints are a lighter, weaker option.

**DNS is the whole problem.** Creating a private endpoint does not change name resolution. The resource's public FQDN must resolve to the private address, and that requires a private DNS zone for the service - `privatelink.database.windows.net`, `privatelink.blob.core.windows.net`, and one per service type - containing an A record for your endpoint, linked to the VNet doing the resolving. If any part of that is missing, the name resolves publicly, the connection is refused because public access is disabled, and the error looks like a firewall problem rather than a DNS one.

**Centralise the zones, do not create them per spoke.** The workable pattern is one set of private DNS zones in the connectivity subscription, with virtual network links to every spoke VNet, and private endpoints registering their records into those central zones automatically via a policy. Per-spoke zones produce inconsistent resolution and are unmanageable at scale. This is one of the strongest arguments for the hub-and-spoke landing zone model.

**Automate the DNS registration with policy.** A `DeployIfNotExists` policy that creates the private DNS zone group on every private endpoint means a team cannot create an endpoint that does not resolve. Without it, the most common platform support ticket becomes "my private endpoint does not work", and the answer is always the missing zone group.

**Disable public access on the resource, and enforce it.** A private endpoint alongside an open public endpoint has added a path rather than removed one. Setting `publicNetworkAccess: Disabled` and enforcing it with policy - plus setting it unconditionally in your platform modules - is what makes the design real.

**Subnet planning needs doing up front.** Private endpoints consume addresses in the subnet they occupy, some services require a dedicated delegated subnet, and address space is painful to change later. Allocate a private endpoint subnet per spoke as part of vending, sized for growth.

**Route egress through inspection deliberately.** In a Corp landing zone, outbound traffic typically routes to Azure Firewall in the hub via a route table, giving one place for egress policy and logging. That is also where a stable outbound address for third-party allowlisting comes from. Note that this makes the firewall a data-plane dependency, so it needs corresponding availability. Explicit egress is also no longer optional: Azure is retiring default outbound access, and virtual networks created with the newer network API versions (from `2025-07-01`, and in the portal since April 2026) get private subnets by default, so a VM or node without a NAT gateway, firewall route, or load balancer outbound rule simply has no internet path. Build the egress route into the vended spoke rather than relying on the old implicit behaviour.

**On-premises resolution needs the DNS path completed too.** Private endpoints are reachable from on-premises over ExpressRoute or VPN, but only if on-premises DNS forwards the relevant zones to a resolver inside Azure - today normally the inbound endpoint of an Azure DNS Private Resolver in the hub, rather than a pair of forwarder VMs you patch yourself. Forgetting this is the second most common failure after the missing zone group.

**Have an answer for services with awkward integration.** Not every Azure service supports private endpoints for every sub-resource, and some platform features behave differently when public access is disabled. Check the specific service's current support before committing a design, and record the exceptions with compensating controls rather than discovering them during implementation.

## Example

```text
The shape: endpoints in the spokes, DNS zones centralised in the hub.

  CONNECTIVITY SUBSCRIPTION (hub)
    hub VNet ......................... Azure Firewall, gateways
    Private DNS zones (ONE set for the whole estate):
        privatelink.database.windows.net
        privatelink.blob.core.windows.net
        privatelink.vaultcore.azure.net
        privatelink.postgres.database.azure.com
        privatelink.servicebus.windows.net
        ... one per service type
      each with a virtual network link to EVERY spoke VNet

  SPOKE: checkout-prod
    snet-app ......................... workloads
    snet-privatelink ................. private endpoints live here
                                       (sized for growth - addresses are consumed
                                        per endpoint and hard to change later)
    route table ...................... 0.0.0.0/0 -> Azure Firewall in the hub

  Resolution path that must work:
    workload asks for  psql-team-payments-checkout.postgres.database.azure.com
      -> spoke VNet resolver
      -> linked private DNS zone privatelink.postgres.database.azure.com
      -> A record 10.42.20.14  (the private endpoint)
      -> traffic stays inside the network

  If the zone link is missing, this resolves to a PUBLIC address, the connection
  is refused because public access is disabled, and the error looks like a
  firewall problem. That is the single most common failure in this design.
```

```bicep
// The module makes the correct design the only expressible one.
resource pg 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: 'psql-${tenant}-${workload}'
  properties: {
    network: {
      publicNetworkAccess: 'Disabled' // private endpoint ALONGSIDE public access
    } //   adds a path rather than removing one
  }
}

resource pe 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: 'pe-${tenant}-${workload}-psql'
  location: location
  properties: {
    subnet: { id: privateLinkSubnetId } // the dedicated PE subnet
    privateLinkServiceConnections: [
      {
        name: 'psql'
        properties: {
          privateLinkServiceId: pg.id
          groupIds: ['postgresqlServer']
        }
      }
    ]
  }
}

// THE PIECE THAT IS ALWAYS FORGOTTEN. Without this the endpoint exists and
// nothing resolves to it.
resource dnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = {
  parent: pe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'postgres'
        // The CENTRAL zone in the connectivity subscription, not a local one
        properties: { privateDnsZoneId: centralPostgresPrivateDnsZoneId }
      }
    ]
  }
}
```

```json
// Policy so a team cannot create a private endpoint that does not resolve.
// This one policy removes the most common platform support ticket.
{
  "properties": {
    "displayName": "Private endpoints must register in the central private DNS zone",
    "mode": "Indexed",
    "policyRule": {
      "if": { "field": "type", "equals": "Microsoft.Network/privateEndpoints" },
      "then": {
        "effect": "DeployIfNotExists",
        "details": {
          "type": "Microsoft.Network/privateEndpoints/privateDnsZoneGroups",
          "roleDefinitionIds": [
            "/providers/Microsoft.Authorization/roleDefinitions/4d97b98b-1d4f-4787-a291-c67834d212e7",
            "/providers/Microsoft.Authorization/roleDefinitions/b12aa53e-6015-4669-85d0-8515ebb3ae7f"
          ],
          "deployment": { "properties": { "mode": "incremental", "template": {} } }
        }
      }
    }
  }
}
```

## Interview tips

- Say early and clearly that DNS is where private endpoints succeed or fail, and describe the failure signature: resolves publicly, connection refused, looks like a firewall problem.
- Distinguish private endpoint from service endpoint precisely - private IP in your subnet versus a VNet rule on a still-public resource.
- Centralised private DNS zones in the connectivity subscription with links to every spoke is the pattern, and it is one of the best arguments for hub-and-spoke.
- The `DeployIfNotExists` policy creating the DNS zone group is the highest-value automation here, because it eliminates the most common support ticket entirely.
- Disabling public access is what makes the design real - a private endpoint next to an open public endpoint has added a path, not removed one.
- Subnet planning for private endpoints, since they consume addresses and are painful to re-space later, is a practical detail worth volunteering.
- The on-premises DNS forwarding requirement is the second most common failure and shows you have implemented this rather than read about it.
- Being honest that not every service supports private endpoints for every sub-resource, and that exceptions should be recorded with compensating controls, is the mature close.

---

[⬅ Back to Azure Platform Engineering](./README.md) · [All topics](../README.md)
