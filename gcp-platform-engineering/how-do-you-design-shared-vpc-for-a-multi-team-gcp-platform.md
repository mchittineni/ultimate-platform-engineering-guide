---
title: "How do you design Shared VPC for a multi-team GCP platform?"
id: 182
category: "GCP Platform Engineering"
difficulty: "Advanced"
tags:
  - platform-engineering
  - gcp-platform-engineering
  - interview-questions
---

# How do you design Shared VPC for a multi-team GCP platform?

**Short answer:** A host project owns the VPC and its subnets, and service projects attach to it so their workloads use those subnets while remaining separately owned, quota-bounded, and billed. The platform team keeps network administration in the host project and grants each team the network user role only on the specific subnets it needs. This gives you central network control with per-team project isolation, which is exactly the split a platform wants.

## Detail

**What the model gives you.** One VPC, one address plan, one set of firewall rules and routes, administered by the platform team - while each workload still lives in its own project with its own IAM, quotas, and billing. Without Shared VPC you either put everything in one project, losing isolation, or give every project its own VPC and then maintain a mesh of peerings with all the transitivity and address-overlap problems that brings.

**Grant the network user role at subnet level, not project level.** Granting `roles/compute.networkUser` on the whole host project lets a service project use any subnet, including ones belonging to other environments or tenants. Granting it on specific subnets is what makes the boundary real, and it is the single most important IAM detail in this design.

**Keep the network administrator role in the host project.** Firewall rules, routes, and subnet creation stay with the platform team. Teams that need a firewall change request it - or better, the platform generates rules from declared dependencies so the request disappears. Handing out firewall administration undoes the reason for centralising the network.

**Plan addresses before you start, and reserve generously.** Subnet ranges must not overlap with each other, with on-premises, or with any peered network. GKE additionally consumes secondary ranges for Pods and Services, and those are sized at cluster creation and awkward to change - Pod range exhaustion limiting cluster growth is a genuinely common and painful problem. GKE can now attach additional, discontiguous Pod ranges to an existing cluster (multi-Pod CIDR), which rescues growth - but only if the address plan still has free space to give it. Reserve larger secondary ranges than seem necessary.

**Firewall rules should be identity-based, not address-based.** Rules matching on service accounts rather than IP ranges or network tags survive rescheduling, cannot be borrowed by another workload that happens to acquire a tag, and read as authorisation rather than plumbing. Network tags are convenient and can be applied by anyone who can edit an instance, which makes them a weaker boundary. For new designs, global network firewall policies with secure tags are the current mechanism: the tags are IAM-governed resources, so binding one to a workload is itself an access-controlled act, and the policy is managed as one object rather than a scattering of VPC rules.

**One host project per environment.** A single host project spanning production and non-production means one firewall misconfiguration can bridge them. Separate host projects for production and non-production, each with its own address space, is the standard and defensible split.

**Not everything attaches identically.** Serverless products reach a Shared VPC through their own mechanisms - connectors or direct VPC egress - and some managed services use private service access with a peered range you must allocate. Plan an address block for private service access alongside your subnets, because discovering that requirement later is disruptive.

**Centralise egress and DNS.** Cloud NAT in the host project for outbound traffic gives you one place for logging and a stable outbound address for third-party allowlisting. Private DNS zones and private service access endpoints belong in the host project too, so every service project resolves consistently.

**Automate the attachment in vending.** A newly vended project should be attached to the right host project, granted the network user role on its subnets, and have its DNS and NAT paths working before anyone deploys. Manual attachment is where inconsistency enters.

## Example

