-- Initial database schema for Canon Builder metadata
-- This will be run automatically by PostgreSQL on first startup

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    canon_status VARCHAR(50) NOT NULL DEFAULT 'canonical',
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    description TEXT,
    chunk_count INTEGER DEFAULT 0,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document tags
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    parent_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document-tag associations
CREATE TABLE IF NOT EXISTS document_tags (
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, tag_id)
);

-- Proposals table
CREATE TABLE IF NOT EXISTS proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    coherence_score FLOAT,
    status VARCHAR(50) NOT NULL DEFAULT 'proposed',
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by UUID REFERENCES users(id)
);

-- Proposal sources (supporting canonical documents)
CREATE TABLE IF NOT EXISTS proposal_sources (
    proposal_id UUID REFERENCES proposals(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    relevance_score FLOAT,
    PRIMARY KEY (proposal_id, document_id)
);

-- Contradictions table
CREATE TABLE IF NOT EXISTS contradictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    description TEXT NOT NULL,
    severity VARCHAR(50) NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by UUID REFERENCES users(id),
    resolution_text TEXT
);

-- Contradiction documents (which documents are involved)
CREATE TABLE IF NOT EXISTS contradiction_documents (
    contradiction_id UUID REFERENCES contradictions(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    statement TEXT,
    PRIMARY KEY (contradiction_id, document_id)
);

-- Audit log for all canonization actions
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Session state (user preferences, feature toggles)
CREATE TABLE IF NOT EXISTS session_state (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    preferences JSONB DEFAULT '{}',
    feature_toggles JSONB DEFAULT '{}',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_canon_status ON documents(canon_status);
CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);
CREATE INDEX IF NOT EXISTS idx_proposals_user ON proposals(user_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_resolved ON contradictions(resolved);
CREATE INDEX IF NOT EXISTS idx_contradictions_severity ON contradictions(severity);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);

-- Insert demo user for MVP
INSERT INTO users (id, username, email, hashed_password)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'demo',
    'demo@canon-builder.local',
    '$2b$12$KIX/QoQdVqmqKjEjXjGcPe7qF8F5qN5Z5qZ5Z5qZ5qZ5qZ5qZ5qZq'  -- password: demo
)
ON CONFLICT (username) DO NOTHING;
