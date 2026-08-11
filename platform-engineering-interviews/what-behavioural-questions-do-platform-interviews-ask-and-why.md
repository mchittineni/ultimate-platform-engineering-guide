---
title: "What behavioural questions do platform interviews ask, and why?"
id: 135
category: "Platform Engineering Interviews"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-engineering-interviews
  - interview-questions
---

# What behavioural questions do platform interviews ask, and why?

**Short answer:** They cluster around influence without authority, judgement about what not to build, handling being the bottleneck, and learning from something you got wrong - because those are the situations a platform engineer is actually in. A platform team cannot compel adoption, is under permanent pressure to build more than it can operate, and is blamed for outages caused by components it inherited. The questions test whether you have navigated that rather than only built things.

## Detail

**Why platform behavioural rounds differ.** A stream-aligned engineer's behavioural questions are about collaboration and delivery. A platform engineer's are about serving internal customers who can ignore you, saying no to people more senior than you, and owning infrastructure everyone depends on and nobody thanks you for. The questions follow the job.

**The clusters, and what each is really probing:**

| Question theme                                     | Probing for                                                  |
| -------------------------------------------------- | ------------------------------------------------------------ |
| Getting teams to adopt something they did not want | Influence without authority; whether you reach for a mandate |
| A time you said no to a senior stakeholder         | Judgement, and whether you can hold a position               |
| When you were the bottleneck                       | Self-awareness; whether you fixed the cause                  |
| A platform decision you got wrong                  | Honesty and reflection; whether you own outcomes             |
| Disagreeing with your team on a technical choice   | How you argue and how you concede                            |
| An incident you caused that affected everyone      | Blamelessness in practice, and follow-through                |
| Deciding what not to build                         | Whether you build what is interesting or what is needed      |
| Handling a team that routed around the platform    | Whether you treat that as feedback or as misbehaviour        |

**Adoption without authority is the signature question.** Have a story where you changed someone's mind with evidence and effort rather than escalation - you did the migration for them, you fixed their specific blocker, you got their peer to vouch for it. A story that ends in leadership mandating it is a weak answer to this question, even if it is what happened, unless you can explain what you would do differently.

**The saying-no story needs a mechanism, not just courage.** The strong version cites something: an error budget policy, a published capacity trade-off, evidence that the request would serve fewer teams than the alternative. "I told them no" is weaker than "I showed them that building it would displace something unblocking six teams, and asked which they preferred".

**The got-it-wrong question is where candidates most often underperform.** A trivial mistake reads as evasion, and "I was too ambitious" reads as rehearsed. Pick something real with a consequence and a specific lesson - a deletion policy that destroyed a database, an interface change that broke forty teams, a capability nobody adopted because you never asked anyone. The specificity is what makes it credible.

**Have a bottleneck story.** Being the constraint is the platform team's characteristic failure, so there is no credit in claiming you never were. The good answer names how you noticed, what you changed structurally - self-service rather than more throughput - and what the number did afterwards.

**The routed-around question is a values test.** A team that built its own tooling to work around your platform is giving you a defect report. Candidates who describe it as non-compliance to be corrected reveal the wrong instinct; candidates who describe finding out what was missing and fixing it reveal the right one.

**Use a structure, lightly.** Situation, action, result, reflection - with most of the time on the action and the reflection, because that is where you appear. Two sentences of context and then what you actually did.

**Prepare four or five stories that flex.** Interviewers ask overlapping questions, and one well-understood project can supply an adoption story, a saying-no story, a mistake, and a disagreement. Prepare fewer stories properly rather than many superficially, and be honest when a question does not match anything you have lived - inventing an example collapses under follow-up.

## Example

