# Design Package → GSD Milestone Mapping Guide

How to translate a pre-designed document package into GSD-native artifacts.

---

## Package Structure Patterns

### Pattern A: Blueprint-Modular

**Signature:** Contains `00_blueprint.md` or similar index document with numbered module docs.

**Typical layout:**
```
00_blueprint.md              → Architecture overview + priority matrix
00_enums_contract.md         → Type definitions / enum contracts
01_module_a.md               → Detailed design for module A
02_module_b.md               → Detailed design for module B
...
09_user_stories.md           → Cross-module user stories + AC
10_user_journey.md           → UX journey map
11_ux_principles.md          → Design principles
12_implementation_scope.md   → File-level scope
```

**Mapping:**
- `00_blueprint.md` → Milestone goal, priority matrix, module dependency graph
- `0N_module_*.md` → Phase N detail, Phase CONTEXT.md content
- `09_user_stories.md` → REQUIREMENTS.md (REQ-IDs grouped by module)
- `12_implementation_scope.md` → Phase CONTEXT.md implementation sections

---

### Pattern B: PRD-Standard

**Signature:** Single PRD document or PRD + Tech Design pair.

**Typical layout:**
```
PRD.md            → Requirements, user stories, scope
TECH-DESIGN.md    → Architecture, API, storage
UX-SPEC.md        → Design principles, interactions
```

**Mapping:**
- `PRD.md` → REQUIREMENTS.md + MILESTONE-CONTEXT.md
- `TECH-DESIGN.md` → Phase CONTEXT.md tech decisions + implementation scope
- `UX-SPEC.md` → UI hint detection + phase UX context

---

### Pattern C: Heuristic

**Signature:** Unstructured collection of markdown files. No clear index.

**Approach:**
1. Read all files (up to 50)
2. Classify each by dimension (Business/Product/UX/Arch/Test/Eng)
3. Extract content heuristically
4. Map the richest dimension first, backfill from others

---

## Priority → GSD Scope Mapping

| Source Priority | GSD Destination | Rule |
|-----------------|----------------|------|
| **P0** | `## v1 Requirements` (checkboxes) | Must deliver in this milestone |
| **P1** | `## v2 Requirements` (no checkboxes) | Acknowledged, deferred to next milestone |
| **P2** | `## Out of Scope` table | Explicitly excluded with reasoning from source |
| Unprioritized but In Scope | `## v1 Requirements` | Treat as P0 if source says "In Scope" |

**Important:** Preserve the original priority labels in requirement source attribution:
```markdown
- [ ] **DECI-01**: User receives run-day decision before workout
  - *Source: 04_decision_engine.md §3.1 (P0)*
```

---

## Module → Phase Mapping

**Rule: One P0 module = One Phase**

Exceptions:
- **Tiny module** (< 3 user stories, < 5 files): Merge with dependent module
- **Large module** (> 10 user stories, cross-cutting): Split into sub-phases (5.1, 5.2)
- **Pure-setup module** (migrations, scaffolding): Can be Phase 1 "Foundation"

**Phase numbering:**
- Continue from existing ROADMAP.md last phase + 1
- Or start at 1 if `--reset-phase-numbers`

**Phase dependency:**
- Module A depends on Module B → Phase A "Depends on: Phase B"
- If dependency is soft (can mock/stub) → note in CONTEXT.md, not hard dependency

---

## User Story → REQ-ID Mapping

**Format:** `[MODULE]-[NUMBER]`

| Source Field | REQ Field |
|-------------|-----------|
| Story ID (e.g., US-015) | Preserved as `source_id` in attribution |
| `AS A... I WANT... SO THAT...` | Requirement description (user-centric) |
| Given-When-Then ACs | Converted to observable success criteria |
| Priority (P0/P1/P2) | Determines v1 / v2 / Out of Scope placement |

**AC → Success Criteria conversion:**

```markdown
# Source (from PRD)
**AC-1**: Given user has completed onboarding, when they open the app,
          then they see today's training decision card.

# GSD Success Criterion
1. User sees a training decision card on the home screen after completing onboarding
```

**Rule:** Convert "Given-When-Then" (test perspective) to "User can..." (outcome perspective).

---

## Business Rule → Decision Mapping

Business rules with thresholds become `## Key Decisions` in Phase CONTEXT.md:

