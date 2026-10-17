from __future__ import annotations

from typing import Any

WELCOME_MESSAGE = (
    "Hello! I'm GREEN_AI, your smart campus assistant. "
    "I can help you explore the features available for your role. What would you like to do?"
)

ROLE_METADATA: dict[str, dict[str, str]] = {
    "student_parent": {
        "role_key": "student_parent",
        "role_label": "Student / Parent",
        "badge": "Academic & Learning Portal",
        "description": "Study assistance, subject explanations, learning guidance, exam preparation, homework support, and parent enquiries.",
        "primary_color": "#ea580c",
    },
    "teacher_staff": {
        "role_key": "teacher_staff",
        "role_label": "Teacher / Staff",
        "badge": "Academic Workspace & Faculty Hub",
        "description": "Teaching assistance, lesson preparation, academic support, administrative guidance, and staff workflows.",
        "primary_color": "#0d9488",
    },
    "visitor_applicant": {
        "role_key": "visitor_applicant",
        "role_label": "Visitor / Applicant",
        "badge": "Admissions & Campus Helpdesk",
        "description": "Campus guidance, admissions information, application tracking, visit planning, and visitor services.",
        "primary_color": "#0284c7",
    },
    "alumni_ex_employee": {
        "role_key": "alumni_ex_employee",
        "role_label": "Alumni / Ex-Employee",
        "badge": "Alumni & Legacy Network",
        "description": "Alumni events, batch reunions, networking, mentorship, career guidance, and official transcript requests.",
        "primary_color": "#7c3aed",
    },
}

