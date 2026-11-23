-- PART 8 | HOSPITAL-ONLY DATABASE, MySQL 8.0.16+ / 8.4+
-- Non-destructive to unrelated databases; intentionally fails on conflicts with existing tables.
-- Read README FIRST. Make a backup if healthcare_chatbot contains previous tables.
CREATE DATABASE IF NOT EXISTS healthcare_chatbot
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE healthcare_chatbot;

CREATE TABLE hospitals (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(200) NOT NULL UNIQUE,
 address VARCHAR(350) NULL,
 city VARCHAR(100) NULL,
 phone VARCHAR(100) NULL,
 alternate_phone VARCHAR(100) NULL,
 email VARCHAR(150) NULL,
 latitude DECIMAL(10,7) NULL,
 longitude DECIMAL(10,7) NULL,
 emergency_24x7 BOOLEAN NULL,
 ambulance_24x7 BOOLEAN NULL,
 general_open_24x7 BOOLEAN NULL,
 total_beds_min INT NULL,
 total_beds_max INT NULL,
 capacity_notes TEXT NULL,
 location_notes TEXT NULL,
 CHECK (total_beds_min IS NULL OR total_beds_min >= 0),
 CHECK (total_beds_max IS NULL OR total_beds_max >= 0),
 CHECK (total_beds_min IS NULL OR total_beds_max IS NULL OR total_beds_min <= total_beds_max)
) ENGINE=InnoDB;

