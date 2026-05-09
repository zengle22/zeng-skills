# Admission Checklist for Design Package

Pre-SSOT quality gate adapted from `ITERATION-DOCUMENT-CHECKLIST.md` for `zgsd-bootstrap-milestone`.

This is the **blocking gate**. Any failure here stops milestone creation.

---

## Quick Scan (5 seconds)

Run this first. If any check fails, stop and run the detailed audit.

| # | Check | Pass Criteria |
|---|-------|--------------|
| 1 | **PRD present?** | Contains user stories + acceptance criteria (AC) |
| 2 | **Scope defined?** | Explicit In Scope / Out of Scope sections |
| 3 | **Business rules?** | Thresholds present with sources/assumptions |
| 4 | **Exceptions?** | Both business-level and system-level exceptions covered |
| 5 | **UX spec?** | Design principles + error-state UX rules |
| 6 | **Tech design?** | Sync/async strategy + layer responsibilities |
| 7 | **API contract?** | Endpoints + core fields + versioning approach |
| 8 | **Sequence diagrams?** | Mermaid/PlantUML for frontend-backend collaboration |
| 9 | **Storage plan?** | Table structure approach / JSONB vs normalized |
| 10 | **Test strategy?** | AC + boundary conditions + AI uncertainty scenarios |
| 11 | **Implementation scope?** | Modules involved + files explicitly NOT touched |
| 12 | **Architecture read?** | References `knowledge/architecture.md` or equivalent |
| 13 | **Git clean?** | Correct branch, no uncommitted changes |

**Result**: All ✅ → proceed to detailed audit. Any ❌ → **BLOCKED**.

> Note: "Git clean" is NOT part of document package admission — it is a GSD pre-coding check (`ITERATION-DOCUMENT-CHECKLIST.md` §5.2). Do not reject a design package for uncommitted git changes.

---

## Detailed Audit

### Dimension 1: Business Design

**Must have at least one of:**
- Product vision / product brief
- Scope declaration (In Scope / Out of Scope)
- Success metrics (quantifiable + target + measurement)

**Checks:**
- [ ] Iteration type identified (feature iteration vs business iteration)
- [ ] User persona defined (for business iterations)
- [ ] Business value stated (for business iterations)
- [ ] **Out of Scope items ≥ 3** and each is **concrete** (e.g., "No WeChat Pay" ✅, "No other payment methods" ❌)
- [ ] Success metrics have baseline or assumption source
- [ ] Priority P0/P1/P2 defined; **P0 ≤ 3 items**

**Block if**: No scope declaration OR Out of Scope is vague.

---

### Dimension 1.5: Package Structure Consistency (Bootstrap-specific)

**Applies only to blueprint-modular pattern.**

- [ ] Blueprint index (`00_blueprint.md`) lists N modules
- [ ] Actual module documents (`01_*.md` through `NN_*.md`) match the index
- [ ] No orphan module docs (numbered docs not referenced in blueprint)
- [ ] No missing module docs (referenced in blueprint but file not found)
- [ ] User stories doc (`09_*` or equivalent) covers all P0 modules
- [ ] Implementation scope doc (`12_*` or equivalent) covers all P0 modules

**Block if**: Blueprint says 7 modules but only 5 docs found, OR a P0 module has no corresponding design doc.

---

### Dimension 2: Product Design

**Must have:**
- PRD with user stories + AC
- OR user journey map with Happy Path + branches + exceptions

**Checks:**
- [ ] Problem statement present (background, pain point, root cause)
- [ ] User stories: `AS A... I WANT... SO THAT...`, numbered
- [ ] **Every user story has ≥ 1 AC**
- [ ] AC passes the "Testable Three Questions":
  1. What to test? (specific behavior/result)
  2. How to trigger? (operation/input)
  3. How to pass? (observable output/state change)
- [ ] In Scope / Out of Scope explicit and concrete
- [ ] Business rules: formulas, thresholds, frequency limits, Guardrail rules
- [ ] **Every threshold has a source** (data reference, user research, "product decision暂定")
- [ ] Exception flows: **business-level** (user error) + **system-level** (service failure)
- [ ] State transitions documented (conditions for each transition)
- [ ] Frontend-backend collaboration scenarios listed (not technical sequencing)

**Block if**: Any user story lacks AC, OR thresholds lack sources, OR no exception flows.

---

### Dimension 3: UX Design

**Must have at least one of:**
- UX specification
- User journey prototype
- Design principles document

**Checks:**
- [ ] **Design principles ≥ 3**, each with explanation + example
- [ ] Core page interaction flow (navigation, key interaction points)
- [ ] State expression rules (levels, calculation, color/icon/copy mapping)
- [ ] Design token reference (existing or new)
- [ ] Copy style guide (tone, forbidden words, ≥ 3 examples covering normal/warning/error)
- [ ] Platform differences (H5 vs Mini Program: functional, interaction, permission)
- [ ] Error-state UX spec (toast / empty page / skeleton / degraded content / retry button)

**Block if**: No design principles OR no error-state UX spec.

---

### Dimension 4: Architecture Design

