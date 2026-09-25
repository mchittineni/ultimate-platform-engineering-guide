---
title: "What is EKS Auto Mode and when would a platform use it?"
id: 154
category: "AWS Platform Engineering"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - aws-platform-engineering
  - interview-questions
---

# What is EKS Auto Mode and when would a platform use it?

**Short answer:** EKS Auto Mode, launched in December 2024, extends AWS's responsibility from the control plane to the data plane. AWS runs Karpenter-based node provisioning, the Pod networking and network policy components, CoreDNS, the load balancer integration, the EBS CSI driver, GPU drivers, and the Pod Identity agent as managed parts of the cluster, and launches nodes as EC2 managed instances on locked-down Bottlerocket images that it patches and replaces - every node within 21 days. A platform uses it when node and add-on toil is the thing its team should stop doing, and avoids it when it needs control over the node image, host access, or component versions.

## Detail

**What changes mechanically.** In standard EKS you install and upgrade Karpenter or node groups, the VPC CNI, CoreDNS, kube-proxy, the AWS Load Balancer Controller, and the EBS CSI driver, and you choose and roll AMIs. In Auto Mode these become core components that AWS operates: they do not run as workloads in your cluster that you upgrade. You still get a Kubernetes API for configuring them, through familiar objects:

- **NodePools** (`karpenter.sh/v1`) - the same Karpenter API you may know, pointing at an Auto Mode **NodeClass** (`eks.amazonaws.com/v1`) instead of an `EC2NodeClass`.
- **StorageClasses** using the `ebs.csi.eks.amazonaws.com` provisioner.
- **IngressClasses** with controller `eks.amazonaws.com/alb`, and `Service` objects with load balancer class `eks.amazonaws.com/nlb`.

Two built-in NodePools, `system` and `general-purpose`, give you working capacity on day one. You should not edit them; you add your own alongside.

**The node model is the real shift.** Auto Mode nodes are treated as appliances. They run a Bottlerocket variant with SELinux enforcing and a read-only root file system, there is no SSH or SSM access, and custom AMIs are not supported. AWS handles spot interruption notices, EC2 health events, and scheduled maintenance, and replaces nodes by age: the default `expireAfter` is 336 hours (14 days), you can shorten it, and 21 days is the hard ceiling. New Auto Mode AMIs, released roughly weekly, also cause nodes to be replaced as drifted. Patching stops being a project: nodes simply get replaced, respecting pod disruption budgets and NodePool disruption budgets.

**What the platform still owns.** VPC design and subnet sizing, the cluster's Kubernetes version upgrades, NodePool policy (instance families, capacity type, limits, disruption budgets), and everything above the node: GitOps, admission policy, observability, secrets, tenancy, and the developer interface. You also still own workload readiness for churn - Auto Mode will move Pods regularly, and a single-replica service with a `minAvailable: 1` PDB will block node replacement just as it does with self-managed Karpenter.

**When it fits.**

- A small platform team whose time is going on node images, add-on compatibility matrices, and Karpenter upgrades rather than on developer-facing capabilities.
- Standard stateless and moderately stateful workloads that already tolerate node replacement.
- New clusters where you want a secure-by-default node posture (immutable OS, no host login, short node lifetime) without building it.
- GPU workloads where you would rather not manage NVIDIA or Neuron drivers yourself.

**When it does not.**

- You need a custom or hardened AMI, host-level agents that expect to modify the node, or interactive node access for debugging.
- You need to pin or patch specific versions of the CNI, CoreDNS, or the load balancer integration, or replace the CNI entirely.
- Your workloads cannot yet tolerate regular node replacement - fix that first, or Auto Mode will expose it.
- The cost model does not work for your fleet: Auto Mode adds a management charge per instance on top of normal EC2 pricing, so at large scale compare it against the cost of the engineering time it replaces rather than assuming either way.

**Adoption is incremental.** Auto Mode can be enabled on an existing cluster and coexists with managed node groups, so a platform can move one workload class at a time: create an Auto Mode NodePool, move Pods with node selectors or taints, then drain the old nodes. Note that Auto Mode uses its own label keys, such as `eks.amazonaws.com/instance-category` in place of `karpenter.k8s.aws/instance-category`, so NodePools and workload affinities copied from self-managed Karpenter need adjusting. Do not run self-managed Karpenter against the same workloads at the same time.

