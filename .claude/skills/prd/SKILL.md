---
name: prd
description: Draft a Product Requirements Document for a new feature. Trigger on "write a PRD", "create a PRD", "PRD for <feature>", or when scoping a non-trivial feature before implementation starts.
---

# Writing a PRD

Produces a lean PRD sized for a solo/small-team developer — heavy on feasibility, data, and edge cases; light on the multi-stakeholder ceremony a large product org would need.

## 0. Check the PRD is warranted

Skip this skill and suggest a plain ticket instead when the work is a single, unambiguous change nobody would disagree on how to build (bug fix, one-line tweak, throwaway script). Continue only when the feature has real scope, ambiguity, or touches data/other features enough that two people could build it two different ways.

## 1. Identify the subject

State in one sentence what feature or problem this PRD covers. If the request doesn't already make this clear, ask before going further — every later step depends on it.

## 2. Gather answers

Ask the following one question at a time, in order — send a single question, wait for the reply, then send the next. Never batch multiple questions into one message. Skip a question already answered earlier in the conversation. Push back once on any answer that's a restated feature description rather than a problem/outcome (e.g. "add budgets" isn't a problem — "users can't tell if they're overspending" is).

**Problem**
- What's broken or missing today? Who hits it, and how do you know (data, complaints, your own use)?
- What happens if this doesn't get built?

**Users**
- Who's the primary user? Any secondary users?
- What's their current workaround, if any?

**Scope**
- What's in scope for v1? What's explicitly out?
- Must-have vs. nice-to-have, ranked.

**Requirements & behavior**
- Walk through the core flow step by step.
- What edge cases or failure states matter?
- Does this touch existing data or features in a way that could break them?

**Technical**
- Any data model or schema changes?
- Any new dependencies, services, or infra?
- Performance, security, or compliance constraints? (flag explicitly for anything touching money or financial data)

**Success**
- What does success look like, and how will it be measured?

**Risks & open questions**
- What's the riskiest or least-understood part?
- Anything without an answer yet?

Move to drafting once every category above has an answer or an explicit "not applicable" — a half-answered category produces a PRD with silent gaps.

## 3. Draft the PRD

Fill the template below. Omit a section only if step 2 marked it not applicable — don't invent content to fill a section.

```markdown
# PRD: <Feature Name>

## Problem
<what's broken/missing, who hits it, evidence>

## Goals
<what success looks like, with a measurable target>

## Non-goals
<explicitly out of scope for this version>

## Users
<primary + secondary, current workaround>

## Requirements
<core flow, step by step>

## Edge cases & failure states
<what can go wrong, and expected behavior>

## Technical notes
<data model changes, new dependencies, performance/security/compliance constraints>

## Priority
<must-have vs nice-to-have, ranked>

## Risks & open questions
<unresolved items, riskiest unknowns>
```

## 4. Save and confirm

Write the PRD to `docs/prds/<kebab-case-feature-name>.md` in the project (create the directory if it doesn't exist). Show the drafted content and ask whether anything needs revision before treating it as final.