```text
Host and service projects: central network, per-team isolation.

  platform/networking/
    proj: vpc-host-prod                  <- owns the VPC, subnets, firewall, NAT
      VPC: shared-prod
        snet-eu-west1-app     10.42.0.0/20
          secondary: pods     10.44.0.0/14    <- GKE pods. SIZE GENEROUSLY;
          secondary: services 10.48.0.0/20       exhaustion caps cluster growth
        snet-eu-west1-run     10.42.16.0/20    <- Cloud Run direct egress
        snet-eu-west1-psc     10.42.32.0/24    <- private service connect
        reserved for PSA      10.60.0.0/16     <- managed services peering range;
                                                  allocate this UP FRONT
        Cloud NAT             one stable egress address set for allowlisting
        Private DNS zones     resolved consistently by every service project

    proj: vpc-host-nonprod               <- SEPARATE host project and address
                                            space, so a firewall mistake cannot
                                            bridge prod and non-prod

  workloads/prod/
    proj: checkout-prod    attached as a service project
                           granted networkUser on snet-eu-west1-app ONLY
    proj: search-prod      attached as a service project
                           granted networkUser on snet-eu-west1-app ONLY
```

```bash
# Attach a service project, then grant the network user role AT SUBNET LEVEL.
gcloud compute shared-vpc associated-projects add checkout-prod \
  --host-project vpc-host-prod

# WRONG - lets this project use ANY subnet in the host project, including
# subnets belonging to other environments:
#   gcloud projects add-iam-policy-binding vpc-host-prod \
#     --role roles/compute.networkUser --member "serviceAccount:..."

# RIGHT - scoped to the one subnet this project should use:
gcloud compute networks subnets add-iam-policy-binding snet-eu-west1-app \
  --region europe-west1 --project vpc-host-prod \
  --role roles/compute.networkUser \
  --member "serviceAccount:$(gcloud projects describe checkout-prod \
      --format='value(projectNumber)')@cloudservices.gserviceaccount.com"
```

```bash
# Firewall rules on IDENTITY, not on tags or addresses. Service accounts survive
# rescheduling and cannot be borrowed the way a network tag can.
gcloud compute firewall-rules create allow-checkout-to-pricing \
  --project vpc-host-prod \
  --network shared-prod \
  --direction INGRESS \
  --action ALLOW --rules tcp:8080 \
  --target-service-accounts sa-pricing@search-prod.iam.gserviceaccount.com \
  --source-service-accounts sa-checkout@checkout-prod.iam.gserviceaccount.com

# Baseline: default deny, then allow only declared dependencies. The platform
# should GENERATE these rules from the service spec's dependsOn, so teams never
# request a firewall change.
gcloud compute firewall-rules create deny-all-ingress \
  --project vpc-host-prod --network shared-prod \
  --direction INGRESS --action DENY --rules all --priority 65000
```

```text
The two failures that hurt most, both from insufficient planning:

  1. GKE POD RANGE EXHAUSTION
     cluster created with secondary pod range /20 (4,096 addresses)
     each node reserves a /24 (256) by default -> ~16 nodes maximum
     -> the cluster cannot grow, and the secondary range cannot simply be
        enlarged in place. Remediation is adding a discontiguous Pod range
        (multi-Pod CIDR) - if the plan has space left - or a new cluster
        and a migration.
     -> allocate pod ranges far larger than current need, and consider a smaller
        per-node CIDR if node counts will be high.

  2. NO PRIVATE SERVICE ACCESS RANGE RESERVED
     a managed database requiring a peered range is requested; no block is free
     that does not overlap on-premises
     -> remediation touches the address plan, which is the most disruptive
        possible change. Reserve the block during initial design.
```

## Interview tips

- Explain the split first: host project owns the network, service projects keep their own IAM, quotas, and billing. That is the property a platform wants and it is why the model exists.
- Granting `compute.networkUser` at subnet level rather than project level is the single most important detail, and getting it wrong lets a project use any subnet.
- Keeping network administration in the host project - and better, generating firewall rules from declared dependencies - connects this to platform interface design.
- Identity-based firewall rules over network tags, with the reason that tags can be applied by anyone who can edit an instance, is a strong security point.
- Separate host projects per environment so a firewall mistake cannot bridge production and non-production.
- GKE secondary range exhaustion is the war story to have ready: it caps cluster growth and the remediation is a new cluster, so generous allocation up front is the lesson.
- Reserving a private service access block during initial design, because retrofitting it touches the address plan, is the second painful-planning point worth volunteering.

---

[⬅ Back to GCP Platform Engineering](./README.md) · [All topics](../README.md)
