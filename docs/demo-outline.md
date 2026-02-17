# Content Marketer — Presentation Outline

**15-20 min presentation + 5-10 min live demo + Q&A**

---

## 1. Thesis (3 min)

> Pharma content is a constrained-assembly problem, not a creative-generation problem.

Two independent systems, by design:

| System | Role | Method |
|---|---|---|
| Generation | Arrange pre-approved claims into formatted HTML | Probabilistic (LLM) |
| Compliance | Validate output before export | Deterministic (regex, string matching, DOM parsing) |

**Rejected alternatives:**

| Approach | Rejected because |
|---|---|
| RAG | LLM retrieves claims — no human-in-the-loop for selection |
| Free-form chat | Generate-then-check loop — frustrating, low first-pass compliance |
| Template system | Too rigid — combinatorial explosion across content types |

---

## 2. User Flow (4 min)

```
Setup ──▶ Brief ──▶ Claims & Assets ──▶ Editor
(user)    (guided)   (user + AI retrieval)  (human + AI + rules)
```

| Step | What happens | Who controls it |
|---|---|---|
| **Setup** | Content type, audience, goal, tone (4 dropdowns) | User — no AI |
| **Brief** | 3 structured questions → vector similarity search | Guided — AI retrieves, doesn't generate |
| **Claims & Assets** | Claims by category + relevance scores, assets by type. Explicit selection. Fair balance warning | User — LLM never sees unselected items |
| **Editor** | LLM assembles HTML, claims in `data-claim-id` spans. ISI appended by system | Human + AI + rules |

**Editor detail:**

- AI edit — natural language instructions, claim spans preserved
- Direct edit — `contentEditable`, ISI locked, double-sanitized (DOMPurify + nh3)
- After every edit — 7 compliance checks in ~200ms, export blocked on failure

---

## 3. Architecture (5 min)

### Stack

```
Next.js 14 (App Router, Zustand, SSE) ──▶ FastAPI (async, orchestrator) ──▶ Postgres 16 + pgvector
```

### Core isolation rule

Compliance engine imports zero AI/ML libraries. Model update can never silently change what passes.

### Two retrieval strategies

| | Discovery | Validation |
|---|---|---|
| **Method** | Vector similarity (pgvector HNSW) | String matching (sliding window) |
| **Why** | Fuzzy — want related results | Strict — need exact matches |

### Ingestion pipeline

```
Source PDFs ──▶ Classify (text ratio) ──▶ Text path (pymupdf) OR Vision path (PNG → Claude)
              ──▶ Extract claims + assets + ISI ──▶ Deduplicate ──▶ Embed ──▶ Store
```

### Generation flow

```
1. Fetch claims + assets
2. Claude assembles HTML (claims verbatim in data-claim-id spans)
3. System appends ISI
4. 7 compliance checks
5. Save ContentVersion (append-only)
6. Save ComplianceRecord + audit log
7. Return version + compliance report
```

### State management

Zustand — one store, six slices. Rejected Context (re-renders on any change during streaming) and Redux (too much ceremony).

---

## 4. Data Model (3 min)

### Seven entities

```
User ──┐
       ├──▶ Project ──▶ ContentVersion ──▶ ComplianceRecord
       │                      │
Claim ─┤    Asset ────────────┘
       │
ClaimSource (claim ↔ citation)
```

Roles: editor (create/edit), reviewer (approve), admin (manage claims library)

### Three non-negotiable decisions

| Decision | Rationale |
|---|---|
| **ContentVersion is append-only** | Revert V5→V2 creates V6. FDA needs exact state at any point |
| **ComplianceRecords per version, not per project** | V5 non-compliant + V6 compliant = both records permanent |
| **Version DAG** | `parent_version_id` self-reference. Sequential numbering + actual edit path |

### Vector index choice

| | HNSW | IVFFlat |
|---|---|---|
| Training required | No | Yes |
| Small dataset performance | Good from day one | Poor without training |
| Scale ceiling | 500K+ | 500K+ |

pgvector over separate vector DB — 18 claims, single-digit ms at 50K, no sync/deployment overhead.

---

## 5. Live Demo (~5-10 min)

| Step | What to show | What to call out |
|---|---|---|
| 1. Create project | HCP email, efficacy + awareness | Dropdowns constrain everything downstream |
| 2. Complete brief | Structured inputs | Brief drives claim discovery via vector search |
| 3. Select claims | Relevance scores, fair balance warning | User controls what the LLM sees |
| 4. Generate | SSE streaming | `data-claim-id` spans in HTML, ISI appended by system |
| 5. AI edit | "Move safety above efficacy" | Compliance re-runs automatically |
| 6. Direct edit | Type unapproved text | ISI locked, compliance catches it |
| 7. Version timeline | Revert to earlier version | New version created, not overwrite |
| 8. Compliance panel | All 7 checks | Green/yellow/red with actionable messages |
| 9. Export | HTML + metadata + compliance report | Blocked unless all checks pass |

---

## 6. Product Thinking (3 min)

### 6-week roadmap

```
Sprint 1                    Sprint 2                      Sprint 3
Multi-channel + templates → Collaboration + approvals →   Analytics + claims management
```

### Five metrics

| Metric | Measures | Source |
|---|---|---|
| Time-to-compliant-export | End-to-end efficiency (north star) | `project.created_at` → first passing `ComplianceRecord` |
| First-attempt compliance pass rate | Claims-first effectiveness | V1 compliance results |
| Revision count per export | Editing friction (target <5) | `MAX(version_number)` per project |
| Claims library coverage | Discovery UX quality | Distinct claims used vs. total library |
| Compliance failure breakdown | Systemic vs. behavioral issues | Aggregated check failure frequency |

### With more time

- Approval workflow (editor → medical → legal → final)
- Richer compliance (grammar, channel limits, prominence analysis)
- Caching (embeddings by brief hash, compliance by content hash)
- Observability (structured LLM call logging, check durations)

### Lessons learned

- **contentEditable + React** — surrender DOM ownership, capture state at boundaries
- **PDF ingestion** — classify by extractable text ratio before choosing extraction path
- **Compliance scoping** — semantic similarity is not textual fidelity in a regulatory context
