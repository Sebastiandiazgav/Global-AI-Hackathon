-- MyAgent - PostgreSQL Initialization Script
-- This runs automatically when the Docker container starts for the first time

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
