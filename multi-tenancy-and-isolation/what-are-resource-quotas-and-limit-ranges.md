---
title: "What are resource quotas and limit ranges?"
id: 43
category: "Multi-Tenancy and Isolation"
difficulty: "Beginner"
tags:
  - platform-engineering
  - multi-tenancy-and-isolation
  - interview-questions
---

# What are resource quotas and limit ranges?

**Short answer:** A ResourceQuota caps the total a namespace may consume - CPU, memory, storage, and counts of objects such as pods or load balancers. A LimitRange sets per-object rules inside that namespace - default requests and limits for containers that do not declare them, plus minimum and maximum sizes. Quota protects the cluster from a tenant; a limit range protects the quota from a single oversized or undeclared pod. You almost always want both.

## Detail

**Requests and limits first, because both objects are built on them.** A container's _request_ is what the scheduler reserves for it on a node. Its _limit_ is the ceiling at runtime: exceeding a CPU limit throttles the container, exceeding a memory limit gets it OOMKilled. Quotas and limit ranges work by counting and constraining these numbers.

**ResourceQuota - the namespace budget.** It is enforced by an admission controller when objects are created. If creating a pod would push the namespace's total `requests.cpu` above the quota, the API server rejects it with a clear `exceeded quota` error. It can cap:

- **Compute:** `requests.cpu`, `requests.memory`, `limits.cpu`, `limits.memory`, and `requests.ephemeral-storage`.
- **Storage:** total `requests.storage` and the number of `persistentvolumeclaims`, optionally per StorageClass.
- **Object counts:** `count/pods`, `count/services.loadbalancers`, `count/configmaps`, `count/secrets`, and similar. These protect the control plane and your cloud bill, not just node capacity.

Quotas can also be scoped, for example to pods with a particular PriorityClass, so a team gets a small allowance of high-priority capacity and a larger allowance of ordinary capacity.

**One behaviour catches everyone out.** Once a quota constrains `requests.cpu` or `requests.memory`, every new pod in that namespace must specify those values, or it is rejected. That is why a quota on its own often breaks deployments that used to work - and why a LimitRange usually accompanies it.

**LimitRange - the per-object rules.** Also enforced at admission, it applies to each container, pod, or PVC individually:

- **`defaultRequest` and `default`** fill in a request and a limit for containers that omit them. This keeps pods out of the BestEffort quality-of-service class, which is evicted first under pressure, and keeps them countable against quota.
- **`min` and `max`** reject containers that are too small to be useful or too large to schedule fairly - no single 64-CPU pod in a shared namespace.
- **`maxLimitRequestRatio`** stops a container requesting a tiny amount while setting a huge limit, which is a way of overcommitting a node without paying for it in quota.

**How they fit together.** The limit range makes every pod well-formed; the quota bounds the sum. Without the limit range, the quota rejects undeclared pods. Without the quota, the limit range stops giant pods but not a thousand medium ones.

**Who the user is.** Application teams live inside these limits, usually without writing them. The platform generates both objects for each tenant namespace from the tenant's tier or declared allowance, and gives teams a way to see current usage against quota - ideally with an alert at around 80% rather than a surprise rejection during a deploy.

**The trade-offs.** Quotas set too tight turn into a steady stream of "please raise my quota" tickets; set too loose, they protect nothing. Quotas count _requests_, not real usage, so a team that over-requests wastes shared capacity while staying within quota - rightsizing reports help. And quotas are admission-time only: they do not evict running pods if you lower them, they only block new ones.

## Example

```yaml
apiVersion: v1
kind: ResourceQuota
metadata: { name: tenant-quota, namespace: team-search }
spec:
  hard:
    requests.cpu: "40"
    requests.memory: 80Gi
    limits.memory: 120Gi
    requests.ephemeral-storage: 40Gi # stops log floods filling node disks
    persistentvolumeclaims: "20"
    requests.storage: 1Ti
    count/pods: "200" # protects etcd and the scheduler
    count/services.loadbalancers: "2" # each one is a cloud resource and a bill
---
apiVersion: v1
kind: LimitRange
metadata: { name: container-defaults, namespace: team-search }
spec:
  limits:
    - type: Container
      defaultRequest: { cpu: 100m, memory: 128Mi } # applied when omitted
      default: { memory: 512Mi } # default memory limit; CPU limit left unset
      min: { cpu: 10m, memory: 32Mi }
      max: { cpu: "8", memory: 16Gi } # no single giant container
      maxLimitRequestRatio: { memory: "4" }
```

```text
$ kubectl describe resourcequota tenant-quota -n team-search
Name:                          tenant-quota
Namespace:                     team-search
Resource                       Used    Hard
--------                       ----    ----
count/pods                     143     200
count/services.loadbalancers   1       2
limits.memory                  96Gi    120Gi
persistentvolumeclaims         6       20
requests.cpu                   31500m  40
requests.ephemeral-storage     12Gi    40Gi
requests.memory                61Gi    80Gi
requests.storage               350Gi   1Ti

$ kubectl apply -f big-batch-job.yaml -n team-search
Error from server (Forbidden): pods "reindex-x7k2p" is forbidden: exceeded quota:
tenant-quota, requested: requests.cpu=12, used: requests.cpu=31500m, limited: requests.cpu=40
```

## Interview tips

- Give the one-line distinction first: quota is the namespace total, limit range is the per-container rule and the source of defaults.
- Mention the trap that a CPU or memory quota rejects pods without requests, and that a LimitRange default is the fix. It shows you have deployed into a quota'd namespace.
- Object-count quotas are the detail that lifts the answer: they protect etcd and the cloud bill, not just nodes.
- Note that quota counts requests, not usage, so it enforces fairness of reservation, not efficiency.
- For the wider noisy-neighbour picture, including API server fairness and priority classes, see [How do you stop one tenant degrading another?](./how-do-you-stop-one-tenant-degrading-another.md).

---

[⬅ Back to Multi-Tenancy and Isolation](./README.md) · [All topics](../README.md)
