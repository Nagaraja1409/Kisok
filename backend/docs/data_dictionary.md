# School CSV data dictionary

Each CSV uses a header row and UTF-8 encoding. Dates use ISO `YYYY-MM-DD`; monetary amounts are INR values stored without currency symbols. `record_id` fields are stable demo identifiers used in AI source citations.

| File | Purpose | Key fields |
|---|---|---|
| students.csv | Student identity and summary metrics | student_id, class_name, attendance, fee_balance |
| parents.csv | Parent-to-child link | parent_id, child_student_id, mobile |
| teachers.csv | Staff profile and teaching context | staff_id, department, assigned_class |
| alumni.csv | Community profile | alumni_id, connection, last_engagement |
| timetable.csv | Period schedule | record_id, class_name, subject, time, room |
| homework.csv | Subject work | record_id, subject, assignment, assigned, due, status |
| attendance.csv | Attendance register and summary | record_id, date, status, periods |
| fees.csv | Installment schedule | record_id, installment, amount, due_date, status |
| fee_payments.csv | Payment ledger | receipt, date, amount, mode, reference |
| exams.csv / exam_scores.csv | Exams and results | subject, date, session, score, grade |
| library_books.csv | Library catalogue | book_id, title, rack, floor, availability |
| events.csv / notices.csv | School communication | id, title, date, time, venue/location |
| sports.csv | Activities | sport_id, sport, next_event, venue |
| hostel.csv | Residential context | room, fee_balance, warden |
| inventory.csv / hrms.csv | Teacher/staff tools | asset or staff record, status, value |
| admissions.csv / preadmissions.csv | Admission guidance | reference, documents, status, next_step |
| campus_facilities.csv | Public campus information | facility, location, hours |
| notifications.csv | Role-aware updates | notification_id, role, title, date |

## Future ERP adapter

`CsvSchoolDataRepository` is the working implementation. `ErpApiSchoolDataRepository` is the replacement seam. The AI layer must consume the `SchoolContext` contract rather than reading CSV files directly.
