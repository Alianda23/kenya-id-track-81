-- Fix for missing lost_id_application_id column in documents table
USE digital_id_system;

-- Check if the column exists and add it if it doesn't
SET @column_exists = 0;
SELECT COUNT(*) INTO @column_exists 
FROM information_schema.columns 
WHERE table_schema = 'digital_id_system' 
AND table_name = 'documents' 
AND column_name = 'lost_id_application_id';

-- Add the column if it doesn't exist
SET @sql = IF(@column_exists = 0, 
    'ALTER TABLE documents ADD COLUMN lost_id_application_id INT NULL AFTER application_id',
    'SELECT "Column lost_id_application_id already exists" AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add the foreign key constraint if the column was just added
SET @fk_exists = 0;
SELECT COUNT(*) INTO @fk_exists 
FROM information_schema.key_column_usage 
WHERE table_schema = 'digital_id_system' 
AND table_name = 'documents' 
AND column_name = 'lost_id_application_id'
AND referenced_table_name = 'lost_id_applications';

SET @sql = IF(@fk_exists = 0 AND @column_exists = 0, 
    'ALTER TABLE documents ADD FOREIGN KEY (lost_id_application_id) REFERENCES lost_id_applications(id) ON DELETE CASCADE',
    'SELECT "Foreign key already exists or was not needed" AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;