```markdown
## Key Decisions

| Decision | Rationale | Source |
|----------|-----------|--------|
| Rest day triggered when LoadScore > 850 | 95th percentile from historical user data | 04_decision_engine.md §5.2 |
| Max weekly mileage increase: 10% | Conservative progression per Daniels' RUNNING Formula | 02_training_plan.md §3.1 |
```

---

## Implementation Scope → Context Mapping

**File-level scope from source** maps directly to Phase CONTEXT.md:

```markdown
## Implementation Scope

### New Files
- `apps/api/internal/decision/` — New package for decision engine
  - `engine.go` — Core rule evaluation
  - `auditor.go` — Decision audit logging
- `db/migrations/000015_create_decision_audits.up.sql`

### Modified Files
- `apps/api/internal/service/training_plan_service.go` — Integrate decision caller
- `apps/miniapp/src/stores/training-plan.ts` — Add decision state

### Do Not Touch
- `apps/api/internal/ai/service/prompt/` — Prompt templates remain unchanged
- `apps/api/internal/guardrail/` — Guardrail rules not in this phase
```

---

## Tech Decision → Context Mapping

**Locked decisions** from source become `<decisions>` blocks in CONTEXT.md:

```markdown
- **[LOCKED] Sync/Async**: Decision evaluation is synchronous (must return within 2s)
  - Rationale: User waits for run-day decision before workout
  - Source: 04_decision_engine.md §2.3

- **[LOCKED] Storage**: Decision audits use normalized PostgreSQL table (not JSONB)
  - Rationale: Queryable for admin dashboard and compliance
  - Source: 00_blueprint.md §8.2
```

---

## UX Spec → UI Hint Mapping

**UI keyword detection** (case-insensitive):

```
UI, interface, frontend, component, layout, page, screen, view, form,
dashboard, widget, CSS, styling, responsive, navigation, menu, modal,
sidebar, header, footer, theme, design system, Tailwind, React, Vue,
Svelte, Next.js, Nuxt, UniApp, Mini Program, 小程序, 页面, 组件, 布局
```

If a phase's module doc or user stories match these keywords, add:
```markdown
**UI hint**: yes
```

This triggers downstream workflows to suggest `/gsd-ui-phase` at the right time.

---

## Artifact Templates

### MILESTONE-CONTEXT.md Template

```markdown
# Milestone Context: v[VERSION] [NAME]

**Source Package:** [PACKAGE_PATH]
**Pattern:** [PATTERN]
**Goal:** [GOAL]

## Target Features (P0)
- [Module Name]: [One-line goal]
- [Module Name]: [One-line goal]

## Deferred Features (P1)
- [Module Name]: [One-line goal]

## Key Constraints
- [Type]: [What] — [Why]

## Source Document Index
| # | Document | Dimension | Path |
|---|----------|-----------|------|
| 1 | [name] | [dim] | `[path]` |

## Design Decisions (Locked)
- **[Name]**: [Value] — [Rationale] (Source: [source])
```

### REQUIREMENTS.md Section Template

```markdown
## v1 Requirements

### [MODULE_NAME]

- [ ] **[REQ_ID]**: [Description]
  - *Source: [source_doc] §[section] ([original_priority])*
  - **AC:**
    - [Given] → [When] → [Then]
```

### Phase CONTEXT.md Template

```markdown
# Phase [NUM]: [NAME]

## Goal
[Goal description]

## Requirements
- [REQ_ID]: [Brief description]

## Depends On
[Phase X] / Nothing (first phase)

## Success Criteria
1. [Criterion] ← [Supporting REQ-IDs]

## Key Decisions
- **[[LOCKED]]** [Decision] — [Rationale]
  - Source: [source_doc]

## Implementation Scope
### New Files
- [path] — [purpose]

### Modified Files
- [path] — [change_description]

### Do Not Touch
- [path] — [reason]

## References
- [Description]: `[path]`

**UI hint**: yes  ← Add if phase matches UI keywords
```

---

## Semantic Drift Guardrails

During mapping, **strictly preserve**:

| Source Element | Preservation Rule |
|----------------|-------------------|
| Threshold values | Exact value + unit; never round or "simplify" |
| Formulas | Exact formula; never rewrite |
| Enum values | Complete list; never omit "edge" values |
| Error codes | Exact code strings; never invent aliases |
| File paths | Exact paths from implementation scope |
| AC conditions | Exact trigger conditions; never generalize |
| Timeout values | Exact milliseconds/seconds; never approximate |

**If source is ambiguous**: Flag as `AMBIGUOUS` in the mapping log, do NOT guess. Ask user in the review gate.