CREATE TABLE source_documents (
 id INT AUTO_INCREMENT PRIMARY KEY,
 hospital_id INT NOT NULL,
 original_filename VARCHAR(255) NOT NULL,
 source_kind VARCHAR(100) NULL,
 page_count INT NULL,
 collected_on DATE NULL,  -- unknown: do not invent a collection date
 notes TEXT NULL,
 FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE departments (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(130) NOT NULL UNIQUE
) ENGINE=InnoDB;
CREATE TABLE hospital_departments (
 hospital_id INT NOT NULL,
 department_id INT NOT NULL,
 availability_type ENUM('listed','on_call','visiting','scheduled','unknown') NOT NULL DEFAULT 'listed',
 availability_notes TEXT NULL,
 source_document_id INT NULL,
 source_page INT NULL,
 PRIMARY KEY (hospital_id, department_id),
 FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE RESTRICT,
 FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE RESTRICT,
 FOREIGN KEY (source_document_id) REFERENCES source_documents(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE doctors (
 id INT AUTO_INCREMENT PRIMARY KEY,
 display_name VARCHAR(180) NOT NULL,
 qualifications TEXT NULL,
 provider_type ENUM('physician_or_unspecified','other_care_provider') NOT NULL DEFAULT 'physician_or_unspecified',
 name_notes TEXT NULL,
 INDEX ix_doctor_name(display_name)
) ENGINE=InnoDB;
CREATE TABLE hospital_doctors (
 id INT AUTO_INCREMENT PRIMARY KEY,
 hospital_id INT NOT NULL,
 doctor_id INT NOT NULL,
 department_id INT NULL,
 consultation_fee DECIMAL(10,2) NULL,
 availability_notes TEXT NULL,
 source_document_id INT NULL,
 source_page INT NULL,
 UNIQUE KEY uq_doctor_hospital_department(hospital_id, doctor_id, department_id),
 FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE RESTRICT,
 FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE RESTRICT,
 FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
 FOREIGN KEY (source_document_id) REFERENCES source_documents(id) ON DELETE SET NULL,
 CHECK (consultation_fee IS NULL OR consultation_fee >= 0)
) ENGINE=InnoDB;

CREATE TABLE facilities (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(170) NOT NULL UNIQUE
) ENGINE=InnoDB;
CREATE TABLE hospital_facilities (
 hospital_id INT NOT NULL,
 facility_id INT NOT NULL,
 source_label VARCHAR(220) NULL,
 availability_notes TEXT NULL,
 source_document_id INT NULL,
 source_page INT NULL,
 PRIMARY KEY(hospital_id, facility_id),
 FOREIGN KEY(hospital_id) REFERENCES hospitals(id) ON DELETE RESTRICT,
 FOREIGN KEY(facility_id) REFERENCES facilities(id) ON DELETE RESTRICT,
 FOREIGN KEY(source_document_id) REFERENCES source_documents(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE hospital_bed_types (
 id INT AUTO_INCREMENT PRIMARY KEY,
 hospital_id INT NOT NULL,
 bed_type VARCHAR(170) NOT NULL,
 reported_bed_count INT NULL,
 reported_room_count INT NULL,
 available_beds INT NULL,   -- NULL = unreported, NOT zero
 price_min DECIMAL(10,2) NULL,
 price_max DECIMAL(10,2) NULL,
 price_unit ENUM('per_night','per_day','unknown') NOT NULL DEFAULT 'unknown',
 source_document_id INT NULL,
 source_page INT NULL,
 source_label VARCHAR(220) NULL,
 notes TEXT NULL,
 FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE RESTRICT,
 FOREIGN KEY (source_document_id) REFERENCES source_documents(id) ON DELETE SET NULL,
 CHECK(reported_bed_count IS NULL OR reported_bed_count >= 0),
 CHECK(reported_room_count IS NULL OR reported_room_count >= 0),
 CHECK(available_beds IS NULL OR available_beds >= 0),
 CHECK(price_min IS NULL OR price_min >= 0),
 CHECK(price_max IS NULL OR price_max >= 0),
 CHECK(price_min IS NULL OR price_max IS NULL OR price_min <= price_max)
) ENGINE=InnoDB;

CREATE TABLE medical_services (
 id INT AUTO_INCREMENT PRIMARY KEY,
 source_name VARCHAR(255) NOT NULL,
 category VARCHAR(110) NOT NULL,
 comparison_key VARCHAR(120) NULL, -- optional; assign only after confirming equivalence
 UNIQUE KEY uq_service_name_category(category, source_name),
 INDEX ix_service_name(source_name),
 INDEX ix_service_comparison_key(comparison_key)
) ENGINE=InnoDB;
CREATE TABLE hospital_service_rates (
 id INT AUTO_INCREMENT PRIMARY KEY,
 hospital_id INT NOT NULL,
 service_id INT NOT NULL,
 source_document_id INT NOT NULL,
 source_page INT NULL,
 source_section VARCHAR(150) NULL,
 source_item_number INT NULL,
 price_min DECIMAL(10,2) NULL,
 price_max DECIMAL(10,2) NULL,
 fee_unit VARCHAR(70) NOT NULL DEFAULT 'unspecified',
 original_price_text VARCHAR(120) NULL,
 price_status ENUM('quoted','missing','needs_review') NOT NULL,
 notes TEXT NULL,
 last_verified DATE NULL,  -- no dates in sources; do NOT set to NOW()
 FOREIGN KEY(hospital_id) REFERENCES hospitals(id) ON DELETE RESTRICT,
 FOREIGN KEY(service_id) REFERENCES medical_services(id) ON DELETE RESTRICT,
 FOREIGN KEY(source_document_id) REFERENCES source_documents(id) ON DELETE RESTRICT,
 INDEX ix_rates_hospital_service(hospital_id,service_id),
 CHECK(price_min IS NULL OR price_min>=0),
 CHECK(price_max IS NULL OR price_max>=0),
 CHECK(price_min IS NULL OR price_max IS NULL OR price_min<=price_max)
) ENGINE=InnoDB;

CREATE TABLE data_review_flags (
 id INT AUTO_INCREMENT PRIMARY KEY,
 hospital_id INT NOT NULL,
 source_document_id INT NULL,
 source_page INT NULL,
 issue_type VARCHAR(70) NOT NULL,
 description TEXT NOT NULL,
 resolved BOOLEAN NOT NULL DEFAULT FALSE,
 FOREIGN KEY(hospital_id) REFERENCES hospitals(id) ON DELETE RESTRICT,
 FOREIGN KEY(source_document_id) REFERENCES source_documents(id) ON DELETE SET NULL
) ENGINE=InnoDB;
