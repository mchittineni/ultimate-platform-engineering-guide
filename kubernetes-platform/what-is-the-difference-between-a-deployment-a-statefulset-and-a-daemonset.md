---
title: "What is the difference between a Deployment, a StatefulSet, and a DaemonSet?"
id: 54
category: "Kubernetes Platform"
difficulty: "Beginner"
tags:
  - platform-engineering
  - kubernetes-platform
  - interview-questions
---

# What is the difference between a Deployment, a StatefulSet, and a DaemonSet?

**Short answer:** All three are controllers that keep a set of Pods running from a template, and they differ in what they promise about those Pods. A Deployment treats Pods as interchangeable replicas - the default for stateless services. A StatefulSet gives each Pod a stable name, stable storage, and an ordered lifecycle - for software where replica 0 is not the same as replica 2. A DaemonSet runs exactly one Pod per matching node - for node-level agents. Picking the right one is mostly a question of what identity the workload needs.

## Detail

**They are all reconcilers.** Each is a controller watching a desired state - "three replicas of this template" or "one per node" - and creating or deleting Pods until reality matches. None of them runs your container directly; they create Pods, and the scheduler and kubelet do the rest. The difference is the contract each controller keeps about identity, ordering, and placement.

**Deployment: interchangeable replicas.** A Deployment manages ReplicaSets, and a ReplicaSet manages Pods with random name suffixes. Any Pod can be killed and replaced by a new one with a different name and IP, and nothing should care. That is what makes rolling updates simple: the Deployment creates a new ReplicaSet for the new template and shifts replicas across, governed by `maxSurge` and `maxUnavailable`, and keeps old ReplicaSets so `kubectl rollout undo` works. It is the right default for web services, APIs, and queue consumers - anything whose state lives in a database or cache elsewhere.

**StatefulSet: stable identity.** Pods are named `name-0`, `name-1`, `name-2`, and keep those names when rescheduled. Each gets its own PersistentVolumeClaim from `volumeClaimTemplates`, and the claim follows the Pod identity - `data-kafka-1` always reattaches to `kafka-1`. A headless Service gives each Pod a stable DNS name (`kafka-1.kafka.team-data.svc`), which clustered software uses to find its peers. By default Pods are created in order and terminated in reverse order, and rolling updates proceed one ordinal at a time from the highest. That matters for systems with a primary, a quorum, or a leader election.

**What a StatefulSet does not do.** It gives stable identity and storage; it does not know how to fail over a database, rebalance partitions, or take a consistent backup. That knowledge lives in the application or in an operator built on top. Deleting a StatefulSet also does not delete its volumes by default, which is a safety feature that surprises people when storage keeps accumulating (`persistentVolumeClaimRetentionPolicy` controls this).

**DaemonSet: one per node.** The controller watches nodes, not a replica count. When a node joins, it gets a Pod; when a node leaves, the Pod goes with it. Node selectors and tolerations narrow which nodes count. This is how log shippers, metrics and eBPF agents, CNI plugins, CSI node drivers, and security agents run. DaemonSet Pods usually need tolerations for tainted pools - otherwise your GPU or system nodes silently have no log shipping.

| Controller  | Pod identity         | Storage                    | Scaling unit    | Typical use                             |
| ----------- | -------------------- | -------------------------- | --------------- | --------------------------------------- |
| Deployment  | Random, disposable   | Shared or none             | Replica count   | Stateless services, workers             |
| StatefulSet | Stable ordinal + DNS | One PVC per Pod, kept      | Replica count   | Databases, Kafka, etcd, ZooKeeper       |
| DaemonSet   | One per node         | Usually host paths or none | Number of nodes | Log, metrics, CNI, CSI, security agents |

**The trade-offs.** StatefulSets are slower to roll and harder to operate: ordered updates take longer, a stuck Pod blocks the ones behind it, and a volume bound to a zone pins its Pod to that zone. DaemonSets cost resources on every node, so an agent requesting 500m of CPU on a 200-node fleet is 100 cores of overhead - a platform team should budget and review them. Deployments are cheap and flexible but only because they assume the state is somewhere else.

