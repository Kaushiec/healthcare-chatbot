# PART 8 — Healthcare chatbot hospital-only MySQL database

## Scope and provenance
This package was derived from the **four PDF files provided in the chat**:
- MRM Doctors_list & info..pdf (MRM staff, departments, facilities, contact)
- MRM Services_and_Charges F1.docx.pdf (MRM rate transcription; 10 pages)
- Aie afa Medlife BM Hospital (1).pdf (Aie Afa hospital summary; 2 pages)
- Nilachal Hospital & Research centre.pdf (Nilachal summary; 4 pages)

The source PDFs are NOT included: use your originals. All source-page numbers refer to these specific PDFs. No online sources were used.

### Parsed/imported records
- Hospitals: **3**
- Named care providers: **40** (MRM 25 incl. one physiotherapy provider listed as Mr., Aie Afa 14, Nilachal 1)
- Medical service/tariff entries: **693** (MRM 616, Aie Afa 5, Nilachal 72)
- Missing prices: **5** (Aie Afa 3, Nilachal 2)
- Needs-review marked tariff entries: **12** (MRM 6+ and alternative labels)
- Bed/accommodation rows: **16** (MRM 5, Aie Afa 7, Nilachal 4)
- Review flags: **31**
- MRM tariff PDF contains 619 numbered entries; **3 are accommodation rates** and were placed in hospital_bed_types, leaving **616** service entries.

### Data safeguards
- All collection/last-verified dates are NULL because the PDFs do not provide verification dates.
- Unknown current vacancies and prices are NULL, not zero.
- Null geographic coordinates and missing street addresses are intentional; only MRM lists a precise address.
- 'Kokrajhar' for Aie Afa and Nilachal is project context, **not an address verified in their PDFs**.
- 'On Call' is departmental availability information; no invented names are stored for on-call doctors.
- Prices and descriptions are preserved from the PDF transcription even when they seem odd.
- MRM alternative listings/asterisks, the mismatch in one doctor's department/qualification, and Aie cabin mapping are flagged for review.
- Accommodation rates for Aie Afa are labelled per_night **based on the user's supplied explanation**, while that period is not explicitly printed in the PDF.
- Do not present these tariffs or bed counts as live/current clinical or pricing information without re-verification.

## For a NEW database (recommended)
1. Make a backup of any earlier MySQL database first. The scripts do **not** remove anything; the schema script intentionally uses CREATE TABLE without IF NOT EXISTS so an existing-table conflict stops execution.
2. In MySQL Workbench, inspect `SHOW DATABASES;` and `SHOW TABLES;` for healthcare_chatbot.
3. If healthcare_chatbot already contains tables from an earlier lesson, **do not run the root SQL files against those tables**; the columns may differ. Instead use the ready-made files in `SAFE_OPTION_existing_database/`, which target the separate `healthcare_chatbot_v2` database. They do not overwrite the previous healthcare_chatbot tables. When the new DB is verified, change `MYSQL_DATABASE=healthcare_chatbot_v2` in your `.env` when you reach the database-connection part.
4. Execute `01_create_schema.sql` in your selected set (all statements, lightning bolt for entire script).
5. Execute `02_insert_hospital_data.sql` from the same selected set **once only** against the freshly created schema. It inserts IDs explicitly to make relations reliable.
6. Execute `03_verify_import.sql` from the selected set and confirm 3 hospitals, 40 providers, 693 service rate rows and 16 accommodation rows.
7. Explore `04_search_examples.sql` from the selected set.
8. Review `issues_to_verify.csv` and `all_service_rates_for_review.csv` against the original PDFs before publishing healthcare price data.

## MySQL Workbench practical tips
- To open: `File > Open SQL Script`, select the .sql file. Inspect the first lines before executing.
- Execute all: use the plain lightning bolt toolbar button (or Ctrl+Shift+Enter depending on Workbench).
- Refresh 'Schemas' in the Navigator to see new tables.
- `USE healthcare_chatbot;` sets active database for the current query tab.
- `DESCRIBE hospitals;` shows column definitions; `SELECT * FROM hospitals;` shows rows.
- Rows being added does NOT mean that real-time availability has been verified.

## Understanding the relationships
`hospital_service_rates` -> `medical_services` and `hospitals` + `source_documents`.
`hospital_bed_types` -> `hospitals` + `source_documents`.
`hospital_doctors` -> `doctors` + `departments` + `hospitals`.
`hospital_facilities` -> `facilities` + `hospitals`.
`hospital_departments` -> `departments` + `hospitals`.
There is NO pharmacy stock or medicine inventory table in Part 8. A hospital's 24x7 in-house pharmacy can still be a facility.

## Next implementation stage
After SQL verification, connect Python's mysql-connector to this database. Make API endpoints for hospitals, doctors, services, fees and beds; only then route LLM-extracted intents to vetted parameterized queries. Never allow LLM-generated arbitrary SQL to run.
