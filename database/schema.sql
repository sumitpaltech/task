-- ============================================================
--  TaskApp Database Schema
--  Drop and recreate cleanly
-- ============================================================

CREATE DATABASE IF NOT EXISTS `3IdeaTask` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `3IdeaTask`;

-- ----------------------------------------
-- Table: users
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100)    NOT NULL,
    username    VARCHAR(100)    NOT NULL,
    email       VARCHAR(150)    NOT NULL,
    password    VARCHAR(255)    NOT NULL,
    role        VARCHAR(50)     NOT NULL DEFAULT 'user',
    department  VARCHAR(100)    DEFAULT NULL,
    status      TINYINT(1)      NOT NULL DEFAULT 1,
    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------
-- Table: task_tracker
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS task_tracker (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    title           VARCHAR(200)    NOT NULL,
    description     TEXT,
    category        VARCHAR(100)    DEFAULT 'General',
    department      VARCHAR(100)    DEFAULT NULL,
    assigned_to     VARCHAR(100)    DEFAULT NULL,
    user_mail       VARCHAR(255)    DEFAULT NULL,
    team_member     VARCHAR(100)    DEFAULT NULL,
    priority        ENUM('low','medium','high') NOT NULL DEFAULT 'medium',
    start_date      DATE,
    due_date        DATE,
    completion_date DATE,
    status          ENUM('pending','in_progress','completed') NOT NULL DEFAULT 'pending',
    remarks         TEXT,
    file_attachment TEXT,
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_assigned_to (assigned_to),
    INDEX idx_department (department),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------
-- Seed: demo user  (password: password123)
-- ----------------------------------------
INSERT INTO users (name, username, email, password, role, department, status) VALUES
('Demo User', 'demo_user', 'demo@example.com',
 'pbkdf2:sha256:600000$example$hashedpassword', 'admin', 'Technical', 1);
 -- Run `python seed.py` to insert a properly hashed user instead.

-- ----------------------------------------
-- Seed: sample task_tracker rows
-- ----------------------------------------
INSERT INTO task_tracker (title, description, category, department, assigned_to, user_mail, team_member, priority, start_date, due_date, completion_date, status, remarks) VALUES
('Setup project environment', 'Install Python, Flask, MySQL', 'Development', 'Technical', 'demo_user', 'Demo Team', 'high', '2024-01-01', '2024-01-10', '2024-01-10', 'completed', 'Initial setup completed'),
('Design database schema', 'Create users and tasks tables', 'Planning', 'Technical', 'demo_user', 'demo@example.com', 'Demo Team', 'high', '2024-01-02', '2024-01-12', '2024-01-12', 'completed', 'Database model drafted'),
('Build auth system', 'Login, register, logout', 'Development', 'Technical', 'demo_user', 'demo@example.com', 'Demo Team', 'medium', '2024-01-05', '2024-01-20', NULL, 'in_progress', 'Auth system in progress'),
('Build task CRUD', 'Create, read, update, delete', 'Development', 'Technical', 'demo_user', 'demo@example.com', 'Demo Team', 'high', '2024-01-10', '2024-01-25', NULL, 'pending', 'CRUD UI and backend'),
('Deploy to production', 'Setup server and go live', 'Release', 'Technical', 'demo_user', 'demo@example.com', 'Demo Team', 'low', '2024-01-20', '2024-02-01', NULL, 'pending', 'Deployment preparation');
