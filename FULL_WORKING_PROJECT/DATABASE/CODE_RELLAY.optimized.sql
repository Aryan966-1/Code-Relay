-- CODE_RELLAY.optimized.sql
-- Target dialect: PostgreSQL (portable ANSI-first style where practical)
-- Re-runnable schema + constraints + indexes + full-text search triggers

BEGIN;

-- Drop in dependency-safe order
DROP TABLE IF EXISTS article_tags;
DROP TABLE IF EXISTS article_versions;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS conversations;
DROP TABLE IF EXISTS articles;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS memberships;
DROP TABLE IF EXISTS workspaces;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workspaces (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    created_by BIGINT NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE memberships (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workspace_id BIGINT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'MEMBER' CHECK (role IN ('OWNER', 'ADMIN', 'MEMBER', 'VIEWER')),
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, workspace_id)
);

CREATE TABLE articles (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    created_by BIGINT REFERENCES users(id),
    current_version INTEGER NOT NULL DEFAULT 1 CHECK (current_version >= 1),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE article_versions (
    id BIGSERIAL PRIMARY KEY,
    article_id BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL CHECK (version_number >= 1),
    content TEXT NOT NULL,
    created_by BIGINT REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    search_vector tsvector,
    UNIQUE (article_id, version_number)
);

CREATE TABLE tags (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    UNIQUE (workspace_id, name)
);

CREATE TABLE article_tags (
    article_id BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    tag_id BIGINT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, tag_id)
);

CREATE TABLE conversations (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    title TEXT,
    created_by BIGINT REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id BIGINT REFERENCES users(id),
    content TEXT NOT NULL,
    parent_message_id BIGINT REFERENCES messages(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    search_vector tsvector
);

-- FK and query-path indexes
CREATE INDEX idx_memberships_user_id ON memberships(user_id);
CREATE INDEX idx_memberships_workspace_id ON memberships(workspace_id);

CREATE INDEX idx_articles_workspace_id ON articles(workspace_id);
CREATE INDEX idx_articles_created_by ON articles(created_by);
CREATE INDEX idx_articles_workspace_status ON articles(workspace_id, status);

CREATE INDEX idx_article_versions_article_id ON article_versions(article_id);
CREATE INDEX idx_article_versions_created_by ON article_versions(created_by);

CREATE INDEX idx_tags_workspace_id ON tags(workspace_id);

CREATE INDEX idx_conversations_workspace_id ON conversations(workspace_id);
CREATE INDEX idx_conversations_created_by ON conversations(created_by);

CREATE INDEX idx_messages_conversation_created_at ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_parent_message_id ON messages(parent_message_id);

-- Full-text trigger functions
CREATE OR REPLACE FUNCTION article_search_vector_update()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION message_search_vector_update()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Full-text triggers
CREATE TRIGGER trg_article_search_update
BEFORE INSERT OR UPDATE ON article_versions
FOR EACH ROW
EXECUTE FUNCTION article_search_vector_update();

CREATE TRIGGER trg_message_search_update
BEFORE INSERT OR UPDATE ON messages
FOR EACH ROW
EXECUTE FUNCTION message_search_vector_update();

-- Full-text indexes
CREATE INDEX idx_article_versions_search ON article_versions USING GIN (search_vector);
CREATE INDEX idx_messages_search ON messages USING GIN (search_vector);

COMMIT;

-- Example ranked search query:
-- SELECT
--     article_id,
--     version_number,
--     content,
--     ts_rank(search_vector, to_tsquery('payment & bug')) AS rank
-- FROM article_versions
-- WHERE search_vector @@ to_tsquery('payment & bug')
-- ORDER BY rank DESC;
