-- Initialize database with pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create index for vector similarity search
-- This will be created by the application as needed
