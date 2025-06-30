-- ATLAS Database Master Initialization Script
-- This script creates all databases and users for ATLAS system
-- Run this as PostgreSQL superuser (e.g., postgres user)

-- Create databases
CREATE DATABASE atlas_main;
CREATE DATABASE atlas_agents;  
CREATE DATABASE atlas_memory;

-- Create users with passwords
CREATE USER atlas_main_user WITH PASSWORD 'atlas_main_password';
CREATE USER atlas_agents_user WITH PASSWORD 'atlas_agents_password'; 
CREATE USER atlas_memory_user WITH PASSWORD 'atlas_memory_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE atlas_main TO atlas_main_user;
GRANT ALL PRIVILEGES ON DATABASE atlas_agents TO atlas_agents_user;
GRANT ALL PRIVILEGES ON DATABASE atlas_memory TO atlas_memory_user;

-- Grant users ability to create schemas and extensions in their databases
\c atlas_main
GRANT CREATE ON DATABASE atlas_main TO atlas_main_user;
ALTER USER atlas_main_user CREATEDB;

\c atlas_agents  
GRANT CREATE ON DATABASE atlas_agents TO atlas_agents_user;
ALTER USER atlas_agents_user CREATEDB;

\c atlas_memory
GRANT CREATE ON DATABASE atlas_memory TO atlas_memory_user;
ALTER USER atlas_memory_user CREATEDB;

-- Switch back to default database
\c postgres

-- Display completion message
SELECT 'ATLAS databases and users created successfully!' as status;
SELECT 'Next steps:' as instruction;
SELECT '1. Run init_atlas_main.sql on atlas_main database' as step_1;
SELECT '2. Run init_atlas_agents.sql on atlas_agents database' as step_2;
SELECT '3. Run init_atlas_memory.sql on atlas_memory database' as step_3;