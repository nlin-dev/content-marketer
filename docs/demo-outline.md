# Content Marketer: Presentation Outline

---

## 1. My Thesis

- Two independent systems: generation (probabilistic) vs. compliance (deterministic)
- Rejected alternatives: RAG, free-form chat, template system

---

## 2. User Flow

```
Setup ──▶ Brief ──▶ Claims & Assets ──▶ Editor
```

| Step | Key point |
|---|---|
| Setup | 4 dropdowns, no AI |
| Brief | Structured questions, vector search |
| Claims & Assets | Explicit selection, fair balance warning |
| Editor | AI edit, direct edit, 7 compliance checks after every edit |

---

## 3. Architecture

```
Next.js 14 ──▶ FastAPI ──▶ Postgres 16 + pgvector
```

1. Core isolation rule
2. Two retrieval strategies: discovery (vector) vs. validation (string matching)
3. Ingestion pipeline: classify, extract, deduplicate, embed, store
4. Generation flow: 7 steps, fetch through compliance report
5. State management: Zustand, one store, six slices

---

## 4. Data Model

```
User ──┐
       ├──▶ Project ──▶ ContentVersion ──▶ ComplianceRecord
       │                      │
Claim ─┤    Asset ────────────┘
       │
ClaimSource (claim ↔ citation)
```

1. Three non-negotiable decisions: append-only versions, per-version compliance, version DAG
2. Roles: editor, reviewer, admin
3. Vector index: HNSW over IVFFlat, pgvector over separate DB

---

## 5. Live Demo


---

## 6. Product Direction

```
Sprint 1                    Sprint 2                      Sprint 3
Multi-channel + templates → Collaboration + approvals →   Analytics + claims management
```

- Five metrics: time-to-export, first-attempt pass rate, revision count, library coverage, failure breakdown
- With more time: approval workflow, richer compliance, caching, observability
- Lessons learned: PDF ingestion, compliance scoping