ROLE_FEATURE_DEFINITIONS: dict[str, list[dict[str, Any]]] = {
    "student_parent": [
        {
            "id": "academic_guidance",
            "name": "Academic Assistance & Subject Explanations",
            "description": "Subject performance analysis, grades explanation, and academic diagnostics.",
            "icon": "GraduationCap",
            "sample_prompts": [
                "Show my recent exam scores and grades",
                "How can I improve my Science marks?",
                "Which subject needs the most attention?",
            ],
            "linked_agents": ["academic_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "attendance_monitoring",
            "name": "Attendance Tracking & Compliance",
            "description": "Track cumulative attendance percentage, absent days, and CBSE 75% compliance.",
            "icon": "UserCheck",
            "sample_prompts": [
                "What is my cumulative attendance rate?",
                "Am I at risk of falling below the 75% attendance threshold?",
                "Which dates was I marked absent?",
            ],
            "linked_agents": ["attendance_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "study_learning",
            "name": "Study Guidance & Library Resources",
            "description": "Library catalogue lookup, reading recommendations, and revision materials.",
            "icon": "BookOpen",
            "sample_prompts": [
                "Recommend library books for Class VIII Science",
                "What study resources are available for Mathematics?",
                "Where can I find Ruskin Bond books in the library?",
            ],
            "linked_agents": ["learning_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "exam_preparation",
            "name": "Exam Timetable & Schedule",
            "description": "Upcoming examinations, testing sessions, reporting hours, and room allotments.",
            "icon": "FileText",
            "sample_prompts": [
                "When is my next examination?",
                "Show the complete Term exam schedule",
                "What time do I need to report for the Math exam?",
            ],
            "linked_agents": ["exam_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "daily_timetable",
            "name": "Daily Class Timetable",
            "description": "Period-wise daily timetable, room locations, and teacher schedules.",
            "icon": "Calendar",
            "sample_prompts": [
                "What is my timetable for today?",
                "Who is teaching Science Lab period 3?",
                "Which classroom is English scheduled in?",
            ],
            "linked_agents": ["student_assistant_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "fee_ledger",
            "name": "Fee Schedule & Account Status",
            "description": "Fee installment dates, ledger statements, and outstanding balance status.",
            "icon": "CreditCard",
            "sample_prompts": [
                "What is my pending fee balance?",
                "Show my fee payment history and receipts",
                "When is the Term II fee installment due?",
            ],
            "linked_agents": ["fee_agent"],
            "status": "read_only",
            "data_mode": "grounded_csv",
        },
        {
            "id": "transport_services",
            "name": "Transport Routes & Bus Timing",
            "description": "School bus routes, pickup points, route timing, and driver coordination.",
            "icon": "Bus",
            "sample_prompts": [
                "What is the morning pickup time for Route 4?",
                "Which bus routes cover Green Park?",
                "Check transport schedule",
            ],
            "linked_agents": ["transport_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "circulars_notices",
            "name": "School Notices & Circulars",
            "description": "Official campus announcements, holiday circulars, and event circulars.",
            "icon": "Bell",
            "sample_prompts": [
                "Are there any new notices or circulars today?",
                "When is the Gandhi Jayanti holiday?",
                "Show recent school circulars",
            ],
            "linked_agents": ["notice_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "family_leave_support",
            "name": "Parent Enquiry & Leave Application Preview",
            "description": "Draft leave requests for approval and parent administrative support.",
            "icon": "HeartHandshake",
            "sample_prompts": [
                "Prepare a leave request for tomorrow due to illness",
                "How do I request a bonafide certificate for my child?",
            ],
            "linked_agents": ["family_support_agent"],
            "status": "preview_only",
            "data_mode": "grounded_csv",
        },
    ],
    "teacher_staff": [
        {
            "id": "teacher_copilot",
            "name": "Faculty Schedule & Classroom Copilot",
            "description": "Daily teaching schedule, period allocations, and classroom briefings.",
            "icon": "Clock",
            "sample_prompts": [
                "What is my teaching schedule for today?",
                "Which classroom is my next period?",
                "Summarize today's duty roster",
            ],
            "linked_agents": ["teacher_copilot_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "class_roster",
            "name": "Class Administration & Student Roster",
            "description": "Assigned class roster, section statistics, and student demographics.",
            "icon": "Users",
            "sample_prompts": [
                "Show class roster for Class VIII A",
                "Who are the students enrolled in my assigned section?",
            ],
            "linked_agents": ["class_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "attendance_analysis",
            "name": "Class Attendance Diagnostics & Risk Scoring",
            "description": "Statistical attendance analysis, chronic absenteeism alerts, and trends.",
            "icon": "Activity",
            "sample_prompts": [
                "Analyze attendance trends for Class VIII A",
                "Which students have chronic absence risk?",
                "What is the average attendance percentage this month?",
            ],
            "linked_agents": ["attendance_analysis_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "assessment_eval",
            "name": "Assessment Intelligence & Performance",
            "description": "Class exam scores, grade distributions, and weak topic identification.",
            "icon": "Award",
            "sample_prompts": [
                "Analyze recent exam scores for Class VIII A",
                "Identify weak topics in Mathematics for my class",
                "Generate subject score summary for Science",
            ],
            "linked_agents": ["assessment_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "lesson_planner",
            "name": "Lesson Preparation & Content Formulation",
            "description": "Pedagogical blueprints, lesson plans, classroom quizzes, and worksheets.",
            "icon": "BookOpen",
            "sample_prompts": [
                "Generate a 40-minute lesson plan for Photosynthesis",
                "Create a 5-question quick quiz on Fractions",
                "Suggest an interactive group activity for English literature",
            ],
            "linked_agents": ["lesson_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "staff_regulations",
            "name": "Institutional Policies & Bylaws",
            "description": "Academic bylaws, CBSE regulations, grading policies, and staff circulars.",
            "icon": "ShieldCheck",
            "sample_prompts": [
                "What is the school policy on continuous internal assessment?",
                "What are the CBSE guidelines for lab record evaluation?",
                "Search staff handbook for evaluation criteria",
            ],
            "linked_agents": ["staff_knowledge_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "hr_leave_management",
            "name": "Staff Leave & HR Balance Inquiries",
            "description": "Casual/medical leave balances and draft leave requisition preview.",
            "icon": "CalendarCheck",
            "sample_prompts": [
                "What is my casual leave balance?",
                "Draft a casual leave application for Friday",
            ],
            "linked_agents": ["hr_leave_agent"],
            "status": "preview_only",
            "data_mode": "grounded_csv",
        },
        {
            "id": "lab_teaching_resources",
            "name": "Lab Apparatus & Teaching Resources",
            "description": "Science lab apparatus catalog, reference textbooks, and inventory status.",
            "icon": "Cpu",
            "sample_prompts": [
                "Check availability of projectors in the Science department",
                "What reference textbooks are available in the central library?",
            ],
            "linked_agents": ["resource_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
    ],
    "visitor_applicant": [
        {
            "id": "admissions_guidance",
            "name": "Admissions Guidance & Eligibility",
            "description": "Admission criteria, age eligibility rules, curriculum details, and fee structure.",
            "icon": "HelpCircle",
            "sample_prompts": [
                "What is the admission procedure for Class VI?",
                "What is the age eligibility for Nursery and Class I?",
                "What is the annual fee structure for the ICSE stream?",
            ],
            "linked_agents": ["admission_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "application_status",
            "name": "Application & Enquiry Tracking",
            "description": "Track status of admissions enquiry BCE/ENQ/2026/114 and document checklist.",
            "icon": "CheckCircle2",
            "sample_prompts": [
                "Track status for enquiry BCE/ENQ/2026/114",
                "Which documents are still pending for my pre-admission application?",
                "Predict admission conversion likelihood for my enquiry",
            ],
            "linked_agents": ["application_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "visitor_helpdesk",
            "name": "Visitor Services & Information Desk",
            "description": "Reception hours, visitor pass guidelines, and front office services.",
            "icon": "Building2",
            "sample_prompts": [
                "What are the visitor desk hours?",
                "Where is the Front Office located on campus?",
                "What is the visitor check-in process?",
            ],
            "linked_agents": ["visitor_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "campus_navigation",
            "name": "Campus Navigation & Facilities Guide",
            "description": "Locations of laboratories, sports grounds, library, and auditoriums.",
            "icon": "Compass",
            "sample_prompts": [
                "Where is the Main Auditorium located?",
                "How do I reach the Science Laboratory from reception?",
                "What sports facilities are available on campus?",
            ],
            "linked_agents": ["campus_navigation_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "appointment_booking",
            "name": "Campus Visit & Admissions Appointment",
            "description": "Schedule a guided campus tour or meeting with Admissions Officer.",
            "icon": "Calendar",
            "sample_prompts": [
                "Book an appointment with the Admissions Officer",
                "Schedule a guided campus tour for next Tuesday",
            ],
            "linked_agents": ["appointment_agent"],
            "status": "preview_only",
            "data_mode": "grounded_csv",
        },
        {
            "id": "public_knowledge",
            "name": "Curriculum, Accreditations & FAQ",
            "description": "CBSE/ICSE affiliations, NAAC ratings, and general school overview.",
            "icon": "Info",
            "sample_prompts": [
                "What curriculum does Green Valley Public School follow?",
                "What are the school operating hours and timings?",
                "What are the school's accreditations and affiliations?",
            ],
            "linked_agents": ["public_knowledge_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
    ],
    "alumni_ex_employee": [
        {
            "id": "alumni_services",
            "name": "Alumni Services & School Connection",
            "description": "Alumni association benefits, newsletter subscriptions, and school legacy.",
            "icon": "Users",
            "sample_prompts": [
                "How can I register with the Green Valley Alumni Association?",
                "How can I contribute to school scholarships or development?",
            ],
            "linked_agents": ["alumni_assistant_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "reunion_events",
            "name": "Reunions & Founders Day Events",
            "description": "Annual Founders Day celebrations, batch reunions, and regional meetups.",
            "icon": "Calendar",
            "sample_prompts": [
                "When is the next Founders Day celebration?",
                "Are there any upcoming batch reunions scheduled?",
                "Show the schedule for alumni gatherings",
            ],
            "linked_agents": ["event_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "transcript_records",
            "name": "Transcript & Academic Archive Records",
            "description": "Official transcript preview, duplicate marksheets, and archive verification.",
            "icon": "FileText",
            "sample_prompts": [
                "How do I request an official graduation transcript?",
                "What is the procedure for obtaining a duplicate certificate?",
            ],
            "linked_agents": ["records_agent"],
            "status": "preview_only",
            "data_mode": "grounded_csv",
        },
        {
            "id": "mentorship_circle",
            "name": "Mentorship & Career Networking",
            "description": "Connect with current students for career guidance and alumni networking.",
            "icon": "Award",
            "sample_prompts": [
                "How can I volunteer to mentor graduating high school students?",
                "Connect with alumni working in Technology and Engineering",
            ],
            "linked_agents": ["community_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "hall_of_fame",
            "name": "Hall of Fame & Alumni Achievements",
            "description": "Notable alumni accomplishments, national honours, and school records.",
            "icon": "Trophy",
            "sample_prompts": [
                "Who are notable alumni from Green Valley Public School?",
                "Show Hall of Fame entries in technology and public service",
            ],
            "linked_agents": ["achievement_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
        {
            "id": "office_support",
            "name": "Ex-Employee Services & Administrative Records",
            "description": "Service certificates, retirement records, and administrative assistance.",
            "icon": "Building2",
            "sample_prompts": [
                "How can a former faculty member request an experience certificate?",
                "Contact administrative desk for ex-employee records",
            ],
            "linked_agents": ["office_support_agent"],
            "status": "live",
            "data_mode": "grounded_csv",
        },
    ],
}


def get_role_metadata(role: str) -> dict[str, str]:
    from app.core.security import SecurityValidator
    canonical = SecurityValidator.normalize_role(role)
    return ROLE_METADATA.get(canonical, ROLE_METADATA["visitor_applicant"])


def get_features_for_role(role: str) -> list[dict[str, Any]]:
    from app.core.security import SecurityValidator
    canonical = SecurityValidator.normalize_role(role)
    return ROLE_FEATURE_DEFINITIONS.get(canonical, ROLE_FEATURE_DEFINITIONS["visitor_applicant"])


def get_all_role_features() -> dict[str, list[dict[str, Any]]]:
    return ROLE_FEATURE_DEFINITIONS
