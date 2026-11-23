-- Common chatbot database searches (run in Workbench for Part 8 verification).
USE healthcare_chatbot;

-- 1. Hospital profiles: addresses left NULL when unavailable.
SELECT id,name,city,phone,total_beds_min,total_beds_max FROM hospitals;

-- 2. Named providers at Aie Afa, with department and original qualifications.
SELECT h.name AS hospital,d.display_name,dp.name AS department,d.qualifications
FROM hospital_doctors hd JOIN hospitals h ON h.id=hd.hospital_id
JOIN doctors d ON d.id=hd.doctor_id
LEFT JOIN departments dp ON dp.id=hd.department_id
WHERE h.id=2 ORDER BY dp.name,d.display_name;

-- 3. Find on-call departments at Nilachal: NO fake doctor records.
SELECT d.name,hd.availability_type
FROM hospital_departments hd JOIN departments d ON d.id=hd.department_id
WHERE hd.hospital_id=3 AND hd.availability_type='on_call';

-- 4. Hospitals with CT scan facility, only if stated in facilities source.
SELECT h.name,f.name AS facility
FROM hospital_facilities hf JOIN hospitals h ON h.id=hf.hospital_id
JOIN facilities f ON f.id=hf.facility_id
WHERE f.name='CT Scan';

-- 5. Compare only exactly named services until a manually approved comparison_key exists.
-- For example, MRM's 'Complete Blood Count (CBC)' and Nilachal's 'CBC' are
-- separate catalogue items; do NOT silently equate test contents/inclusions.
SELECT h.name,m.source_name,r.price_min,r.price_max,r.fee_unit,
       sd.original_filename,r.source_page
FROM hospital_service_rates r
JOIN hospitals h ON h.id=r.hospital_id
JOIN medical_services m ON m.id=r.service_id
JOIN source_documents sd ON sd.id=r.source_document_id
WHERE m.source_name LIKE '%CBC%' OR m.source_name LIKE '%Complete Blood Count%'
ORDER BY r.price_min;

-- 6. Cheapest listed exact test entry (not necessarily equivalent to other test variants).
SELECT h.name,m.source_name,r.price_min,r.fee_unit
FROM hospital_service_rates r
JOIN hospitals h ON h.id=r.hospital_id
JOIN medical_services m ON m.id=r.service_id
WHERE m.source_name='Widal test' AND r.price_status='quoted'
ORDER BY r.price_min;

-- 7. Accommodation rates with explicit periods and unknown capacities.
SELECT h.name,b.bed_type,b.reported_bed_count,b.reported_room_count,
       b.price_min,b.price_max,b.price_unit,b.notes
FROM hospital_bed_types b JOIN hospitals h ON h.id=b.hospital_id
ORDER BY h.name,b.bed_type;

-- 8. Tariff entries requiring manual verification.
SELECT h.name,m.source_name,r.original_price_text,r.source_page,r.notes
FROM hospital_service_rates r JOIN hospitals h ON h.id=r.hospital_id
JOIN medical_services m ON m.id=r.service_id
WHERE r.price_status='needs_review';
