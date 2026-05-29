---
name: zgsd-bootstrap-milestone
description: "Bootstrap a GSD milestone from a pre-designed document package with admission gating. Use when the user has a complete design document package (PRD, UX spec, Tech Design, Implementation Scope, etc.) and wants to convert it directly into GSD planning artifacts (milestone, requirements, roadmap, phase contexts) without going through GSD's discovery/questioning phase. Triggers on: 'bootstrap milestone from docs', 'create milestone from design package', 'import design docs as milestone', 'convert docs to GSD milestone'."
---

# zgsd-bootstrap-milestone

Convert a pre-designed document package into a GSD milestone with full planning artifacts. This skill bridges the gap between "design-complete" and "execution-ready" by automating the translation of design docs into GSD's native format.

**Key difference from `gsd-ingest-docs`**: `ingest-docs` merges doc content into existing planning incrementally. This skill treats the document package as a **self-contained milestone blueprint** and generates a complete, standalone milestone ready for `/gsd-plan-phase`.

**Admission gate**: Documents that fail the Pre-SSOT checklist are rejected with a detailed gap report. No milestone is created for incomplete input.

---

## Execution Flow

### Phase 1: Admission Gate (Blocking)

Parse `$ARGUMENTS`:
- First positional token → `PACKAGE_PATH` (required)
- `--name "Milestone Name"` → milestone name (optional, defaults to inferred from package)
- `--version X.Y` → milestone version (optional, defaults to next version from MILESTONES.md)
- `--mode new|merge` → `new` overwrites existing milestone artifacts; `merge` appends to existing (default: `merge` if `.planning/` exists)
- `--reset-phase-numbers` → start phase numbering at 1 (default: continue from last milestone)
- `--force` → skip admission gate. **DANGEROUS**: incomplete design packages will produce broken milestones. Require explicit user acknowledgment.

**Validate path:**
```bash
test -d "$PACKAGE_PATH" || { echo "ERROR: Package path not found: $PACKAGE_PATH"; exit 1; }
```

**Run admission check:**

Read `references/admission-checklist.md` for the full checklist, then execute:

```bash
# Scan package structure
find "$PACKAGE_PATH" -type f -name '*.md' | sort > /tmp/doc_list.txt
wc -l /tmp/doc_list.txt
```

Spawn admission auditor agent to perform the admission audit:

```
Agent(prompt="
You are an admission auditor. Read the document package at $PACKAGE_PATH and check it against the Pre-SSOT checklist in references/admission-checklist.md.

<files_to_read>
- references/admission-checklist.md
- All .md files under $PACKAGE_PATH (read incrementally, focus on key documents first)
</files_to_read>

<audit_scope>
1. Document existence: Does the package cover all 6 dimensions (Business, Product, UX, Architecture, Test, Engineering)?
2. PRD testability: Does every user story have AC? Are ACs Given-When-Then or observable?
3. Scope clarity: Is In Scope / Out of Scope explicitly defined?
4. Business rules: Are thresholds present with sources/assumptions?
5. Exception coverage: Are both business-level and system-level exceptions defined?
6. Implementation scope: Is there a file-level scope declaration (which files to touch / not touch)?
7. Tech decisions: Are sync/async strategies, storage approach, and key architectural decisions documented?
8. Consistency: Are terms, values, and logic consistent across documents?
</audit_scope>

<output>
Produce a structured admission report. Format:

## ADMISSION REPORT

**Package:** $PACKAGE_PATH
**Status:** PASS / BLOCKED

### Dimension Coverage
| Dimension | Status | Evidence |
|-----------|--------|----------|
| Business Design | ✅/❌ | [file + section] |
| Product Design | ✅/❌ | [file + section] |
| UX Design | ✅/❌ | [file + section] |
| Architecture | ✅/❌ | [file + section] |
| Test Design | ✅/❌ | [file + section] |
| Engineering | ✅/❌ | [file + section] |

### Critical Gaps (if any)
- [ ] [Gap description] → [Required action]

### Quality Gate
- Q1 Document existence: ✅/❌
- Q2 Decision traceability: ✅/❌
- Q3 Exception coverage: ✅/❌
- Q4 Testability: ✅/❌
- Q5 Consistency: ✅/❌

### Verdict
PASS: All gates cleared. Ready for bootstrap.
OR
BLOCKED: N critical gaps found. Milestone creation refused.
</output>
", description="Admission audit")
```

