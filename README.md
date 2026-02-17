# Content Marketer

Pharmaceutical content generation platform to create FDA-compliant marketing assets (emails, banners, social posts, slides) through a guided conversational interface. Pre-approved clinical claims are assembled into formatted content while a deterministic compliance engine grounds content against regulatory guardrails before final export.

Key constraint: the system never invents medical claims and simply arranges approved, citation-backed claims from an indexed library. Compliance checking is completely deterministic. Claim text matching, ISI presence, fair balance, and forbidden phrase detection all run through rule-based validators.

## System architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Next.js 14)                        │
│                                                                        │
│  ┌──────────────┐  ┌───────────────────┐  ┌────────────────────────┐   │
│  │ Project Setup │→│ Conversational    │→│ Claim Discovery &       │   │
│  │ Form         │  │ Brief Builder     │  │ Selection + Asset Picker│   │
│  └──────────────┘  └───────────────────┘  └────────────┬───────────┘   │
│                                                         │              │
│  ┌──────────────────────────────────────────────────────▼───────────┐  │
│  │                    Content Workspace                              │  │
│  │  ┌─────────────────┐  ┌──────────────┐  ┌───────────────────┐   │  │
│  │  │ HTML Preview     │  │ Edit Modes   │  │ Version Timeline  │   │  │
│  │  │ (live render +   │  │ ┌──────────┐ │  │ (DAG, revert,     │   │  │
│  │  │  contentEditable │  │ │ AI Edit  │ │  │  edited_by user)  │   │  │
│  │  │  inline editing) │  │ │ (NL bar) │ │  │                   │   │  │
│  │  │                  │  │ ├──────────┤ │  └───────────────────┘   │  │
│  │  │                  │  │ │ Direct   │ │  ┌───────────────────┐   │  │
│  │  │                  │  │ │ Edit     │ │  │ Comment Thread    │   │  │
│  │  │                  │  │ │ (inline) │ │  │ (threaded review) │   │  │
│  │  └─────────────────┘  │ └──────────┘ │  └───────────────────┘   │  │
│  │                        └──────────────┘                          │  │
│  │  ┌─────────────────┐  ┌──────────────────────────────────────┐  │  │
│  │  │ Compliance Panel │  │ Export Panel (HTML + metadata + ISI  │  │  │
│  │  │ (pass/warn/fail) │  │  + asset manifest, blocked if not   │  │  │
│  │  │                  │  │  compliant)                          │  │  │
│  │  └─────────────────┘  └──────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  State: Zustand    User: X-User-Id header (POC, no auth)              │
│  Proxy: /api/* → backend:8000                                          │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ REST + SSE (streaming generation)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI / Python 3.12)                  │
│                                                                        │
│  Routers                                                               │
│  ┌────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐ ┌────────┐ ┌───────┐ │
│  │/users  │ │/projects │ │/claims │ │/assets  │ │/content│ │/export│ │
│  └───┬────┘ └────┬─────┘ └───┬────┘ └────┬────┘ └───┬────┘ └───┬───┘ │
│      │           │           │           │          │           │      │
│      │    ┌──────┴───────────┴───────────┘          │           │      │
│      │    │    ┌─────────────────────┐  ┌───────────┘           │      │
│      │    │    │  /comments router   │  │                       │      │
│      │    │    └─────────┬───────────┘  │                       │      │
│      └────┴──────────────┴──────────────┴───────────────────────┘      │
│                                  │                                     │
│                                  ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      Orchestrator Service                        │  │
│  │  discover → generate → validate → persist                        │  │
│  │  + NL edit, direct edit, asset swap, revert                      │  │
│  │  + optimistic concurrency (version_id check)                     │  │
│  └──────┬──────────────┬───────────────┬──────────────┬──────────┘  │
│         │              │               │              │              │
│         ▼              ▼               ▼              ▼              │
│  ┌─────────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │ Claim       │ │ Content  │ │ Compliance   │ │ Audit        │    │
│  │ Retrieval   │ │ Assembly │ │ Engine       │ │ Service      │    │
│  │             │ │          │ │              │ │              │    │
│  │ pgvector    │ │ Claude   │ │ ZERO AI deps │ │ Append-only  │    │
│  │ semantic    │ │ formats  │ │ Rule-based:  │ │ event log    │    │
│  │ search      │ │ approved │ │ • ISI check  │ │ + user_id    │    │
│  │             │ │ claims + │ │ • Fair bal.  │ │              │    │
│  │ OpenAI      │ │ assets  │ │ • Claim match│ │              │    │
│  │ embeddings  │ │ into     │ │ • Unapproved │ │              │    │
│  │             │ │ HTML     │ │   content    │ │              │    │
│  │             │ │          │ │ • Asset check│ │              │    │
│  │             │ │          │ │ • Channel len│ │              │    │
│  └──────┬──────┘ └────┬─────┘ └──────┬───────┘ └──────────────┘    │
│         │              │               │                            │
│         ▼              │               ▼                            │
│  ┌─────────────┐       │        ┌──────────────┐                   │
│  │ Embedding   │       │        │ Claim        │                   │
│  │ Service     │       │        │ Validator    │                   │
│  │ (OpenAI)    │       │        │ (difflib     │                   │
│  └─────────────┘       │        │  exact match)│                   │
│                        │        └──────────────┘                   │
│                        │                                           │
└────────────────────────┼───────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     PostgreSQL 16 + pgvector                            │
│                                                                        │
│  ┌────────────┐ ┌────────────────┐ ┌──────────────────────────────┐   │
│  │ users      │ │ claims         │ │ content_versions             │   │
│  │ (role,     │ │ + embedding[]  │ │ (append-only)                │   │
│  │  display   │ │ + sources      │ │ + claim_links                │   │
│  │  name)     │ │ HNSW index     │ │ + asset_links                │   │
│  └────────────┘ └────────────────┘ │ + compliance_records         │   │
│                                     │ + edited_by (FK → users)     │   │
│  ┌────────────┐ ┌────────────────┐ └──────────────────────────────┘   │
│  │ approved   │ │ comments       │                                    │
│  │ _assets    │ │ (threaded,     │                                    │
│  │ (type,     │ │  per-version,  │                                    │
│  │  file_url, │ │  resolvable)   │                                    │
│  │  approval  │ └────────────────┘                                    │
│  │  _id)      │                                                       │
│  └────────────┘                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ audit_log (append-only, user-attributed)                         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

External APIs: Claude (content assembly) · OpenAI (embeddings)
Static assets: /static/assets/ (approved visual library served by backend)
```
