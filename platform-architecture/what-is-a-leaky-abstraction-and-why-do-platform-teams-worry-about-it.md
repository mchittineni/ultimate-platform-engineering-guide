---
title: "What is a leaky abstraction and why do platform teams worry about it?"
id: 31
category: "Platform Architecture"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-architecture
  - interview-questions
---

# What is a leaky abstraction and why do platform teams worry about it?

**Short answer:** An abstraction leaks when details it was supposed to hide show up anyway - usually through failures, performance, or limits - and the user suddenly needs to understand the layer underneath. Platform teams worry about it because the whole value of a platform abstraction is that developers do not need to learn Kubernetes, cloud networking, or database tuning. A leak brings that cognitive load straight back, at the worst moment, often during an incident, and with no documentation because the abstraction pretended the detail did not exist.

## Detail

**The origin of the term.** Joel Spolsky's "Law of Leaky Abstractions" (2002) states that all non-trivial abstractions leak to some degree. His example was TCP: it presents a reliable stream, but when the network is unplugged, reliability is simply not available, and the application has to deal with it. The law is not a criticism of abstractions - it is a warning that you cannot design the lower layer out of existence.

**How platform abstractions leak.** The same four routes come up again and again:

- **Errors in the wrong vocabulary.** A developer writes `postgres: { size: small }` and gets back `InvalidParameterCombination: Cannot find version 15.2 for postgres`. The platform promised them they did not need to know about engine versions; the error says otherwise.
- **Performance.** "A volume" looks the same whether it is local SSD or network-attached storage, until latency is ten times higher. "A queue" looks the same until the underlying service's message size limit is hit.
- **Limits and quotas.** Connection limits on the small database tier, API rate limits on the cloud account, IP address exhaustion in a subnet. The abstraction had no concept of them, so the developer cannot see them coming.
- **Lifecycle and timing.** Provisioning that is "instant" in the interface takes twelve minutes in reality; deletion that looks reversible is not.

**Why it is a platform-specific worry.** The platform's user chose the abstraction precisely so they did not have to learn what is beneath it. When it leaks, they are worse off than if they had used the raw tool: they now need the underlying knowledge and have to reverse-engineer what the platform generated. The result is support tickets, loss of trust, and teams quietly leaving the golden path. Cognitive load is the reason platforms exist - see [cognitive load and platform design](../developer-experience/what-is-cognitive-load-and-why-does-it-drive-platform-design.md) - and a leak spends it.

**What platform teams do about it.** Since leaks cannot be eliminated, the goal is to make them honest and manageable:

- **Translate errors.** Catch provider errors at the platform boundary and rewrite them in the interface's terms, with the original attached for those who want it.
- **Expose limits as part of the contract.** If `size: small` means 100 connections, say so in the documentation and in `platform explain`.
- **Show the generated output.** A read-only view of what the platform created lets a developer reason about a leak without guessing.
- **Offer an escape hatch.** When the abstraction genuinely cannot express something, a controlled override beats a ticket queue. See [keeping an abstraction escapable](./how-do-you-keep-a-platform-abstraction-escapable.md).
- **Choose the level carefully.** Abstract what is genuinely common and stable. Hiding something that teams regularly need to tune guarantees leaks.

**The trade-off.** A thicker abstraction hides more and leaks more painfully; a thinner one leaks less but saves less effort. Multi-cloud portability layers are the extreme case, because they try to hide differences that affect behaviour - see [what a portable abstraction costs](../multi-cloud-and-hybrid-platforms/what-does-a-genuinely-portable-platform-abstraction-cost-you.md).

## Example

```text
A leak, and the same leak handled well.

Developer's spec:
  dependencies:
    - postgres: { size: small }

WITHOUT translation - raw provider error surfaced in the portal:
  Error: creating RDS DB Instance (checkout-db): operation error RDS:
  CreateDBInstance, api error StorageQuotaExceeded: DB instance storage
  quota exceeded for account.

  The developer does not know what an account storage quota is, which
  account it refers to, or who can raise it. They open a ticket.

WITH translation at the platform boundary:
  Error: postgres "checkout-db" could not be created.
    Reason:  the payments production account has reached its database
             storage quota (platform limit, not something you can fix).
    Action:  the platform team has been paged automatically (PLAT-4821).
             Your request will retry when the quota is raised.
    Detail:  StorageQuotaExceeded from AWS RDS CreateDBInstance
             (shown for debugging; you do not need to act on it)

Same leak - the quota is real and cannot be abstracted away - but the
developer now knows it is not their fault, who owns it, and what happens next.
```

## Interview tips

- Cite Spolsky's law and state it correctly: all non-trivial abstractions leak. Then say the goal is to make leaks honest, not to eliminate them.
- Give concrete leak routes - errors, performance, limits, lifecycle. A real example you have seen is worth more than the definition.
- Tie it to the user: a leak is worse than no abstraction, because the developer now needs the hidden knowledge and the platform's generated output on top.
- Error translation at the boundary is the most practical mitigation and is often overlooked; volunteer it.
- Expect the follow-up "so how thick should the abstraction be?" - thick enough to remove common decisions, thin enough that the things teams regularly tune stay visible.

---

[⬅ Back to Platform Architecture](./README.md) · [All topics](../README.md)
