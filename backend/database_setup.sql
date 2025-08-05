-- Digital ID System Database Schema
-- Run this SQL script in your MySQL database

CREATE DATABASE IF NOT EXISTS digital_id_system;
USE digital_id_system;

-- Officers table (for application officers)
CREATE TABLE IF NOT EXISTS officers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_number VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    station VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Admins table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Applications table (for ID applications)
CREATE TABLE IF NOT EXISTS applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_number VARCHAR(50) UNIQUE NOT NULL,
    officer_id INT,
    application_type ENUM('new', 'renewal') NOT NULL,
    
    -- Personal Information
    full_names VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender ENUM('male', 'female') NOT NULL,
    father_name VARCHAR(100) NOT NULL,
    mother_name VARCHAR(100) NOT NULL,
    marital_status ENUM('single', 'married', 'divorced', 'widowed'),
    husband_name VARCHAR(100) NULL,
    husband_id_no VARCHAR(20) NULL,
    
    -- Location Information  
    district_of_birth VARCHAR(100) NOT NULL,
    tribe VARCHAR(100) NOT NULL,
    clan VARCHAR(100),
    family VARCHAR(100),
    home_district VARCHAR(100) NOT NULL,
    division VARCHAR(100) NOT NULL,
    constituency VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    sub_location VARCHAR(100) NOT NULL,
    village_estate VARCHAR(100) NOT NULL,
    home_address VARCHAR(255),
    occupation VARCHAR(100) NOT NULL,
    
    -- Supporting Documents (JSON field for document info)
    supporting_documents JSON,
    
    -- For renewals
    existing_id_number VARCHAR(20) NULL,
    renewal_reason ENUM('lost', 'damaged', 'expired') NULL,
    
    -- Application status
    status ENUM('submitted', 'approved', 'rejected', 'dispatched', 'ready_for_collection', 'collected') DEFAULT 'submitted',
    
    -- Generated ID number (after approval)
    generated_id_number VARCHAR(20) UNIQUE NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (officer_id) REFERENCES officers(id)
);

-- Documents table (for storing file paths of uploaded documents)
CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NULL,
    lost_id_application_id INT NULL,
    document_type ENUM('passport_photo', 'fingerprints', 'birth_certificate', 'parent_id_front', 'parent_id_back', 'ob_photo', 'new_passport_photo', 'birth_cert_photo') NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
    FOREIGN KEY (lost_id_application_id) REFERENCES lost_id_applications(id) ON DELETE CASCADE
);

-- Citizens table (for storing existing citizen data from approved applications)
CREATE TABLE IF NOT EXISTS citizens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_number VARCHAR(20) UNIQUE NOT NULL,
    full_names VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    place_of_birth VARCHAR(100) NOT NULL,
    gender ENUM('male', 'female') NOT NULL,
    nationality VARCHAR(50) DEFAULT 'Kenyan',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Lost ID Applications table
CREATE TABLE IF NOT EXISTS lost_id_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    waiting_card_number VARCHAR(50) UNIQUE NOT NULL,
    citizen_id_number VARCHAR(20) NOT NULL,
    officer_id INT NOT NULL,
    ob_number VARCHAR(50) NOT NULL,
    ob_description TEXT NOT NULL,
    payment_method ENUM('cash', 'mpesa') NOT NULL,
    payment_amount DECIMAL(10, 2) DEFAULT 1000.00,
    status ENUM('submitted', 'approved', 'rejected', 'dispatched', 'ready_for_collection', 'collected') DEFAULT 'submitted',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (officer_id) REFERENCES officers(id),
    FOREIGN KEY (citizen_id_number) REFERENCES citizens(id_number)
);

-- Payments table (for renewal payments)
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NULL,
    lost_id_application_id INT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method ENUM('cash', 'mpesa') NOT NULL,
    mpesa_transaction_id VARCHAR(50) NULL,
    status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (application_id) REFERENCES applications(id),
    FOREIGN KEY (lost_id_application_id) REFERENCES lost_id_applications(id)
);

-- Status history table (for tracking status changes)
CREATE TABLE IF NOT EXISTS status_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_by_admin_id INT NULL,
    changed_by_officer_id INT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    
    FOREIGN KEY (application_id) REFERENCES applications(id),
    FOREIGN KEY (changed_by_admin_id) REFERENCES admins(id),
    FOREIGN KEY (changed_by_officer_id) REFERENCES officers(id)
);

-- Insert default admin user
INSERT IGNORE INTO admins (username, full_name, password_hash) 
VALUES ('admin', 'System Administrator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewfT1bfaXHOGTCK2');
-- Default username: 'admin', password: 'admin123' - change this immediately

-- Create indexes for better performance (skip if they already exist)
CREATE INDEX IF NOT EXISTS idx_officers_email ON officers(email);
CREATE INDEX IF NOT EXISTS idx_officers_status ON officers(status);
CREATE INDEX IF NOT EXISTS idx_applications_number ON applications(application_number);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_officer ON applications(officer_id);
CREATE INDEX IF NOT EXISTS idx_documents_application ON documents(application_id);
CREATE INDEX IF NOT EXISTS idx_citizens_id_number ON citizens(id_number);
CREATE INDEX IF NOT EXISTS idx_lost_id_applications_citizen ON lost_id_applications(citizen_id_number);
CREATE INDEX IF NOT EXISTS idx_lost_id_applications_officer ON lost_id_applications(officer_id);
CREATE INDEX IF NOT EXISTS idx_lost_id_applications_status ON lost_id_applications(status);