-- Schema lưu lịch sử chat (PostgreSQL / Neon).
-- Bảng được tạo tự động khi backend khởi động (init_db), file này để tham khảo
-- hoặc chạy tay trong Neon SQL Editor.

CREATE TABLE IF NOT EXISTS chat_sessions (
    id          VARCHAR(64) PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          BIGSERIAL PRIMARY KEY,
    session_id  VARCHAR(64) NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role        VARCHAR(16) NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id_id
    ON chat_messages (session_id, id);
