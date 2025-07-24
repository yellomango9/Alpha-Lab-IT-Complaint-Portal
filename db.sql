-- Create database
CREATE DATABASE IF NOT EXISTS alpha_lab_it_portal;
USE alpha_lab_it_portal;

-- Departments
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Roles
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    role_id INT NOT NULL,
    department_id INT,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- Complaint Types
CREATE TABLE complaint_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Statuses
CREATE TABLE statuses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Complaints
CREATE TABLE complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type_id INT NOT NULL,
    status_id INT NOT NULL,
    assigned_to_user_id INT,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (type_id) REFERENCES complaint_types(id),
    FOREIGN KEY (status_id) REFERENCES statuses(id),
    FOREIGN KEY (assigned_to_user_id) REFERENCES users(id)
);

-- File Attachments
CREATE TABLE file_attachments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    file_name VARCHAR(255),
    file_path VARCHAR(512),
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(id)
);

-- Feedbacks
CREATE TABLE feedbacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    rating TINYINT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(id)
);

-- FAQs
CREATE TABLE faqs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question VARCHAR(512) NOT NULL,
    answer TEXT NOT NULL
);

