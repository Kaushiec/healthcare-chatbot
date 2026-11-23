-- Run AFTER 01 and 02; confirms every source was imported.
USE healthcare_chatbot;
SHOW TABLES;
SELECT COUNT(*) AS hospitals FROM hospitals;                  -- 3
SELECT COUNT(*) AS providers FROM doctors;                    -- 40 named people (incl. one Mr. in physiotherapy)
SELECT COUNT(*) AS service_rate_rows FROM hospital_service_rates; -- 693
SELECT COUNT(*) AS accommodation_rows FROM hospital_bed_types;   -- 16
SELECT COUNT(*) AS reviewed_items FROM data_review_flags;
SELECT h.name, COUNT(r.id) AS service_entries
FROM hospitals h LEFT JOIN hospital_service_rates r ON r.hospital_id=h.id
GROUP BY h.id,h.name ORDER BY h.id;
-- Expected: MRM=616, Aie=5, Nilachal=72
SELECT h.name, COUNT(DISTINCT hd.doctor_id) AS named_providers
FROM hospitals h LEFT JOIN hospital_doctors hd ON hd.hospital_id=h.id
GROUP BY h.id,h.name ORDER BY h.id;
-- Expected: MRM=25, Aie=14, Nilachal=1
SELECT h.name, h.total_beds_min,h.total_beds_max,
       b.bed_type,b.reported_bed_count,b.reported_room_count,
       b.available_beds,b.price_min,b.price_max,b.price_unit
FROM hospitals h LEFT JOIN hospital_bed_types b ON b.hospital_id=h.id
ORDER BY h.id,b.id;
SELECT d.name, hd.availability_type, hd.availability_notes
FROM hospital_departments hd JOIN departments d ON d.id=hd.department_id
WHERE hd.hospital_id=3 ORDER BY d.name;
-- Unknown prices must remain unknown, not ₹0.
SELECT h.name,m.source_name,r.source_page,r.price_min,r.price_status
FROM hospital_service_rates r
JOIN hospitals h ON h.id=r.hospital_id
JOIN medical_services m ON m.id=r.service_id
WHERE r.price_status='missing' ORDER BY h.name,m.source_name;
-- Find possible wrong amounts (not proof of correct prices).
SELECT * FROM hospital_service_rates WHERE price_min < 0 OR price_max < price_min;