```text
"Tell me about a time you got a team to adopt something they did not want to."

  WEAK - resolves by escalation
    "One team refused to migrate to our pipeline, so I escalated to their manager
     and they were told to do it. It took a couple of weeks but they moved."
  -> answers the question asked, and demonstrates the opposite of what is being
     probed. If this is genuinely what happened, say what you would do differently.

  STRONG - influence, evidence, and doing the work
    SITUATION (brief)
    "One team of eight had built their own deployment tooling and did not want our
     golden path. They were the last holdout of forty-one, and my instinct was
     that they were being difficult."

    ACTION
    "I sat with them for an afternoon instead of making the case again. Their
     objection turned out to be specific and correct: our default readiness probe
     configuration did not fit their workload, which takes ninety seconds to warm
     up, and our path had no way to override it. They had not told us because
     they assumed the answer would be no.
     I shipped a field override that week, then wrote the migration myself and
     opened the pull request against their repository with their tests passing.
     I was there for the first deploy."

    RESULT
    "They migrated in two days. More usefully, when I looked at the escape hatch
     register afterwards, eleven other services were overriding the same probe
     configuration - so our default was simply wrong, and I had been treating it
     as an adoption problem for months."

    REFLECTION
    "The lesson was that a team routing around the platform is a defect report,
     not non-compliance. I had spent three months persuading rather than asking
     what was missing. I now review the escape hatch register monthly, precisely
     so I find out before it becomes an adoption argument."
```

```text
"Tell me about a platform decision you got wrong."

  WEAK   "I was too ambitious with the roadmap and we over-committed."
         -> generic, no consequence, no specific lesson. Reads as rehearsed.

  STRONG "We shipped self-service databases with the default deletion policy,
          which meant deleting the claim destroyed the database. Two weeks in,
          someone deleted a staging namespace and we lost a database. Staging, so
          it cost a day - if it had been production it would have been a serious
          incident with data loss.
          Root cause on my side: I designed creation carefully and did not think
          about deletion at all. We moved everything stateful to orphan-on-delete,
          added admission policy requiring an explicit annotation to delete a
          production claim, and turned off GitOps pruning for stateful kinds.
          The general lesson I took is that creation and destruction deserve
          asymmetric ease - and I now design the deletion path at the same time
          as the creation path, for every capability. It is on our design
          checklist because of this."
         -> real, consequential, specific, and it produced a durable change.
```

```text
"Tell me about a time you said no to a senior stakeholder."

  The mechanism is what makes this strong - not the courage.

  "Our director asked for a developer portal. I did not want to build it and my
   opinion alone would not have been persuasive, so I brought two things.
   First, the support-question categories: zero of the previous quarter's 200
   questions were about finding services or people, which is what a portal would
   address. The top category, 41 a month, was 'why has my deploy not gone out' -
   which I could fix by exposing in-flight status, at about a tenth of the cost.
   Second, our published capacity split: building the portal would displace GPU
   scheduling, which would unblock six teams and remove four exceptions.
   I laid both out and asked which she would prefer. She chose GPU scheduling.
   What made that work was that the capacity split and the support categorisation
   already existed and were already published - I was not asking her to trust my
   judgement, I was showing her a trade-off. If I had only had an opinion, I think
   we would have built the portal."
```

## Interview tips

- Recognise the clusters - influence without authority, saying no, being the bottleneck, getting it wrong, being routed around - and prepare one story for each.
- For adoption, avoid a story that resolves through escalation. If that is what happened, say what you would do differently and why.
- For saying no, cite a mechanism: an error budget policy, a published capacity trade-off, evidence about how many teams are served. Courage alone is a weaker answer than a visible trade-off.
- For the mistake, pick something real with a consequence. The deletion-policy example works because it is specific, technical, consequential, and produced a durable change to how you design.
- Have a bottleneck story and describe a structural fix - self-service rather than more throughput. Claiming you were never the bottleneck is not credible for a platform role.
- Treat the routed-around question as the values test it is: a defect report, not non-compliance.
- Keep the situation short and spend your time on action and reflection. And be honest when a question does not match your experience - invented examples do not survive follow-up questions.

---

[⬅ Back to Platform Engineering Interviews](./README.md) · [All topics](../README.md)