**Handle result:**

- **If BLOCKED**: Write the full admission report to `.planning/BOOTSTRAP-ADMISSION.md`, display it to the user, and **stop**. Do not proceed to Phase 2.
- **If PASS**: Write the admission report to `.planning/BOOTSTRAP-ADMISSION.md`, display a concise summary, and proceed to Phase 2.

> **Hard rule**: Unless `--force` is present, a BLOCKED admission report is terminal. Never create milestone artifacts for incomplete design packages.

---

### Phase 2: Parse & Map

Read `references/mapping-guide.md` for the full mapping rules.

**Step 2.1: Identify package structure**

Detect the document package pattern:

```bash
# Blueprint-modular pattern (e.g., MVP 1.5)
if [ -f "$PACKAGE_PATH/00_blueprint.md" ]; then
  PATTERN="blueprint-modular"
# PRD-standard pattern
elif [ -f "$PACKAGE_PATH/PRD.md" ] || ls "$PACKAGE_PATH"/*-prd.md 1>/dev/null 2>&1; then
  PATTERN="prd-standard"
# Fallback
else
  PATTERN="heuristic"
fi
```

**Step 2.2: Extract structured data**

Spawn parsing agent to extract machine-readable milestone spec:

```
Agent(prompt="
Parse the document package at $PACKAGE_PATH (pattern: $PATTERN) and extract:

1. **Milestone metadata**: name, version, goal (1 sentence)
2. **Priority matrix**: P0 items → v1 scope, P1 → v2 scope, P2 → out of scope
3. **Module list**: each module's name, goal, dependencies on other modules
4. **User stories**: ID, description, AC (Given-When-Then), priority
5. **Business rules**: rule name, formula/threshold, source/assumption
6. **Exception flows**: scenario, system behavior, user perception
7. **Tech decisions**: sync/async, storage, API approach, key architecture choices
8. **Implementation scope**: files to create, files to modify, files NOT to touch
9. **UX specifications**: design principles, state rules, platform differences
10. **Test strategy**: test layers, AI uncertainty scenarios, boundary conditions

Write the extracted spec to: /tmp/bootstrap-spec.json
Use a flat JSON structure for easy downstream consumption.
", description="Parse design package")
```

---

### Phase 3: Generate GSD Artifacts

**Step 3.1: Generate MILESTONE-CONTEXT.md**

```markdown
# Milestone Context: v$VERSION $NAME

**Source Package:** $PACKAGE_PATH
**Goal:** [from spec.goal]

## Target Features
- [Feature 1 from P0]
- [Feature 2 from P0]
- ...

## Key Context
- [Core constraints from spec]
- [Tech stack from spec]
- [Critical decisions from spec]

## Priority Matrix
- **P0 (v1 — this milestone):** [list]
- **P1 (v2 — next milestone):** [list]
- **P2 (Out of Scope):** [list]

## Source Documents
| Document | Role | Path |
|----------|------|------|
| [name] | [dimension] | `$PACKAGE_PATH/[file]` |
```

Write to `.planning/MILESTONE-CONTEXT.md`.

**Step 3.2: Generate REQUIREMENTS.md**

- REQ-ID format: `[MODULE]-[NUM]` (e.g., `RUNR-01`, `DECI-03`)
- Continue numbering from existing REQUIREMENTS.md if present
- P0 items → `## v1 Requirements` (with checkboxes)
- P1 items → `## v2 Requirements` (no checkboxes)
- P2 items + explicit exclusions → `## Out of Scope` table
- Preserve Given-When-Then ACs verbatim from source
- Add `Source:` attribution per requirement pointing to original doc

**Step 3.3: Generate ROADMAP.md**

- Each P0 module → one Phase
- Phase numbering: continue from existing ROADMAP.md, or start at 1 if `--reset-phase-numbers`
- Phase `Depends on`: derived from module dependency graph
- Phase `Requirements`: REQ-IDs from the module's user stories
- Phase `Success Criteria`: derived from ACs (converted to observable user behaviors)
- Add `**UI hint**: yes` for phases matching UI keywords
- Include `**Source:** $PACKAGE_PATH/[module-doc]` per phase

**Step 3.4: Pre-generate Phase CONTEXT.md files**

For each phase, create `.planning/phases/{nn}-{slug}/{nn}-CONTEXT.md` with:

