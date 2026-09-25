---
title: "What is structured logging and why does a platform enforce it?"
id: 215
category: "Platform Observability"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-observability
  - interview-questions
---

# What is structured logging and why does a platform enforce it?

**Short answer:** Structured logging means writing each log entry as a set of named fields - usually a JSON object - rather than a free-text sentence, so machines can filter, aggregate, and join logs without fragile parsing. A platform enforces it because logs from hundreds of services are only useful together when they share a format and a few common fields - timestamp, severity, service, and trace ID - and because consistent structure is what makes redaction, retention, and cost controls possible at all.

## Detail

**Unstructured versus structured.** An unstructured line such as `Payment failed for order 8812 after 3 retries (card declined)` is readable by a person but awkward for a machine. To find all declined payments you write a regular expression, and it breaks the day someone rewords the message. The structured version records the same facts as fields: `event=payment_failed`, `order_id=8812`, `retries=3`, `reason=card_declined`. Now "count declined payments by reason in the last hour" is a query, not a parsing project.

**The mechanism.** The application uses a logging library that emits key-value pairs, and a handler serialises them, usually as one JSON object per line on standard output. On Kubernetes, the container runtime writes stdout to a file on the node, and a node agent - often the OpenTelemetry Collector with its filelog receiver - reads the file, parses the JSON, adds Kubernetes metadata, and forwards the record. Because the log is already structured, the pipeline does not need a custom parser per service.

**The fields a platform standardises.** Teams can add whatever domain fields they like, but a small core must be consistent everywhere:

| Field                     | Why it must be consistent                                    |
| ------------------------- | ------------------------------------------------------------ |
| Timestamp (UTC, ISO 8601) | Ordering events across services and time zones               |
| Severity                  | Filtering, alerting, and retention by level                  |
| Message                   | A short, stable description of the event                     |
| `service.name`, version   | Knowing which build produced the line                        |
| `trace_id`, `span_id`     | Joining the log to the trace of the request that produced it |
| Tenant or owning team     | Access, cost attribution, and routing                        |

OpenTelemetry's log data model defines these ideas - timestamp, severity, body, attributes, resource, and trace context - so the platform does not need to invent its own schema.

**Trace correlation is the biggest single win.** When the OpenTelemetry SDK or a logging bridge is active, the current trace and span IDs can be attached to every log record automatically. An engineer looking at a slow span can then see exactly the logs that request produced, across every service it touched. Without the trace ID, finding them means guessing from timestamps.

**Why enforce rather than recommend.** A recommendation produces a mix of formats, and the value of structure is in consistency. If a tenth of services log free text, every cross-service query has a blind spot, every parser needs exceptions, and redaction rules cannot rely on field names. Enforcement can be gentle: provide a logging library per language that is pre-configured, generate new services from templates that already use it, and have the pipeline flag or quarantine lines that are not valid JSON rather than silently dropping them.

**Structure enables the controls the platform owns.** With known field names, the Collector can drop or hash fields such as `user.email` before logs reach storage, route security-relevant events to a longer-retention store, sample or drop debug-level logs in production, and attribute log volume to the owning team. None of this is dependable against free text.

**The trade-offs.** Structured logs are larger than terse text lines, and JSON is noisier for a human reading a terminal - most libraries offer a readable console format for local development and switch to JSON in deployed environments. Structure also makes it tempting to attach huge objects to every line, which inflates cost; the platform should cap line size and discourage dumping whole request bodies. Finally, structure does not fix bad content: a well-formed log line saying `error occurred` is still useless.

**Who benefits.** Product engineers, the platform's users, get logs that are searchable and linked to traces with no pipeline work of their own. The platform team gets one parsing path instead of hundreds, and security and compliance get field-level redaction they can trust.

## Example

```go
// Go's standard library log/slog (Go 1.21+) emitting JSON to stdout.
package main

import (
    "log/slog"
    "os"
)

func main() {
    logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo})).
        With("service.name", "checkout", "service.version", "1.4.3")

    logger.Warn("payment failed",
        "event", "payment_failed",
        "order_id", 8812,
        "retries", 3,
        "reason", "card_declined",
    )
}
```

```json
{
  "time": "2026-09-25T14:02:17.412Z",
  "level": "WARN",
  "msg": "payment failed",
  "service.name": "checkout",
  "service.version": "1.4.3",
  "event": "payment_failed",
  "order_id": 8812,
  "retries": 3,
  "reason": "card_declined",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7"
}
```

The `trace_id` and `span_id` are added by the platform's logging wrapper from the active OpenTelemetry context, not by hand.

```yaml
# Collector agent: read container logs, parse JSON, and flag lines that are not structured.
receivers:
  filelog:
    include: [/var/log/pods/*/*/*.log]
    include_file_path: true
    operators:
      - type: container # unwraps the container runtime format
      - type: json_parser
        if: body matches "^\\{"
        parse_to: body # parsed lines get a map body; free text stays a string
        on_error: send # keep the line even if parsing fails
processors:
  transform/flag_unstructured:
    log_statements:
      - context: log
        statements:
          - set(attributes["platform.log.unstructured"], true) where IsString(body)
  attributes/redact:
    actions:
      - { key: user.email, action: hash }
```

## Interview tips

- Define it concretely with a before-and-after: the free-text line versus the same facts as named fields.
- Name the core fields and why each matters, and single out the trace ID as the field that links logs to traces.
- Explain why enforcement beats recommendation: the value is consistency, and a partial rollout leaves blind spots in every query.
- Describe enforcement as paved road rather than punishment - pre-configured libraries, templates, and a pipeline that flags unstructured lines instead of dropping them.
- Connect structure to the controls it enables: redaction, routing, retention, and cost attribution all depend on known field names.
- Be honest about the costs - bigger lines, less readable in a terminal, and the temptation to log whole objects - and mention a readable local format as the usual fix.

---

[⬅ Back to Platform Observability](./README.md) · [All topics](../README.md)