**Must have at least one of:**
- Tech architecture overview
- Rough tech design

**Checks:**
- [ ] Tech stack declared (language, framework, DB, AI provider, key libs) — **locked, no discussion**
- [ ] Architecture layers and responsibilities (Transport/Handler/Service/AI/Repository/Domain)
- [ ] **Sync/async strategy** for every external call; every call has rationale
- [ ] Core data flow (full chain, transformation points, caching)
- [ ] Rough API contract: endpoints (path+method), core fields (name+type+required), versioning, auth
- [ ] **Sequence diagrams** (Mermaid/PlantUML) for frontend-backend collaboration covering:
  - Call direction
  - Sync/async nature
  - Timeout per call
  - Retry count + interval strategy
  - Degradation path
  - Idempotency strategy
- [ ] Storage approach (relational vs document, key entities, JSONB vs normalized)
- [ ] Non-functional requirements (performance P99, security, concurrency, degradation)
  - **Must be consistent with sequence diagram timeouts**
- [ ] Integration points and external dependencies + fallback strategy

**Block if**: No sync/async strategy OR no sequence diagrams OR API contract missing core fields.

---

### Dimension 5: Test Design

**Must have at least one of:**
- Acceptance criteria in PRD
- Known risk scenario list

**Checks:**
- [ ] Every user story has testable AC (Given-When-Then or observable metric)
- [ ] AC answers: what to test, how to trigger, how to pass
- [ ] Time-based AC has concrete values (or explicit "determined by tech design")
- [ ] AI-related AC has expected output mode (JSON structure, field ranges, enums)
- [ ] **Happy Path** defined end-to-end
- [ ] **Boundary conditions** per core business field (null, extreme values, long strings, concurrency, large data)
- [ ] **AI uncertainty scenarios**: invalid JSON, timeout, unexpected content, token limit
- [ ] Test layer strategy (unit / integration / E2E)
- [ ] Testability review conclusion (which ACs are ready for test translation)

**Block if**: ACs are not testable (no Given-When-Then and no observable metric).

---

### Dimension 6: Engineering Implementation

**Must have:**
- Implementation scope declaration

**Checks:**
- [ ] **Modules/directories to modify** listed (at least 3 directories or file types)
- [ ] **Files explicitly NOT to touch** listed
- [ ] Key implementation decisions documented and **locked**:
  - Sync vs async
  - Immediate vs delayed / scheduled
  - Optimistic vs pessimistic vs no lock
  - Soft vs hard delete
  - Cache strategy (Redis key structure, TTL)
- [ ] Dependencies on prior phases/features/PRs
- [ ] Rollback and degradation strategy
- [ ] Performance and capacity estimate (data volume, QPS, AI token usage, storage growth)

**Block if**: No file-level scope OR no "do not touch" list.

---

## Quality Gate (Q1-Q5)

Run these after the 6-dimension check.

| Gate | Check | Pass Criteria | Block? |
|------|-------|--------------|--------|
| Q1 | Document existence | All 6 dimensions have at least 1 document | **Yes** |
| Q2 | Decision traceability | Key decisions (tech, threshold, scope) have rationale/source | **Yes** |
| Q3 | Exception coverage | Every core scenario has business + system exception with behavior + perception | **Yes** |
| Q4 | Testability | Every AC can be independently verified by a third party | **Yes** |
| Q5 | Consistency | Same concept has same name, same value, same logic across all docs | **Yes** |

---

## Admission Report Templates

### PASS Template

```markdown
## ADMISSION REPORT

**Package:** [path]
**Status:** ✅ PASS

### Summary
- Documents: [N] files
- Dimensions covered: 6/6
- Quality gates: 5/5
- Critical gaps: 0

### Dimension Coverage
| Dimension | Status | Evidence |
|-----------|--------|----------|
| Business | ✅ | [file] §[section] |
| Product | ✅ | [file] §[section] |
| UX | ✅ | [file] §[section] |
| Architecture | ✅ | [file] §[section] |
| Test | ✅ | [file] §[section] |
| Engineering | ✅ | [file] §[section] |

### Verdict
All Pre-SSOT requirements satisfied. Ready for milestone bootstrap.
```

### BLOCKED Template

```markdown
## ADMISSION REPORT

**Package:** [path]
**Status:** ❌ BLOCKED

### Critical Gaps (must fix before bootstrap)

1. **[Dimension] — [Gap]**
   - **Missing:** [what's missing]
   - **Required by:** [checklist item]
   - **Fix:** [specific action]
   - **Source doc:** [expected location]

2. ...

### Quality Gate Results
| Gate | Status |
|------|--------|
| Q1 Document existence | ✅/❌ |
| Q2 Decision traceability | ✅/❌ |
| Q3 Exception coverage | ✅/❌ |
| Q4 Testability | ✅/❌ |
| Q5 Consistency | ✅/❌ |

### Verdict
[N] critical gaps found. Milestone bootstrap **refused**.

**Next steps:**
1. Fix the gaps above
2. Re-run `/zgsd-bootstrap-milestone [path]`
```