```markdown
## Goal
[from module goal]

## Requirements
- [REQ-IDs]

## Key Decisions
[from tech decisions relevant to this module]

## Implementation Scope
### New Files
- [file paths]

### Modified Files
- [file paths]

### Do Not Touch
- [file paths]

## References
- Design doc: `$PACKAGE_PATH/[module-doc]`
- User stories: `$PACKAGE_PATH/[user-stories-doc]`
- UX spec: `$PACKAGE_PATH/[ux-doc]` (if applicable)
```

---

### Phase 4: Integrate with GSD

**⚠️ CRITICAL: Do NOT call `/gsd-new-milestone` after generating artifacts.**

`new-milestone` Step 9 regenerates REQUIREMENTS.md from scratch, which would **destroy** the carefully mapped REQ-IDs, P0/P1/P2 scoping, and source attributations from Phase 3.

Instead, perform **direct artifact integration**:

**Step 4.1: Update PROJECT.md**

Append the `## Current Milestone` section directly (same format as `new-milestone` Step 4):

```markdown
## Current Milestone: v$VERSION $NAME

**Goal:** [from spec.goal]

**Target features:**
- [Feature 1]
- [Feature 2]

**Source Design Package:** `$PACKAGE_PATH`
```

Ensure `## Evolution` section exists (add if missing, per `new-milestone` Step 4).

**Step 4.2: Update STATE.md**

Use SDK to atomically reset for new milestone:
```bash
gsd-sdk query state.milestone-switch --milestone "v$VERSION" --name "$NAME"
```

**Step 4.3: Update MILESTONES.md (optional)**

Add upcoming milestone entry:
```markdown
## v$VERSION — $NAME

**Status:** 📋 Planned
**Phases:** [start]-[end]
**Source:** `$PACKAGE_PATH`
```

**Step 4.4: Cleanup**

Delete `.planning/MILESTONE-CONTEXT.md` (consumed, per `new-milestone` Step 6).

```bash
rm -f .planning/MILESTONE-CONTEXT.md
```

Present to user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ZGSD ► MILESTONE BOOTSTRAPPED ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Milestone v$VERSION: $NAME**
**Source:** $PACKAGE_PATH

| Artifact | Location | Status |
|----------|----------|--------|
| Admission Report | .planning/BOOTSTRAP-ADMISSION.md | ✅ PASS |
| Milestone Context | .planning/MILESTONE-CONTEXT.md | ✅ Created |
| Requirements | .planning/REQUIREMENTS.md | ✅ [N] REQ-IDs |
| Roadmap | .planning/ROADMAP.md | ✅ [N] Phases |
| Phase Contexts | .planning/phases/{nn}-*/ | ✅ [N] pre-filled |

**Next Steps:**
1. Review generated artifacts (especially REQUIREMENTS.md scope)
2. `/gsd-plan-phase [first-phase-number]` — start planning

The phase CONTEXTs are pre-filled from your design docs.
Plan-phase will start with full context, skipping the usual discovery.
```

**Option B: Manual review gate**

If user prefers, stop after artifact generation and ask:
- "Approve and commit?"
- "Review REQUIREMENTS.md first?"
- "Adjust phases?"

---

## Anti-Patterns

- **Do NOT** skip the admission gate unless `--force` is explicitly passed AND user has acknowledged the risk
- **Do NOT** invent requirements not present in the source documents
- **Do NOT** change business rules, thresholds, or formulas during translation
- **Do NOT** create phases for P1/P2 items — only P0 goes into this milestone
- **Do NOT** delete or modify original source documents in `$PACKAGE_PATH`
- **Do NOT** overwrite existing `.planning/` files without user approval in merge mode

## Success Criteria

- [ ] Admission gate passed (report written to `.planning/BOOTSTRAP-ADMISSION.md`)
- [ ] MILESTONE-CONTEXT.md created and references source package
- [ ] REQUIREMENTS.md generated with REQ-IDs, P0/P1/P2 correctly scoped
- [ ] ROADMAP.md generated with phase-per-module, dependencies mapped
- [ ] Phase CONTEXT.md files pre-filled with design doc references
- [ ] PROJECT.md updated with `## Current Milestone` section
- [ ] STATE.md reset via `gsd-sdk query state.milestone-switch`
- [ ] All business rules, thresholds, and ACs preserved without modification
- [ ] User knows next step: `/gsd-plan-phase [N]`