**The platform view.** Application developers should mostly never choose. The platform's service specification maps `type: web-service` or `type: worker` to a Deployment with the right disruption budget and spread constraints. StatefulSets are rarely a golden path for tenants - most platforms steer teams towards managed databases and queues and keep StatefulSets for the platform's own components. DaemonSets are almost entirely the platform team's own tool, because they run on every tenant's nodes. Also worth knowing: Jobs and CronJobs are the fourth common controller, for work that runs to completion rather than forever.

## Example

```yaml
# A StatefulSet showing the three things a Deployment cannot give you:
# stable names, per-Pod storage, and stable DNS via a headless Service.
apiVersion: v1
kind: Service
metadata: { name: kafka, namespace: team-data }
spec:
  clusterIP: None # headless: DNS returns each Pod, not a virtual IP
  selector: { app: kafka }
  ports: [{ name: broker, port: 9092 }]
---
apiVersion: apps/v1
kind: StatefulSet
metadata: { name: kafka, namespace: team-data }
spec:
  serviceName: kafka # gives kafka-0.kafka.team-data.svc, kafka-1..., kafka-2...
  replicas: 3
  selector: { matchLabels: { app: kafka } }
  persistentVolumeClaimRetentionPolicy:
    whenDeleted: Retain # deleting the StatefulSet never deletes the data
    whenScaled: Retain
  template:
    metadata: { labels: { app: kafka } }
    spec:
      containers:
        - name: broker
          image: apache/kafka:4.1.0 # KRaft settings via env omitted for brevity
          ports: [{ name: broker, containerPort: 9092 }]
          volumeMounts: [{ name: data, mountPath: /var/lib/kafka/data }]
  volumeClaimTemplates: # one PVC per Pod: data-kafka-0, data-kafka-1, data-kafka-2
    - metadata: { name: data }
      spec:
        accessModes: [ReadWriteOnce]
        resources: { requests: { storage: 200Gi } }
```

```yaml
# A DaemonSet for a platform log agent. Note the tolerations: without them the
# tainted GPU and system pools would have no log collection at all.
apiVersion: apps/v1
kind: DaemonSet
metadata: { name: log-agent, namespace: platform-telemetry }
spec:
  selector: { matchLabels: { app: log-agent } }
  updateStrategy: { type: RollingUpdate, rollingUpdate: { maxUnavailable: 10% } }
  template:
    metadata: { labels: { app: log-agent } }
    spec:
      priorityClassName: system-node-critical
      tolerations:
        - operator: Exists # run on every node, whatever its taints
      containers:
        - name: agent
          image: fluent/fluent-bit:4.0.3
          resources:
            requests: { cpu: 50m, memory: 64Mi } # multiplied by every node in the fleet
            limits: { memory: 128Mi }
          volumeMounts: [{ name: varlog, mountPath: /var/log, readOnly: true }]
      volumes:
        - name: varlog
          hostPath: { path: /var/log }
```

## Interview tips

- Frame the answer around identity: disposable replicas, stable ordinal identity, or one per node. That single axis explains everything else.
- For StatefulSets, name all three guarantees - stable name, per-Pod PVC, stable DNS via a headless Service - and then say what it does not do: it is not a database operator and knows nothing about failover.
- The DaemonSet-missing-tolerations trap (no logs from tainted nodes) and the fleet-wide cost of DaemonSet requests are practical details that show you have run one.
- Expect "would you run Postgres in a StatefulSet?" A good answer is "only with a mature operator, and usually the platform should offer a managed database instead" - the choice is about who owns day-two operations.
- From the platform angle, say developers should pick a service type, not a controller; the platform maps it to a Deployment with the right defaults.

---

[⬅ Back to Kubernetes Platform](./README.md) · [All topics](../README.md)
