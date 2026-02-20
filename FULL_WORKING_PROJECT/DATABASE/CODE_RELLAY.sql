CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- INSERT INTO users (name, email, password_hash)
-- VALUES ('Test User', 'test@example.com', 'dummyhash');

-- SELECT * FROM users;
-- -----------------------------------------------------------
-- -----------------------------------------------------------


CREATE TABLE workspaces (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    created_by BIGINT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SELECT * FROM workspaces;
-- INSERT INTO workspaces (name, created_by)
-- VALUES ('Test Workspace', 1);

-- memberships (RBAC backbone)

CREATE TABLE memberships (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    workspace_id BIGINT REFERENCES workspaces(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'MEMBER'
		CHECK (role IN ('OWNER','ADMIN','MEMBER','VIEWER')),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, workspace_id)
);



-- INSERT INTO memberships (user_id, workspace_id, role)
-- VALUES (2, 3, 'OWNER');

-- SELECT * FROM memberships;
-- --------------------------------------------------------

CREATE TABLE articles (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT REFERENCES workspaces(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
    created_by BIGINT REFERENCES users(id),
    current_version INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
);





--  ARTICLE VERSION --
CREATE TABLE article_versions (
    id BIGSERIAL PRIMARY KEY,
    article_id BIGINT REFERENCES articles(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    content TEXT NOT NULL,
    created_by BIGINT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(article_id, version_number)
);


-- ///////////////////////////-------

CREATE TABLE tags (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    UNIQUE(workspace_id, name)
);




--////////////////////////////////------


-- Create article_tags Table (many-to-many)

CREATE TABLE article_tags (
    article_id BIGINT REFERENCES articles(id) ON DELETE CASCADE,
    tag_id BIGINT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY(article_id, tag_id)
);

-- ------------------CORE LOGIC AND TESTING--------------------------------------


ALTER TABLE article_versions
ADD COLUMN search_vector tsvector;

-- TRIGGER FUNCTION CREATION--

CREATE OR REPLACE FUNCTION article_search_vector_update()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        to_tsvector('english', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


--  ATTACHING THE TRIGGER --

CREATE TRIGGER trg_article_search_update
BEFORE INSERT OR UPDATE ON article_versions
FOR EACH ROW
EXECUTE FUNCTION article_search_vector_update();


-- CREATE GIN INDEX --
CREATE INDEX idx_article_versions_search
ON article_versions
USING GIN (search_vector);

--  FOR TESTING ONLY --

-- INSERT INTO article_versions (article_id, version_number, content, created_by)
-- VALUES (1, 2, 'Payment bug fixed in checkout module', 1);

-- SELECT article_id, version_number, content
-- FROM article_versions
-- WHERE search_vector @@ to_tsquery('payment & bug');

-- ------------------------------------------------


-- RANKED SEARCHED QUERRY --

SELECT
    article_id,
    version_number,
    content,
    ts_rank(search_vector, to_tsquery('payment & bug')) AS rank
FROM article_versions
WHERE search_vector @@ to_tsquery('payment & bug')
ORDER BY rank DESC;



-- CLEAN ALL TABLE --
TRUNCATE TABLE
    article_tags,
    article_versions,
    articles,
    tags,
    memberships,
    workspaces,
    users
RESTART IDENTITY CASCADE;


-- -------------------------





CREATE TABLE conversations (
    id BIGSERIAL PRIMARY KEY,
    workspace_id BIGINT REFERENCES workspaces(id) ON DELETE CASCADE,
    title TEXT,
    created_by BIGINT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);





CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id BIGINT REFERENCES users(id),
    content TEXT NOT NULL,
    parent_message_id BIGINT REFERENCES messages(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



--  SEARCHING THE CHAT HISTORY --
ALTER TABLE messages
ADD COLUMN search_vector tsvector;


CREATE OR REPLACE FUNCTION message_search_vector_update()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        to_tsvector('english', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION message_search_vector_update()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        to_tsvector('english', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



CREATE TRIGGER trg_message_search_update
BEFORE INSERT OR UPDATE ON messages
FOR EACH ROW
EXECUTE FUNCTION message_search_vector_update();




CREATE INDEX idx_messages_search
ON messages
USING GIN (search_vector);

