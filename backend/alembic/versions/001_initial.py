"""Initial migration - create all tables

Revision ID: 001
Revises: None
Create Date: 2026-02-17
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Enum types
    userrole = sa.Enum("admin", "editor", "viewer", name="userrole", create_type=True)
    claimcategory = sa.Enum(
        "efficacy", "safety", "mechanism", "dosing", "indication",
        "survival", "response_rate", "biomarker", "combination", "quality_of_life",
        name="claimcategory", create_type=True,
    )
    assettype = sa.Enum("image", "video", "document", "infographic", name="assettype", create_type=True)
    contenttype = sa.Enum("email", "banner_ad", "social_post", "website", "brochure", name="contenttype", create_type=True)
    audience = sa.Enum("hcp", "patient", "caregiver", "payer", name="audience", create_type=True)
    goal = sa.Enum("awareness", "education", "conversion", "retention", name="goal", create_type=True)
    tone = sa.Enum("professional", "empathetic", "urgent", "optimistic", name="tone", create_type=True)
    projectstatus = sa.Enum("draft", "in_review", "approved", "exported", name="projectstatus", create_type=True)
    compliancestatus = sa.Enum("pass", "fail", "warning", name="compliancestatus", create_type=True)
    eventtype = sa.Enum(
        "project_created", "version_created", "content_generated",
        "content_edited", "compliance_run", "comment_added", "exported",
        name="eventtype", create_type=True,
    )

    # --- Tables in FK-safe order ---

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("role", userrole, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # claims
    op.create_table(
        "claims",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("category", claimcategory, nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # claim_sources
    op.create_table(
        "claim_sources",
        sa.Column("claim_id", sa.String(), sa.ForeignKey("claims.id"), primary_key=True),
        sa.Column("source_id", sa.String(), primary_key=True),
    )

    # approved_assets
    op.create_table(
        "approved_assets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("asset_type", assettype, nullable=False),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # projects
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("content_type", contenttype, nullable=False),
        sa.Column("audience", audience, nullable=False),
        sa.Column("goal", goal, nullable=False),
        sa.Column("tone", tone, nullable=False),
        sa.Column("status", projectstatus, nullable=False),
        sa.Column("brief_responses", sa.JSON(), nullable=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # content_versions
    op.create_table(
        "content_versions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("parent_version_id", sa.String(), sa.ForeignKey("content_versions.id"), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("html_content", sa.Text(), nullable=False),
        sa.Column("edit_instruction", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "version_number", name="uq_project_version"),
    )

    # content_version_claims
    op.create_table(
        "content_version_claims",
        sa.Column("content_version_id", sa.String(), sa.ForeignKey("content_versions.id"), primary_key=True),
        sa.Column("claim_id", sa.String(), sa.ForeignKey("claims.id"), primary_key=True),
    )

    # content_version_assets
    op.create_table(
        "content_version_assets",
        sa.Column("content_version_id", sa.String(), sa.ForeignKey("content_versions.id"), primary_key=True),
        sa.Column("approved_asset_id", sa.String(), sa.ForeignKey("approved_assets.id"), primary_key=True),
    )

    # compliance_records
    op.create_table(
        "compliance_records",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("content_version_id", sa.String(), sa.ForeignKey("content_versions.id"), nullable=False),
        sa.Column("check_name", sa.String(255), nullable=False),
        sa.Column("status", compliancestatus, nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # comments
    op.create_table(
        "comments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("content_version_id", sa.String(), sa.ForeignKey("content_versions.id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("parent_comment_id", sa.String(), sa.ForeignKey("comments.id"), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("anchor_selector", sa.String(500), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # audit_logs (append-only, no updated_at)
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("event_type", eventtype, nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # HNSW index for vector similarity search
    op.create_index(
        "ix_claims_embedding_hnsw",
        "claims",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    # FK indexes (PostgreSQL does not auto-index FK columns)
    op.create_index("ix_projects_user_id", "projects", ["user_id"])
    op.create_index("ix_content_versions_project_id", "content_versions", ["project_id"])
    op.create_index("ix_comments_content_version_id", "comments", ["content_version_id"])
    op.create_index("ix_compliance_records_content_version_id", "compliance_records", ["content_version_id"])

    # Append-only trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_update_delete()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'Updates not allowed on append-only table %', TG_TABLE_NAME;
            ELSIF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Deletes not allowed on append-only table %', TG_TABLE_NAME;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Apply triggers to append-only tables
    op.execute("""
        CREATE TRIGGER trg_content_versions_append_only
        BEFORE UPDATE OR DELETE ON content_versions
        FOR EACH ROW EXECUTE FUNCTION prevent_update_delete();
    """)

    op.execute("""
        CREATE TRIGGER trg_audit_logs_append_only
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_update_delete();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_append_only ON audit_logs")
    op.execute("DROP TRIGGER IF EXISTS trg_content_versions_append_only ON content_versions")
    op.execute("DROP FUNCTION IF EXISTS prevent_update_delete()")

    # Drop indexes
    op.drop_index("ix_compliance_records_content_version_id", table_name="compliance_records")
    op.drop_index("ix_comments_content_version_id", table_name="comments")
    op.drop_index("ix_content_versions_project_id", table_name="content_versions")
    op.drop_index("ix_projects_user_id", table_name="projects")
    op.drop_index("ix_claims_embedding_hnsw", table_name="claims")

    # Drop tables in reverse FK order
    op.drop_table("audit_logs")
    op.drop_table("comments")
    op.drop_table("compliance_records")
    op.drop_table("content_version_assets")
    op.drop_table("content_version_claims")
    op.drop_table("content_versions")
    op.drop_table("projects")
    op.drop_table("approved_assets")
    op.drop_table("claim_sources")
    op.drop_table("claims")
    op.drop_table("users")

    # Drop enum types
    for name in [
        "eventtype", "compliancestatus", "projectstatus", "tone", "goal",
        "audience", "contenttype", "assettype", "claimcategory", "userrole",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {name}")

    # Drop extension
    op.execute("DROP EXTENSION IF EXISTS vector")