**How it relates to Karpenter.** Auto Mode is not a different autoscaler; it is Karpenter operated by AWS with a restricted node class. If you already run Karpenter well and need its full `EC2NodeClass` flexibility - custom user data, AMI selection, instance store configuration - there may be little to gain. If running Karpenter is the toil, Auto Mode removes it. See [managing node capacity with Karpenter](./how-do-you-manage-eks-node-capacity-with-karpenter.md) for the disruption controls that apply equally here.

## Example

```bash
# Create a cluster with Auto Mode: compute, load balancing, and block storage
# are all managed. The node role is the only node-level IAM you provide.
aws eks create-cluster \
  --name prod-eu-2 \
  --role-arn arn:aws:iam::111122223333:role/eks-cluster-prod-eu-2 \
  --resources-vpc-config subnetIds=subnet-0a1b,subnet-0c2d,subnet-0e3f,endpointPrivateAccess=true,endpointPublicAccess=false \
  --access-config authenticationMode=API \
  --no-bootstrap-self-managed-addons \
  --compute-config '{"enabled":true,"nodePools":["system","general-purpose"],"nodeRoleArn":"arn:aws:iam::111122223333:role/eks-auto-node-prod-eu-2"}' \
  --kubernetes-network-config '{"elasticLoadBalancing":{"enabled":true}}' \
  --storage-config '{"blockStorage":{"enabled":true}}'
```

```yaml
# A custom NodeClass and NodePool alongside the built-in ones: private
# subnets only, larger ephemeral storage, and a shorter node lifetime.
apiVersion: eks.amazonaws.com/v1
kind: NodeClass
metadata: { name: private-large-disk }
spec:
  # Same role as the built-in pools, so its EC2 access entry already exists.
  # A different role needs an access entry of type EC2 with the
  # AmazonEKSAutoNodePolicy access policy, or its nodes cannot join.
  role: eks-auto-node-prod-eu-2
  subnetSelectorTerms:
    - tags: { platform.example.com/tier: private }
  securityGroupSelectorTerms:
    - tags: { platform.example.com/cluster: prod-eu-2 }
  ephemeralStorage:
    size: 160Gi
---
apiVersion: karpenter.sh/v1
kind: NodePool
metadata: { name: batch-spot }
spec:
  template:
    spec:
      nodeClassRef: { group: eks.amazonaws.com, kind: NodeClass, name: private-large-disk }
      taints:
        - { key: interruptible, value: "true", effect: NoSchedule }
      requirements:
        - { key: karpenter.sh/capacity-type, operator: In, values: [spot, on-demand] }
        - { key: eks.amazonaws.com/instance-category, operator: In, values: [c, m, r] }
        - { key: eks.amazonaws.com/instance-generation, operator: Gt, values: ["5"] }
      expireAfter: 168h # shorter than the 14-day default and 21-day ceiling
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
    budgets:
      - nodes: "20%"
  limits: { cpu: "800" }
---
# Block storage through the managed driver - note the Auto Mode provisioner.
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: gp3-encrypted }
provisioner: ebs.csi.eks.amazonaws.com
volumeBindingMode: WaitForFirstConsumer
parameters:
  type: gp3
  encrypted: "true"
```

```text
Decision record from a platform team adopting it:

  context   3 platform engineers, 14 clusters, ~40% of team time on AMI
            rollouts, add-on compatibility, and Karpenter upgrades
  decision  Auto Mode for all new clusters; migrate existing clusters by
            workload class over two quarters
  excluded  2 clusters running a vendor agent that needs a custom AMI -
            stay on self-managed Karpenter, reviewed 2027-03
  watch     per-instance management charge vs. engineering time recovered;
            PDBs that block the 21-day replacement (alert on node age)
```

## Interview tips

- Define it by responsibility: standard EKS manages the control plane; Auto Mode also manages nodes and the core data-plane components.
- Explain that it is Karpenter underneath, configured through `karpenter.sh/v1` NodePools and an `eks.amazonaws.com/v1` NodeClass - it shows you know the mechanism rather than the marketing.
- Name the node model: Bottlerocket, immutable, no SSH/SSM, no custom AMIs, 21-day maximum lifetime. Those are exactly the constraints that decide fit.
- Give both sides of the decision - when to adopt and when not to - and frame the cost question as management charge versus engineering time, without quoting prices.
- Point out that disruption hygiene still matters: blocking PDBs stop node replacement in Auto Mode just as they do with self-managed Karpenter.

---

[⬅ Back to AWS Platform Engineering](./README.md) · [All topics](../README.md)
