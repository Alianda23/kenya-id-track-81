-- Fix for documents table foreign key constraints
USE digital_id_system;

-- First, drop existing foreign key constraints to rebuild them properly
SET FOREIGN_KEY_CHECKS = 0;

-- Drop the documents table and recreate it with proper structure
DROP TABLE IF EXISTS documents;

CREATE TABLE documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NULL,
    lost_id_application_id INT NULL,
    document_type ENUM('passport_photo', 'fingerprints', 'birth_certificate', 'parent_id_front', 'parent_id_back', 'ob_photo', 'new_passport_photo', 'birth_cert_photo') NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
    FOREIGN KEY (lost_id_application_id) REFERENCES lost_id_applications(id) ON DELETE CASCADE,
    
    -- Ensure at least one of the foreign keys is set
    CONSTRAINT chk_application_type CHECK (
        (application_id IS NOT NULL AND lost_id_application_id IS NULL) OR
        (application_id IS NULL AND lost_id_application_id IS NOT NULL)
    )
);

SET FOREIGN_KEY_CHECKS = 1;