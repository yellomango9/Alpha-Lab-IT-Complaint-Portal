-- Start transaction for atomicity
START TRANSACTION;

-- Insert Departments
INSERT INTO departments (name) VALUES 
('IT'),
('HR'),
('Finance');

-- Insert Roles
INSERT INTO roles (name) VALUES 
('User'),
('Engineer'),
('AMC_Admin'),
('Admin');

-- Insert Complaint Types
INSERT INTO complaint_types (name) VALUES 
('Hardware'),
('Software'),
('Network'),
('Peripheral Devices'),
('Data Transfer'),
('Others');

-- Insert Statuses
INSERT INTO statuses (name) VALUES 
('Open'),
('In Progress'),
('Resolved'),
('Closed');

-- Insert Sample Users (replace hashes with your generated pbkdf2_sha256 hashes)
INSERT INTO users (username, password_hash, email, full_name, role_id, department_id) VALUES
('user1', '$pbkdf2-sha256$29000$MSakVMoZQwjBuDcmBACAkA$m/OEIdgJkIMJiS0HqLsQLdnehI8e9gyYRgto5nfkoVc', 'user1@drdo.com', 'Test User', 1, 1), -- User, HR
('engineer1', '$pbkdf2-sha256$29000$rxXiPIeQEmKsNUYIoTTmXA$/uu/ReiFZ90N07D7JuItGMR7ONFlkEiWlCxhN40tllU', 'engineer1@drdo.com', 'Test Engg', 2, 1), -- Engineer, IT
('amc1', '$pbkdf2-sha256$29000$TikFQGiN0ZqTUgrh3Pu/tw$BDK34IsM1VEjzlw9vvdmVKBdltAMDjYcDWWxRbdFiWU', 'amc1@drdo.com', 'Test Amc', 3, 1), -- AMC_Admin, Finance
('admin1', '$pbkdf2-sha256$29000$vLdWSkmJce59j3EOYWztvQ$MEPzbXlXx3KUNEiJJirMqIaqYu1nM/pBvReu07c0hkA', 'admin1@drdo.com', 'Test Admin', 4, 1); -- Admin, IT

-- Insert Sample Complaints
INSERT INTO complaints (user_id, type_id, status_id, assigned_to_user_id, title, description, created_at, updated_at) VALUES
(1, 1, 1, NULL, 'Laptop Failure', 'Laptop won’t boot.', '2025-07-24 10:00:00', '2025-07-24 10:00:00'),
(1, 3, 2, 2, 'Network Issue', 'Cannot connect to Wi-Fi.', '2025-07-24 10:15:00', '2025-07-24 10:20:00'),
(1, 2, 3, 2, 'Software Crash', 'Application freezes on startup.', '2025-07-24 10:30:00', '2025-07-24 10:35:00');

-- Insert File Attachments
INSERT INTO file_attachments (complaint_id, file_name, file_path, uploaded_at) VALUES
(1, 'laptop_error_screenshot.png', '/uploads/complaints/1/screenshot.png', '2025-07-24 10:05:00'),
(2, 'network_log.txt', '/uploads/complaints/2/log.txt', '2025-07-24 10:20:00');

-- Insert Feedbacks
INSERT INTO feedbacks (complaint_id, rating, comment, submitted_at) VALUES
(3, 4, 'Resolved quickly, great service!', '2025-07-24 10:36:00'),
(3, 3, 'Took longer than expected.', '2025-07-24 10:36:00');

-- Insert FAQs
INSERT INTO faqs (question, answer) VALUES
('How do I reset my password?', 'Contact the IT department via the portal.'),
('What to do if my laptop crashes?', 'File a complaint under Hardware with a detailed description.'),
('How to check complaint status?', 'Log in and view your complaints in the dashboard.');

-- Commit transaction
COMMIT;
