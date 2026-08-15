"""Add render deployment models

Revision ID: render_v84
Revises: 
Create Date: 2026-08-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'render_v84'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Subscription tiers
    op.create_table('subscription_tiers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('price', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('features', sa.Text(), nullable=True),
        sa.Column('max_contracts', sa.Integer(), nullable=True),
        sa.Column('max_clients', sa.Integer(), nullable=True),
        sa.Column('ai_requests_per_day', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_subscription_tiers_slug'), 'subscription_tiers', ['slug'], unique=True)

    # Achievements
    op.create_table('achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('points', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_achievements_slug'), 'achievements', ['slug'], unique=True)

    # User achievements
    op.create_table('user_achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('earned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'achievement_id', name='uq_user_achievement')
    )

    # FAQs
    op.create_table('faqs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('views', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Blog posts
    op.create_table('blog_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=100), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('featured_image', sa.String(length=255), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('views', sa.Integer(), nullable=True),
        sa.Column('likes', sa.Integer(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_blog_posts_slug'), 'blog_posts', ['slug'], unique=True)

    # Blog comments
    op.create_table('blog_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('author_name', sa.String(length=100), nullable=True),
        sa.Column('author_email', sa.String(length=100), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_approved', sa.Boolean(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['blog_comments.id'], ),
        sa.ForeignKeyConstraint(['post_id'], ['blog_posts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Svetlana knowledge
    op.create_table('svetlana_knowledge',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(length=100), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_svetlana_knowledge_topic'), 'svetlana_knowledge', ['topic'], unique=False)

    # Marketplace items
    op.create_table('marketplace_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('images', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('views', sa.Integer(), nullable=True),
        sa.Column('sales_count', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Numeric(precision=2, scale=1), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_marketplace_items_slug'), 'marketplace_items', ['slug'], unique=True)

    # Grants
    op.create_table('grants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('organization', sa.String(length=200), nullable=True),
        sa.Column('amount_min', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('amount_max', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('ai_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_grants_slug'), 'grants', ['slug'], unique=True)

    # User grant applications
    op.create_table('user_grant_applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('grant_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('application_data', sa.Text(), nullable=True),
        sa.Column('ai_recommendation', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['grant_id'], ['grants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'grant_id', name='uq_user_grant')
    )


def downgrade():
    op.drop_table('user_grant_applications')
    op.drop_index(op.f('ix_grants_slug'), table_name='grants')
    op.drop_table('grants')
    op.drop_index(op.f('ix_marketplace_items_slug'), table_name='marketplace_items')
    op.drop_table('marketplace_items')
    op.drop_index(op.f('ix_svetlana_knowledge_topic'), table_name='svetlana_knowledge')
    op.drop_table('svetlana_knowledge')
    op.drop_table('blog_comments')
    op.drop_index(op.f('ix_blog_posts_slug'), table_name='blog_posts')
    op.drop_table('blog_posts')
    op.drop_table('faqs')
    op.drop_table('user_achievements')
    op.drop_index(op.f('ix_achievements_slug'), table_name='achievements')
    op.drop_table('achievements')
    op.drop_index(op.f('ix_subscription_tiers_slug'), table_name='subscription_tiers')
    op.drop_table('subscription_tiers')
