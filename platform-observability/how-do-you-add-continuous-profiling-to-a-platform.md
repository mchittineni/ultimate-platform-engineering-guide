---
title: "How do you add continuous profiling to a platform?"
id: 223
category: "Platform Observability"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-observability
  - interview-questions
---

# How do you add continuous profiling to a platform?

**Short answer:** Run a low-overhead sampling profiler on every node - today usually eBPF-based, so it covers every process without code changes - enrich the profiles with the same service, version, and Kubernetes metadata as the other signals, send them through the telemetry pipeline to a profiling backend, and link them to traces. Treat it as a platform capability with a measured overhead budget and clear symbolisation requirements. The OpenTelemetry profiles signal, in public alpha since 2026, is the direction of travel for the pipeline, but it is still an evaluation choice rather than a production default.

## Detail

**What continuous profiling gives that other signals do not.** Metrics tell you CPU is high; traces tell you a span was slow; neither tells you which function was burning the CPU or allocating the memory. A profiler samples call stacks many times per second and aggregates them into a flame graph showing where time and memory actually go, down to the line. Running it continuously in production - rather than attaching a profiler during an incident - means the data for last Tuesday's latency regression already exists, and you can compare version 1.4.2 with 1.4.3 directly.

**The mechanism: statistical sampling.** A sampling profiler interrupts each thread at a fixed frequency - commonly around 19 to 100 samples per second per CPU - records the stack, and counts identical stacks. At those rates the overhead is typically around or below one percent of CPU, which is what makes always-on profiling acceptable. Allocation, lock, and heap profiles work similarly but are usually language-runtime specific.

**Two ways to collect, and a platform usually wants both:**

| Approach                    | How it works                                                                           | Strengths                                                      | Limits                                                     |
| --------------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------- |
| eBPF whole-system profiler  | A privileged DaemonSet samples stacks for every process via the kernel                 | Zero code change, covers every language and third-party binary | Mostly CPU; needs privileges, a recent kernel, and symbols |
| In-process runtime profiler | Language SDK or agent (Go pprof, JFR, async-profiler, language agents) pushes profiles | Allocation, heap, lock, and goroutine profiles; exact frames   | Per-language integration, one more library to upgrade      |

The eBPF profiler donated to OpenTelemetry by Elastic now ships as a Collector receiver in its own distribution, with support for native code, the JVM, Go, Python, Node.js, .NET, Ruby, and more. It is the natural floor: every service gets CPU profiles on day one. In-process profilers are the opt-in for teams that need memory and contention detail.

**Symbolisation is the hard part.** A stack of raw addresses is useless. Interpreted and JIT languages can be unwound and named by the profiler, but compiled binaries need symbols, and stripped production images have none. The platform needs a policy: build with frame pointers enabled (many distributions and language toolchains now do this by default because profilers need them), and upload debug symbols from CI to a symbol store the backend can use, keyed by build ID. Without it you get flame graphs full of hex addresses.

**Use the same context as every other signal.** Profiles must carry `service.name`, `service.version`, namespace, pod, node, and deployment environment, added by the Collector's `k8sattributes` processor just as for traces. That is what lets an engineer filter to one service and one version, and compare before and after a deploy. Without shared context, profiling becomes a separate tool that nobody opens.

**Link profiles to traces.** The most useful question is "why was this span slow?", and a profile filtered to the samples taken while that span was running answers it. The OpenTelemetry profiles data model lets samples carry trace and span IDs; some backends also support span-scoped profiling through SDK integrations. From the other direction, a flame graph can link to exemplar traces that ran through the hot function.

**The pipeline and backend.** The Collector can receive, enrich, and export profiles in OTLP; profiles pipelines are alpha and have been behind the `service.profilesSupport` feature gate, so check the release notes for the version you run. Backends include open-source options such as Grafana Pyroscope and Parca, and commercial products that accept OTLP or pprof. Because the backend market for OTLP profiles is still settling, keeping the Collector in between is what protects you from a migration later.

**Cost and retention.** Profiles are compact once aggregated, but per-pod, per-15-second profiles across a large fleet add up. Keep high-resolution data for days, downsample or merge for longer retention, and sample fewer nodes for low-tier workloads if needed. Attribute volume per team like any other signal.

**Security and privileges.** The eBPF profiler needs elevated privileges and host PID visibility, which is a real exception to the platform's own pod security rules. Run it in a dedicated, locked-down namespace, restrict who can change its configuration, and document the exception. Stack traces can also leak function and file names from third-party code, which matters in some regulated environments.

