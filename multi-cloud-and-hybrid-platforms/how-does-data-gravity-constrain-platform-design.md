---
title: "How does data gravity constrain platform design?"
id: 103
category: "Multi-Cloud and Hybrid Platforms"
difficulty: "Advanced"
tags:
  - platform-engineering
  - multi-cloud-and-hybrid-platforms
  - interview-questions
---

# How does data gravity constrain platform design?

**Short answer:** Large datasets are expensive and slow to move, so compute tends to migrate toward the data rather than the reverse - and egress pricing makes that asymmetry a financial one, not only a physical one. For a platform this means placement decisions should follow the data, cross-boundary data movement should be a declared and reviewed choice, and "we could move this later" becomes progressively less true as a dataset grows.

## Detail

**The mechanism.** Data accumulates in one place; the systems that use it are drawn to it because moving compute is cheap and moving data is not. Over time more services attach to the dataset, integrations multiply, and the cost and risk of relocating it rise faster than the data itself grows. The practical consequence is that the location of your primary datastore is one of the most durable decisions your platform will make.

**Egress pricing is what makes it asymmetric.** Getting data into a provider is typically free; getting it out costs per gigabyte, and cross-region and cross-zone transfer also carry charges. This means the economics of a migration worsen as the dataset grows, and it means that a design where a hot path crosses a billing boundary has an ongoing cost that scales with traffic rather than with the size of the estate.

**Where it constrains platform decisions:**

- **Runtime placement.** A service doing heavy reads should run where its data is. A platform that lets teams choose placement independently of their data will produce services paying cross-boundary transfer on every request.
- **Multi-cloud feasibility.** Portable compute is achievable; portable data is where multi-cloud programmes stall. If the dataset cannot move, a second cloud can only host workloads that do not need it, which is usually a much smaller set than the plan assumed.
- **Multi-region design.** Cross-region replication has cost, latency, and consistency implications. Reading locally and writing to a primary region is a common compromise, and it changes what the application must tolerate.
- **Observability.** Telemetry is data with its own gravity. Shipping metrics and traces across boundaries can become a surprisingly large line item, and it is why collectors and aggregation usually belong close to the workloads.
- **Analytics.** Copying operational data into a warehouse elsewhere means paying egress continuously and holding two copies. Keeping the warehouse near the source is usually the right instinct.

**The platform's job is to make the cost visible at design time.** A team choosing to put a service in one place and its database in another should see that as a flagged decision with a cost estimate, not discover it in a bill three months later. Making cross-boundary data flow a declared property of the service specification is what turns this from a monthly surprise into a design conversation.

**Reduce the flow rather than accepting it.** Caching at the edge, aggregating before transfer, compressing, sampling telemetry, using private connectivity where it prices better than public egress, and processing in place rather than moving data to compute. Most large egress bills come from a small number of patterns, and each of those patterns has a specific remedy.

**Treat exit cost as a growing number.** If portability matters at all, it should be assessed against current dataset sizes, and reassessed - because a decision that was reversible at ten terabytes may not be at a petabyte. Recording that trajectory is more useful than a one-off exit plan.

**The design principle to state.** Put the data where it will live for years, then place compute around it. Reversing that order - choosing compute placement first and assuming the data will follow - is how organisations end up paying for a hot path that crosses a billing boundary.

## Example

```text
Three designs for the same system. The difference is where the data sits.

DESIGN A - compute and data together (correct)
  primary Postgres ...... provider X, eu-west
  services reading it .... provider X, eu-west
  cross-boundary flow ... none on the hot path
  analytics ............. warehouse in provider X, same region; loaded internally
  egress cost ........... minimal, and it does not scale with request volume

DESIGN B - compute in one place, data in another (the expensive mistake)
  primary Postgres ...... provider X, eu-west
  services reading it .... provider Y (chosen for a Kubernetes preference)
  cross-boundary flow ... EVERY read crosses a billing boundary
  consequence ........... egress cost scales with request volume, plus 20-40ms
                          added latency per call, plus a new failure domain
  how it happened ....... placement chosen for compute reasons; nobody modelled
                          the data flow

DESIGN C - split by necessity, designed for (acceptable)
  primary Postgres ...... on-premises (regulatory requirement)
  read-heavy services ... on-premises, next to the data
  stateless API .......... cloud, calling on-premises ASYNCHRONOUSLY where it can
  aggregates ............ computed on-premises, only summaries cross the link
  cross-boundary flow ... small and bounded by design, not by hope

  The lesson: place the data first, then the compute. Design B is not a bad
  Kubernetes decision - it is a good Kubernetes decision made without looking
  at the data.
```

```yaml
# Making the cost visible at design time. Cross-boundary data flow is a declared
# property, so it is reviewed rather than discovered in a bill.
apiVersion: platform.example.com/v1
kind: Service
metadata: { name: reporting-api }
spec:
  owner: group:team-data
  placement: { provider: X, region: eu-west-1 }
  dependencies:
    - postgres:
        ref: warehouse-primary
        location: { provider: X, region: eu-west-1 } # SAME - no boundary crossed
  dataFlows:
    # Declared, estimated, and reviewed. The platform flags anything that
    # crosses a billing boundary on a hot path.
    - name: nightly-export
      to: { provider: Y, service: partner-sftp }
      volumePerDay: 40GB
      crossesBillingBoundary: true
      acknowledged: true
      mitigations: ["compressed", "off-peak schedule", "aggregated before transfer"]
```

```text
Where large egress bills actually come from, and the remedy for each:

  PATTERN                                  REMEDY
  telemetry shipped cross-boundary          collector + aggregation local to the
                                            workloads; sample traces; drop
                                            high-cardinality labels at source
  operational data copied to a warehouse    keep the warehouse near the source;
    in another provider                     replicate summaries, not raw rows
  service-to-service calls crossing a       co-locate; this cost scales with
    boundary on the hot path                request volume, which is the worst shape
  backups replicated cross-provider         compress, deduplicate, and rate-limit;
                                            also check the link is not shared with
                                            interactive traffic
  images pulled from a registry in another  regional registry replicas or a
    provider/region on every node scale-up  pull-through cache
  chatty analytics reading operational       read replicas locally; materialise
    data remotely                           aggregates near the data

  Exit cost as a growing number - the assessment worth keeping current:
    dataset            size now   egress est.   downtime   verdict
    operational PG      2.1 TB      moderate     hours     movable today
    object storage     140 TB       large        days      expensive, feasible
    warehouse          890 TB       very large   weeks     effectively immovable
    -> the warehouse decision is now permanent. Recording WHEN it became
       permanent is more useful than a one-off exit plan.
```

## Interview tips

- Lead with the mechanism and then the economics: compute moves toward data because moving data is slow, and egress pricing makes the asymmetry financial as well as physical.
- "Place the data first, then the compute" is the design principle, and Design B - a good Kubernetes decision made without looking at the data - is the memorable failure.
- The multi-cloud connection is strong: portable compute is achievable, portable data is where these programmes stall, so the second cloud can only host workloads that do not need the dataset.
- Telemetry as data with its own gravity is a detail most candidates miss, and it explains why collectors and aggregation belong near the workloads.
- Making cross-boundary data flow a declared, estimated property of the service specification is the platform answer - it converts a monthly billing surprise into a design review.
- The patterns-and-remedies list is concrete and shows you have reduced a real egress bill rather than just observed one.
- Framing exit cost as a growing number, and recording when a dataset became effectively immovable, is the senior close.

---

[⬅ Back to Multi-Cloud and Hybrid Platforms](./README.md) · [All topics](../README.md)
