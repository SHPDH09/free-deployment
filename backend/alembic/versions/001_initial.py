"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.String(512), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    op.create_table(
        'github_accounts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('github_id', sa.String(50), nullable=False),
        sa.Column('github_username', sa.String(255), nullable=False),
        sa.Column('access_token_encrypted', sa.Text(), nullable=False),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scopes', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('github_id'),
    )

    op.create_table(
        'projects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('github_repo_full_name', sa.String(512), nullable=False),
        sa.Column('github_repo_id', sa.String(50), nullable=True),
        sa.Column('default_branch', sa.String(255), nullable=False, server_default='main'),
        sa.Column('framework', sa.String(100), nullable=True),
        sa.Column('root_directory', sa.String(512), nullable=False, server_default='.'),
        sa.Column('build_command', sa.String(512), nullable=True),
        sa.Column('install_command', sa.String(512), nullable=True),
        sa.Column('output_directory', sa.String(512), nullable=True),
        sa.Column('start_command', sa.String(512), nullable=True),
        sa.Column('node_version', sa.String(50), nullable=True),
        sa.Column('python_version', sa.String(50), nullable=True),
        sa.Column('deployment_type', sa.String(50), nullable=False, server_default='static'),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('active_deployment_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])
    op.create_index('ix_projects_slug', 'projects', ['slug'])

    op.create_table(
        'project_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('auto_deploy', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('preview_deployments', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('build_timeout_seconds', sa.Integer(), nullable=False, server_default='600'),
        sa.Column('max_memory_mb', sa.Integer(), nullable=False, server_default='512'),
        sa.Column('max_cpu', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('health_check_path', sa.String(255), nullable=False, server_default='/'),
        sa.Column('health_check_timeout', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id'),
    )

    op.create_table(
        'deployments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('commit_sha', sa.String(40), nullable=True),
        sa.Column('commit_message', sa.Text(), nullable=True),
        sa.Column('branch', sa.String(255), nullable=False),
        sa.Column('author_name', sa.String(255), nullable=True),
        sa.Column('author_email', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('build_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('deployment_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('is_production', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_preview', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deployment_url', sa.String(512), nullable=True),
        sa.Column('preview_url', sa.String(512), nullable=True),
        sa.Column('container_id', sa.String(128), nullable=True),
        sa.Column('container_name', sa.String(255), nullable=True),
        sa.Column('build_duration_ms', sa.Integer(), nullable=True),
        sa.Column('deploy_duration_ms', sa.Integer(), nullable=True),
        sa.Column('total_duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('health_check_status', sa.String(50), nullable=True),
        sa.Column('health_check_response_ms', sa.Integer(), nullable=True),
        sa.Column('triggered_by', sa.String(50), nullable=False, server_default='manual'),
        sa.Column('worker_id', sa.String(128), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_deployments_project_id', 'deployments', ['project_id'])
    op.create_index('ix_deployments_status', 'deployments', ['status'])

    op.create_table(
        'deployment_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('deployment_id', sa.UUID(), nullable=False),
        sa.Column('level', sa.String(20), nullable=False, server_default='info'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('step', sa.String(100), nullable=True),
        sa.Column('is_user_visible', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['deployment_id'], ['deployments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_deployment_logs_deployment_id', 'deployment_logs', ['deployment_id'])

    op.create_table(
        'deployment_artifacts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('deployment_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('storage_path', sa.String(1024), nullable=False),
        sa.Column('s3_key', sa.String(1024), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('checksum', sa.String(64), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['deployment_id'], ['deployments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'domains',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verification_token', sa.String(128), nullable=True),
        sa.Column('verification_method', sa.String(50), nullable=True),
        sa.Column('dns_records', postgresql.JSONB(), nullable=True),
        sa.Column('ssl_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('ssl_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cloudflare_record_id', sa.String(128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain'),
    )
    op.create_index('ix_domains_project_id', 'domains', ['project_id'])

    op.create_table(
        'environment_variables',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value_encrypted', sa.Text(), nullable=False),
        sa.Column('environment', sa.String(50), nullable=False, server_default='production'),
        sa.Column('is_secret', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'key', 'environment', name='uq_env_var_project_key_env'),
    )
    op.create_index('ix_env_vars_project_id', 'environment_variables', ['project_id'])

    op.create_table(
        'build_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('deployment_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('worker_id', sa.String(128), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('queued_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['deployment_id'], ['deployments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_build_jobs_status', 'build_jobs', ['status'])

    op.create_table(
        'workers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('worker_id', sa.String(128), nullable=False),
        sa.Column('hostname', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='idle'),
        sa.Column('current_job_id', sa.UUID(), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cpu_usage', sa.Float(), nullable=True),
        sa.Column('memory_usage', sa.Float(), nullable=True),
        sa.Column('jobs_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('jobs_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('worker_id'),
    )

    op.create_table(
        'resource_usage',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('deployment_id', sa.UUID(), nullable=True),
        sa.Column('cpu_percent', sa.Float(), nullable=True),
        sa.Column('memory_mb', sa.Float(), nullable=True),
        sa.Column('memory_limit_mb', sa.Float(), nullable=True),
        sa.Column('disk_mb', sa.Float(), nullable=True),
        sa.Column('network_rx_bytes', sa.BigInteger(), nullable=True),
        sa.Column('network_tx_bytes', sa.BigInteger(), nullable=True),
        sa.Column('container_status', sa.String(50), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deployment_id'], ['deployments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_resource_usage_project_id', 'resource_usage', ['project_id'])

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.UUID(), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('resource_usage')
    op.drop_table('workers')
    op.drop_table('build_jobs')
    op.drop_table('environment_variables')
    op.drop_table('domains')
    op.drop_table('deployment_artifacts')
    op.drop_table('deployment_logs')
    op.drop_table('deployments')
    op.drop_table('project_settings')
    op.drop_table('projects')
    op.drop_table('github_accounts')
    op.drop_table('users')