**Rolling it out.** Start with the eBPF profiler on a subset of nodes, measure its overhead against an agreed budget, and fix symbolisation for the main languages. Then enable it fleet-wide, add a "profile" link from service dashboards and trace views, and publish a few wins - the platform's users, product engineers, adopt profiling once they see it find a regression in minutes that would otherwise have taken days. Finally, offer in-process profiling as an opt-in for memory and lock analysis.

**Trade-offs.** Profiling surfaces where resources go, not whether users are hurt, so it is a diagnosis and efficiency tool, not an alerting source. The alpha status of OpenTelemetry profiles means formats and component configuration can still change. And privileged node agents widen the platform's attack surface. For most fleets the efficiency gains - often double-digit percentage CPU savings found in a handful of hot functions - justify the cost.

## Example

```yaml
# Collector config for the otelcol-ebpf-profiler distribution (profiles are alpha).
receivers:
  profiling:
    samples_per_second: 97 # an odd rate avoids lock-step with periodic work
processors:
  memory_limiter: { check_interval: 1s, limit_percentage: 75, spike_limit_percentage: 20 }
  k8sattributes: {} # same service/pod/namespace context as traces
exporters:
  otlp:
    endpoint: profiling-backend.observability:4317
service:
  pipelines:
    profiles:
      receivers: [profiling]
      processors: [memory_limiter, k8sattributes]
      exporters: [otlp]
```

```yaml
# The DaemonSet that runs it on every node; the config above is mounted from a ConfigMap.
apiVersion: apps/v1
kind: DaemonSet
metadata: { name: ebpf-profiler, namespace: observability-profiling }
spec:
  selector: { matchLabels: { app: ebpf-profiler } }
  template:
    metadata: { labels: { app: ebpf-profiler } }
    spec:
      serviceAccountName: ebpf-profiler # needs RBAC to read pods for k8sattributes
      hostPID: true # sees every process on the node
      tolerations: [{ operator: Exists }]
      containers:
        - name: profiler
          image: otel/opentelemetry-collector-ebpf-profiler:0.148.0 # pin the version you tested
          args: ["--config=/etc/otel/config.yaml", "--feature-gates=service.profilesSupport"]
          securityContext:
            privileged: true # documented exception to the platform's pod security rules
          volumeMounts:
            - { name: config, mountPath: /etc/otel }
            - { name: sys-kernel, mountPath: /sys/kernel, readOnly: true }
          resources:
            requests: { cpu: 100m, memory: 200Mi }
            limits: { memory: 400Mi }
      volumes:
        - { name: config, configMap: { name: ebpf-profiler-config } }
        - { name: sys-kernel, hostPath: { path: /sys/kernel } }
```

```text
Comparing two versions of checkout after a CPU regression (diff flame graph):

  service.name=checkout  cpu, 1h window, v1.4.2 (baseline) vs v1.4.3

  FUNCTION                                   v1.4.2   v1.4.3   DELTA
  encoding/json.(*encodeState).marshal         6.1%    31.8%   +25.7%  <--
    orders.(*History).MarshalJSON               0.4%    27.2%   +26.8%
  crypto/tls.(*Conn).Write                     9.8%     9.6%    -0.2%
  runtime.gcBgMarkWorker                        7.2%    12.9%    +5.7%  (knock-on GC)

  cause: v1.4.3 serialises the full order history on every /pay request
  found in 4 minutes from the dashboard "profile" link; fix returns ~30% CPU

  linked traces: 12 slow /pay spans ran through orders.(*History).MarshalJSON
```

```text
Rollout checklist the platform tracks:

  overhead on pilot nodes ............ 0.6% CPU, 180Mi memory per node   within budget (1%)
  frame pointers in base images ...... Go, Rust, C/C++ images            enabled
  debug symbols uploaded from CI ..... 42 of 45 services                 3 missing
  profile link on service dashboards . generated from the template       done
  privileged exception ............... namespace, RBAC, review date 2027-03-31
```

## Interview tips

- Start with what profiling adds: metrics and traces show that something is slow, profiles show which code is responsible.
- Explain statistical sampling and why its low overhead makes always-on production profiling acceptable - and say you would measure it against a budget.
- Distinguish eBPF whole-system profiling (zero code, every language, mostly CPU) from in-process runtime profilers (memory, locks, exact frames), and propose both.
- Symbolisation is the detail that marks real experience: frame pointers and debug symbols uploaded from CI, or the flame graphs are unreadable.
- Insist on shared context and trace linkage, so profiles are filtered by service and version and reachable from a slow span.
- Be accurate on maturity: OpenTelemetry profiles entered public alpha in 2026 and pipelines are feature-gated, so it is an evaluation path with the Collector in front to avoid lock-in.
- Name the security exception - privileged, host PID - and how you contain it. Interviewers probe this for any node-level agent.

---

[⬅ Back to Platform Observability](./README.md) · [All topics](../README.md)
