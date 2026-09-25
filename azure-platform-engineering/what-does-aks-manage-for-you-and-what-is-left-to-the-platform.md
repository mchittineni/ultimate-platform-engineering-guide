---
title: "What does AKS manage for you, and what is left to the platform?"
id: 163
category: "Azure Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - azure-platform-engineering
  - interview-questions
---

# What does AKS manage for you, and what is left to the platform?

**Short answer:** Azure Kubernetes Service runs the Kubernetes control plane for you (API server, etcd, scheduler, controller manager), publishes patched node images and Kubernetes versions, repairs unhealthy nodes, and offers managed add-ons. Almost everything that makes a cluster usable by many teams is still yours: network design, identity wiring, policy, tenancy, ingress, GitOps, observability, upgrade cadence, and cost. AKS gives you a cluster; the platform turns clusters into a product.

## Detail

**What Microsoft runs.** The control plane lives in a Microsoft-managed subscription and you never see its VMs. On the Standard tier it carries a financially backed uptime SLA for the API server, and it scales with your cluster size. Microsoft patches the control plane, backs up etcd, and runs the components you would otherwise have to keep highly available yourself. It also publishes node images weekly, monitors node health, and automatically repairs nodes that go `NotReady`.

**What runs in your subscription.** The worker nodes are Virtual Machine Scale Sets in a separate node resource group (by default named `MC_<rg>_<cluster>_<region>`). You pay for them, they consume your quota, and their networking sits in your virtual network. You choose the VM sizes, the operating system (Azure Linux or Ubuntu, plus Windows for Windows containers), and how many node pools to run. Microsoft supplies the images; you decide when nodes move to them, either by hand or by setting an auto-upgrade channel.

**The shared-responsibility line, as a table:**

| Area                       | AKS does                                                     | You (the platform) do                                              |
| -------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------ |
| Control plane              | Runs, patches, scales, and backs it up                       | Choose tier; decide public, private, or VNet-integrated API server |
| Kubernetes versions        | Publishes versions; supports roughly the three newest minors | Upgrade within the support window; test workloads first            |
| Node OS                    | Publishes patched images; auto-repair                        | Pick OS, channel, and maintenance windows                          |
| Node capacity              | Cluster autoscaler or node autoprovisioning when enabled     | Choose and configure them; set limits; right-size requests         |
| Networking                 | Implements the CNI you select                                | Choose CNI, IP plan, egress path, network policy                   |
| Identity                   | OIDC issuer and workload identity features                   | Create identities, federated credentials, role assignments         |
| Ingress / gateway          | Optional application routing add-on                          | Choose the entry point, TLS, WAF, DNS                              |
| Policy                     | Azure Policy add-on and deployment safeguards                | Decide which policies, per namespace or tenant                     |
| Tenancy                    | Namespaces exist                                             | Quotas, RBAC, network isolation, onboarding                        |
| Delivery and observability | Managed Prometheus and Container Insights available          | GitOps, dashboards, alerts, SLOs                                   |

**Upgrades are the responsibility people underestimate.** AKS supports a Kubernetes minor version for about a year, and a cluster left behind falls out of support. AKS will stop an upgrade if it detects use of deprecated APIs, but it cannot know whether your workloads survive a node drain, whether PodDisruptionBudgets are sane, or whether an operator you installed supports the new version. The platform team owns that testing, the order of clusters, and the communication to tenants. Long-term support (on the Premium tier) buys a longer window for a specific minor version, not an escape from upgrading.

**Networking choices are made once.** The container network interface (CNI) you choose at creation, such as Azure CNI Overlay with the Cilium data plane, decides how pods get addresses, how much VNet address space you consume, and which network policies are available. Changing it later is disruptive. Egress needs a deliberate path (a NAT gateway or a route through the hub firewall), and whether the API server is private shapes how CI and engineers reach it.

**Add-ons move work, not responsibility.** AKS offers managed add-ons such as KEDA, the Istio-based service mesh, the application routing add-on for ingress, the Key Vault secrets store CSI driver, and Azure Monitor integration. They save you installing and patching those components, but you still decide which ones the platform supports, configure them, and handle their upgrade notes. For ingress in particular, the community ingress-nginx project has been retired, so a new platform should plan around Gateway API; the application routing add-on now offers a Gateway API implementation.

**Who the user is.** Product teams should not need to know any of this. They want a namespace with quotas, an identity that reaches their database, a way to deploy from Git, and dashboards. Everything in the right-hand column of the table is the work that produces that experience, and it is why a platform team exists even when the cluster itself is managed. If most of that column is more than you want to own, AKS Automatic presets much of it.

## Example

```bash
# An AKS Standard cluster where the platform has made the choices AKS leaves open.
az aks create \
  --resource-group rg-platform-aks \
  --name aks-prod-weu-01 \
  --tier standard \
  --network-plugin azure \
  --network-plugin-mode overlay \
  --network-dataplane cilium \
  --vnet-subnet-id "$NODE_SUBNET_ID" \
  --outbound-type userDefinedRouting \
  --enable-oidc-issuer \
  --enable-workload-identity \
  --enable-aad \
  --enable-azure-rbac \
  --disable-local-accounts \
  --auto-upgrade-channel patch \
  --node-os-upgrade-channel NodeImage \
  --os-sku AzureLinux \
  --zones 1 2 3
```

```text
What each flag decided (and who would otherwise have to):

  --tier standard ................. uptime SLA on the API server
  overlay + cilium ................ pod IPs outside the VNet range; eBPF network policy
  userDefinedRouting .............. egress through the hub firewall, not a public IP
  oidc-issuer + workload-identity . pods get Entra tokens without secrets
  enable-aad + azure-rbac ......... cluster access through Entra groups and Azure RBAC
  disable-local-accounts .......... no shared admin kubeconfig to leak
  auto-upgrade patch .............. patch releases applied automatically
  node-os NodeImage ............... weekly image updates, inside maintenance windows

Still not decided by any flag: minor version upgrade timing, namespaces and quotas,
policy set, ingress, GitOps, dashboards, cost allocation. That is the platform.
```

## Interview tips

- Draw the line precisely: Microsoft runs the control plane; nodes are VM Scale Sets in your subscription that you pay for and choose when to update.
- Say that upgrades remain your job, with the reason: AKS cannot test your workloads, PodDisruptionBudgets, or operators against a new version.
- Mention that CNI and IP planning are effectively one-way decisions, which is why they belong in the platform's design rather than each team's.
- Treat add-ons as "less to install", not "nothing to own".
- Name the users (product teams wanting a namespace, identity, deployment path, and dashboards) and frame the right-hand column as the product you build for them.
- Related reading: [How do you upgrade a fleet of clusters without breaking tenants?](../kubernetes-platform/how-do-you-upgrade-a-fleet-of-clusters-without-breaking-tenants.md) and [What is AKS Automatic and when would a platform use it?](./what-is-aks-automatic-and-when-would-a-platform-use-it.md).

---

[⬅ Back to Azure Platform Engineering](./README.md) · [All topics](../README.md)
