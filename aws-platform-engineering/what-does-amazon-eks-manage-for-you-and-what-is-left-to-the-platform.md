---
title: "What does Amazon EKS manage for you, and what is left to the platform?"
id: 150
category: "AWS Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - aws-platform-engineering
  - interview-questions
---

# What does Amazon EKS manage for you, and what is left to the platform?

**Short answer:** In its standard mode, EKS runs the Kubernetes control plane for you - the API server and etcd, spread across three availability zones, scaled, backed up, and patched - and integrates it with IAM and the VPC. Almost everything else is still a decision you own: when to upgrade the Kubernetes version, how nodes are provisioned and patched, which add-on versions run, how traffic gets in, and every platform capability on top - GitOps, policy, observability, secrets, tenancy, and the interface developers use. EKS Auto Mode and EKS Capabilities move more of that line towards AWS, but they do not remove it.

## Detail

**What AWS runs in standard mode.** The control plane lives in an AWS-owned account and connects into your VPC through elastic network interfaces. AWS keeps at least two API server instances and three etcd members across zones, replaces unhealthy ones, scales them with load, encrypts etcd, and applies patch releases within your chosen Kubernetes minor version. You get an API endpoint (public, private, or both), optional control-plane logs to CloudWatch, and integration points: **access entries** mapping IAM principals to Kubernetes permissions (replacing the old `aws-auth` ConfigMap), and **EKS Pod Identity** for giving Pods IAM roles.

**What AWS offers but you still drive.**

- **Kubernetes minor upgrades.** AWS publishes versions; you choose when to move. Each version gets roughly 14 months of standard support followed by up to 12 months of extended support at additional cost, after which EKS upgrades the cluster for you. Upgrade insights flag deprecated API usage before you upgrade.
- **Managed add-ons** - the VPC CNI, CoreDNS, kube-proxy, the EBS CSI driver, the Pod Identity agent. EKS packages and validates versions, but you pick when to update them and must keep them compatible with the cluster version.
- **Managed node groups.** EKS creates the Auto Scaling group and can roll nodes to a new AMI, but you trigger the update, choose the AMI family, and handle workloads that resist being drained.

**The data plane options, from most to least work.**

| Option              | You own                                                     | Typical use                                        |
| ------------------- | ----------------------------------------------------------- | -------------------------------------------------- |
| Self-managed nodes  | AMI, bootstrap, scaling, patching, replacement              | Unusual OS or hardware requirements                |
| Managed node groups | AMI choice and update timing, scaling policy                | The traditional default                            |
| Karpenter           | Karpenter itself, NodePools, AMI selection, disruption      | Flexible, bin-packed capacity; spot                |
| Fargate             | Pod sizing; accept its limits (no DaemonSets, no GPUs)      | Small or isolated workloads                        |
| EKS Auto Mode       | NodePool policy and workload readiness for node replacement | Teams that want AWS to run nodes and core add-ons  |
| EKS Hybrid Nodes    | The on-premises machines and their connectivity             | Running on-premises capacity under one EKS cluster |

**What is always left to the platform.** Even with the most managed options, these remain yours, and together they are most of the platform team's work:

- **Upgrade discipline across a fleet**: sequencing, testing, and checking tenants for deprecated APIs before AWS's support clock forces the issue.
- **Networking design**: VPC and subnet sizing (the VPC CNI gives each Pod a VPC address), ingress through the AWS Load Balancer Controller or a Gateway API implementation, and network policy.
- **Identity and access**: mapping teams to namespaces and permissions through access entries, and one IAM role per workload.
- **Platform components**: GitOps, admission policy, secrets delivery, observability agents, cost allocation, and the service template developers actually use.
- **Tenancy and guardrails**: namespaces, quotas, priority classes, Pod Security Standards.

**Where the line has moved recently.** **EKS Auto Mode** (December 2024) runs compute, load balancing, block storage, and networking components for you, with AWS patching and replacing nodes. **EKS Capabilities** (November 2025) runs Argo CD, AWS Controllers for Kubernetes (ACK), and kro as managed services in AWS-owned infrastructure rather than as Pods you operate. Both shift real toil, and both leave the choices - what to deploy, which policies apply, what developers see - with the platform team.

**Who the user is.** Product engineers should never need to know which of these options is in use. They push a service definition and get a running workload with logs, metrics, and a URL. The platform's job is to make EKS an implementation detail behind that interface, and to own the parts AWS does not.

**The trade-off.** A more managed EKS means less toil but less control: fewer choices about AMIs, add-on versions, and node access, and a dependency on AWS's release cadence. A less managed EKS gives control at the cost of a team to run it. Choose by the size of your platform team and how unusual your workloads are, not by what feels most sophisticated.

## Example

```text
Responsibility split for one production cluster (standard mode + Karpenter):

  AWS                                      PLATFORM TEAM
  -------------------------------------    --------------------------------------
  API server + etcd, 3 AZs, scaling        choose and schedule 1.xx -> 1.yy upgrades
  control-plane patching                   Karpenter, NodePools, AMI currency
  endpoint, control-plane logs             VPC CNI, CoreDNS, kube-proxy versions
  managed add-on packaging                 ingress / Gateway API controller
  access entries + Pod Identity APIs       team -> namespace -> access policy mapping
  upgrade insights                         Argo CD, Kyverno, OpenTelemetry, secrets
                                           quotas, PSS, cost allocation, templates
```

```bash
# Access entries: the current way to grant a team access, scoped to their
# namespace. No aws-auth ConfigMap edits.
aws eks create-access-entry \
  --cluster-name prod-eu-1 \
  --principal-arn arn:aws:iam::111122223333:role/AWSReservedSSO_team-payments-dev_0123456789abcdef

aws eks associate-access-policy \
  --cluster-name prod-eu-1 \
  --principal-arn arn:aws:iam::111122223333:role/AWSReservedSSO_team-payments-dev_0123456789abcdef \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy \
  --access-scope type=namespace,namespaces=team-payments

# Before an upgrade: what will break?
aws eks list-insights --cluster-name prod-eu-1
```

## Interview tips

- Draw the line precisely: EKS standard mode manages the **control plane**; the **data plane and everything on top** is yours unless you opt into more managed options.
- Mention that upgrades are still your decision, with a support clock (standard then extended support) that eventually forces them. That is why fleet upgrade practice matters - see [upgrading a fleet of clusters](../kubernetes-platform/how-do-you-upgrade-a-fleet-of-clusters-without-breaking-tenants.md).
- Name access entries as the replacement for the `aws-auth` ConfigMap - it is a quick currency check interviewers use.
- Know the data plane spectrum from self-managed nodes to Auto Mode, and when each fits. See [Karpenter](./how-do-you-manage-eks-node-capacity-with-karpenter.md) and [EKS Auto Mode](./what-is-eks-auto-mode-and-when-would-a-platform-use-it.md).
- Close on the user: developers should not know or care which option you picked.

---

[⬅ Back to AWS Platform Engineering](./README.md) · [All topics](../README.md)
