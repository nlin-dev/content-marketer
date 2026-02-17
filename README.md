# Content Marketer

Pharmaceutical content generation platform for FDA-compliant marketing emails. Marketers select pre-approved clinical claims from an indexed library, pick approved visual assets, and the system assembles them into formatted HTML. A deterministic compliance engine validates everything before export.

The system never invents medical claims. The LLM is a formatter that arranges citation-backed, approved text into structured HTML with `data-claim-id` spans. Compliance checking runs entirely through rule-based validators with zero AI dependencies.

## Quick start

```
cp .env.example .env
# Add your OPENAI_API_KEY and ANTHROPIC_API_KEY

docker compose up -d
```

Backend runs at `localhost:8000`. Seed the database:

```
docker compose exec api python -c "from app.seed import seed_database; import asyncio; asyncio.run(seed_database())"
```

This ingests two source PDFs through the extraction pipeline, generates embeddings for 18 FRUZAQLA claims, and populates approved assets + ISI content.

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI, Python 3.12, SQLAlchemy async, Alembic |
| Database | PostgreSQL 16, pgvector (HNSW index, 1536-dim embeddings) |
| Frontend | Next.js 14 (App Router), TypeScript strict, Tailwind, Zustand |
| External APIs | Claude (content assembly), OpenAI (embeddings) |
| Auth | `X-User-Id` header (MVP scope, no OAuth) |

## Architecture

The backend is organized into four layers:

**Ingestion** (`app/ingestion/`) parses source PDFs into structured data. Text PDFs go through pymupdf extraction. Image-only PDFs (raster pages, no selectable text) get rendered to PNG and sent to Claude's vision API. The pipeline routes each PDF automatically based on extractable text density.

- `pdf_parser.py` -- text extraction + page-to-image rendering
- `claim_extractor.py` -- claim extraction via Claude (text or vision)
- `asset_extractor.py` -- visual asset identification from page images
- `isi_extractor.py` -- ISI HTML from prescribing info sections
- `pipeline.py` -- orchestrates classify > extract > deduplicate > embed

**Services** (`app/services/`) contain all business logic:

- `embedding.py` -- OpenAI embeddings with lazy client singleton
- `claim_retrieval.py` -- pgvector cosine distance search
- `claim_validator.py` -- difflib SequenceMatcher sliding window (zero AI imports)
- `llm_assembly.py` -- Claude-powered generation with verbatim claim enforcement
- `compliance.py` -- 7 deterministic checks: ISI present, fair balance, claim matching, unapproved content detection (0.65 threshold), claim statuses, asset compliance, channel spec. Zero AI imports.
- `orchestrator.py` -- ties it all together: discover > generate > validate > persist. Handles NL edits, direct edits, asset swaps, reverts. Auto-appends ISI, sanitizes HTML via nh3.
- `audit.py` -- append-only event log

**Routes** (`app/routes/`) expose the REST API:

| Route | Purpose |
|-------|---------|
| `GET /users/me` | Current user |
| `POST /projects` | Create project (content type, audience, goal, tone) |
| `GET /claims/discover/{project_id}` | Semantic claim discovery from brief |
| `GET /claims/search?q=` | Free-text claim search |
| `POST /content/generate/stream` | SSE streaming content generation |
| `POST /content/edit` | NL instruction editing |
| `POST /content/direct-edit` | Raw HTML edit (nh3-sanitized) |
| `POST /content/swap-asset` | Replace an asset in generated content |
| `POST /content/revert` | DAG-preserving version revert |
| `POST /export/{version_id}` | JSON bundle (blocked if non-compliant) |
| `GET /content/versions/{project_id}` | Version history |
| `POST /comments` | Threaded comments per version |

**Models** (`app/models/`) define the data layer. `ContentVersion` and `AuditLog` are append-only (FDA audit trail). The version model forms a DAG through `parent_version_id`, so reverting from V5 to V2 creates V6 with parent=V5 and V2's content.

## Key design decisions

**Claims-first generation.** The LLM receives only selected pre-approved claims as input. It can't hallucinate medical content because it never gets asked to produce any. Generated HTML wraps each claim in `<span data-claim-id="...">` for downstream validation.

**Deterministic compliance.** The compliance engine imports only `re`, `dataclasses`, `enum`, `bs4`, `sqlalchemy`, and `difflib`. No AI libraries touch the validation path. This is a regulatory requirement: you need to be able to explain exactly why content passed or failed.

**Dual retrieval strategy.** Semantic search (pgvector cosine distance) powers claim discovery during authoring. Exact matching (difflib SequenceMatcher) powers post-generation validation to confirm the LLM used claims verbatim.

**Append-only versioning.** Content versions never get updated or deleted. Every edit creates a new version linked to its parent, preserving full audit history. The orchestrator checks version currency before writes.

**ISI auto-append.** Important Safety Information is extracted from prescribing info PDFs and auto-appended to every generated version. It's marked `data-isi="true" data-editable="false"` and locked from editing.

## Development

Run tests:

```
cd backend && python -m pytest tests/ -v
```

The test suite covers PDF parsing, claim extraction, asset extraction, embedding behavior, and security regressions (wildcard injection, auth guards).

## Project structure

```
backend/
  app/
    ingestion/     # PDF parsing and extraction pipeline
    models/        # SQLAlchemy ORM (User, Claim, Project, ContentVersion, etc.)
    routes/        # FastAPI routers
    schemas/       # Pydantic request/response contracts
    services/      # Business logic (orchestrator, compliance, LLM assembly)
    config.py      # Pydantic settings from env
    database.py    # Async SQLAlchemy engine + session
    dependencies.py # FastAPI deps (get_db, get_current_user)
    main.py        # App factory, CORS, router wiring, static mount
    seed.py        # Database population from source PDFs
  fixtures/        # Source PDFs for ingestion
  tests/
  alembic/         # Migration scripts
frontend/
  # Next.js 14 App Router
```
