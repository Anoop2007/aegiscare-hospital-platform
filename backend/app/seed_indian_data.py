from datetime import datetime, timedelta, timezone
import json
import secrets
from .database import query_one, query_all, execute_insert, execute_update
from .auth import hash_password

def seed_indian_entities():
    now_iso = datetime.now(timezone.utc).isoformat()
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Seed Indian Fictional Hospitals across all 8 required cities and localities
    hospitals_master = [
        # Chennai
        ("CareSync Apex Super-Specialty Hospital", "Chennai", "Adyar", "42 Lattice Bridge Road, Adyar, Chennai, Tamil Nadu 600020", "+91 44 2491 8000", 600.0,
         "24x7 Emergency • Interventional Cardiology • Multi-Specialty OPD • Organ Transplant", "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=600"),
        ("CareSync Mediversal Hospital", "Chennai", "Anna Nagar", "15 2nd Avenue, Anna Nagar, Chennai, Tamil Nadu 600040", "+91 44 2621 9000", 500.0,
         "24x7 Emergency • Neurology & Stroke Center • Trauma Unit • Dermatology Wing", "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=600"),
        ("CareSync Central Metro Hospital", "Chennai", "T Nagar", "12 Usman Road, T Nagar, Chennai, Tamil Nadu 600017", "+91 44 2815 4000", 550.0,
         "24x7 Emergency • Orthopedic Excellence • Women & Child Health", "https://images.unsplash.com/photo-1587351021759-3e566b6af7cc?w=600"),
        ("CareSync Coastal Care Hospital", "Chennai", "OMR", "Plot 88, Rajiv Gandhi Salai, OMR, Chennai, Tamil Nadu 600096", "+91 44 6620 5000", 650.0,
         "24x7 Emergency • Critical Care Pavilion • Robotic Surgery Center", "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=600"),
        ("CareSync South Health Campus", "Chennai", "Velachery", "5 Bypass Road, Velachery, Chennai, Tamil Nadu 600042", "+91 44 2244 3000", 500.0,
         "24x7 Emergency • Gastroenterology • Dialysis & Renal Unit", "https://images.unsplash.com/photo-1512678080530-7760d81faba6?w=600"),

        # Mumbai
        ("CareSync Western Multi-Specialty Hospital", "Mumbai", "Andheri", "S.V. Road, Andheri West, Mumbai, Maharashtra 400058", "+91 22 2628 3000", 800.0,
         "24x7 Emergency • Critical Care • Pulmonology & GI Center • Dermatology", "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=600"),
        ("CareSync Central Healthcare Pavilion", "Mumbai", "Bandra", "Hill Road, Bandra West, Mumbai, Maharashtra 400050", "+91 22 2640 4000", 850.0,
         "24x7 Emergency • Executive Preventive Health • Aesthetic Surgery • Dermatology", "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600"),
        ("CareSync Lakeside Medical Institute", "Mumbai", "Powai", "Central Avenue, Hiranandani Gardens, Powai, Mumbai 400076", "+91 22 2570 6000", 750.0,
         "24x7 Emergency • Cardiology & Cardiac Rehab • Comprehensive Oncology", "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=600"),
        ("CareSync Suburban Health Hospital", "Mumbai", "Borivali", "Link Road, Borivali West, Mumbai, Maharashtra 400092", "+91 22 2890 5000", 650.0,
         "24x7 Emergency • Pediatrics & Neonatology • Joint Replacement Unit", "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=600"),

        # Bengaluru
        ("CareSync Heritage Health Institute", "Bengaluru", "Koramangala", "88 80 Feet Road, 4th Block, Koramangala, Bengaluru, Karnataka 560034", "+91 80 2553 4000", 750.0,
         "24x7 Emergency • Advanced Robotic Surgery • Organ Transplant • Cardiology", "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=600"),
        ("CareSync Metro Care Hospital", "Bengaluru", "Indiranagar", "100 Feet Road, HAL 2nd Stage, Indiranagar, Bengaluru, Karnataka 560038", "+91 80 4115 5000", 700.0,
         "24x7 Emergency • Orthopedic & Sports Medicine • Daycare Surgery", "https://images.unsplash.com/photo-1587351021759-3e566b6af7cc?w=600"),
        ("CareSync Silicon City Hospital", "Bengaluru", "Whitefield", "ITPL Main Road, Whitefield, Bengaluru, Karnataka 560066", "+91 80 4960 7000", 700.0,
         "24x7 Emergency • Comprehensive Cancer Center • Neurovascular Sciences", "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=600"),
        ("CareSync Greenview Medical Pavilion", "Bengaluru", "HSR Layout", "27th Main, Sector 1, HSR Layout, Bengaluru, Karnataka 560102", "+91 80 2572 8000", 650.0,
         "24x7 Emergency • Women Health • Pediatric Critical Care • Endocrinology", "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=600"),

        # Hyderabad
        ("CareSync Continental Medical Centre", "Hyderabad", "Banjara Hills", "Road No. 2, Banjara Hills, Hyderabad, Telangana 500034", "+91 40 2355 6000", 700.0,
         "24x7 Emergency • Oncology & Interventional Cardiology • Organ Care", "https://images.unsplash.com/photo-1512678080530-7760d81faba6?w=600"),
        ("CareSync Global Health City", "Hyderabad", "Gachibowli", "Plot 12, Financial District, Gachibowli, Hyderabad, Telangana 500032", "+91 40 4488 7000", 650.0,
         "24x7 Emergency • Quaternary Care & Critical Care Pavilion • Pulmonology", "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=600"),
        ("CareSync Cyber Health Hospital", "Hyderabad", "Madhapur", "Hitech City Road, Madhapur, Hyderabad, Telangana 500081", "+91 40 4560 9000", 650.0,
         "24x7 Emergency • Interventional Cardiology • Neurology • Orthopedics", "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600"),
        ("CareSync Prana Healthcare Hospital", "Hyderabad", "Kukatpally", "KPHB Colony Phase 3, Kukatpally, Hyderabad, Telangana 500072", "+91 40 2305 4000", 550.0,
         "24x7 Emergency • Multi-Specialty OPD • Dialysis • Nephrology", "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=600"),

        # Vijayawada
        ("CareSync Amaravati Hospital", "Vijayawada", "Benz Circle", "MG Road, Benz Circle, Vijayawada, Andhra Pradesh 520010", "+91 866 243 7000", 500.0,
         "24x7 Emergency • Nephrology & General Surgery Center • Trauma Care", "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=600"),
        ("CareSync Krishna Valley Hospital", "Vijayawada", "Moghalrajpuram", "Siddhartha College Road, Moghalrajpuram, Vijayawada 520010", "+91 866 247 8000", 500.0,
         "24x7 Emergency • Cardiology & Pulmonology • Pediatric Wing", "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=600"),
        ("CareSync City Care Hospital", "Vijayawada", "Governorpet", "Prakasam Road, Governorpet, Vijayawada, Andhra Pradesh 520002", "+91 866 257 6000", 450.0,
         "24x7 Emergency • General Medicine • ENT • Eye Pavilion", "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=600"),

        # Pune
        ("CareSync Deccan Health Hospital", "Pune", "Kothrud", "Paud Road, Kothrud, Pune, Maharashtra 411038", "+91 20 2544 6000", 550.0,
         "24x7 Emergency • Internal Medicine, Pediatrics & Dialysis • Orthopedics", "https://images.unsplash.com/photo-1587351021759-3e566b6af7cc?w=600"),
        ("CareSync Sunrise Multi-Specialty Hospital", "Pune", "Viman Nagar", "Symbiosis Road, Viman Nagar, Pune, Maharashtra 411014", "+91 20 6608 9000", 600.0,
         "24x7 Emergency • Cardiology • Interventional Radiology • Daycare Surgery", "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=600"),
        ("CareSync Tech City Hospital", "Pune", "Hinjawadi", "Phase 1, Hinjawadi IT Park, Pune, Maharashtra 411057", "+91 20 6790 5000", 650.0,
         "24x7 Emergency • Trauma & Neuro Care • Spine Surgery Unit", "https://images.unsplash.com/photo-1512678080530-7760d81faba6?w=600"),
        ("CareSync Baner Medical Pavilion", "Pune", "Baner", "Baner-Pashan Link Road, Baner, Pune, Maharashtra 411045", "+91 20 2729 4000", 600.0,
         "24x7 Emergency • Women & Child Institute • Gastro & Endoscopy", "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=600"),

        # Delhi
        ("CareSync Capital Care Hospital", "Delhi", "Saket", "Press Enclave Marg, Saket, New Delhi, Delhi 110017", "+91 11 2651 5000", 750.0,
         "24x7 Emergency • Level-1 Trauma • Comprehensive Super-Specialty • Cardiology", "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600"),
        ("CareSync Millennium Hospital", "Delhi", "Dwarka", "Sector 9, Dwarka, New Delhi, Delhi 110077", "+91 11 4560 3000", 700.0,
         "24x7 Emergency • Renal Sciences • Cardiac Surgery • Neuro ICU", "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=600"),
        ("CareSync North Delhi Health Institute", "Delhi", "Rohini", "Sector 14, Rohini, New Delhi, Delhi 110085", "+91 11 2755 7000", 650.0,
         "24x7 Emergency • Oncology • Orthopedics • Pediatric Critical Care", "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=600"),
        ("CareSync Ridge View Hospital", "Delhi", "Vasant Kunj", "Nelson Mandela Marg, Vasant Kunj, New Delhi 110070", "+91 11 4265 8000", 800.0,
         "24x7 Emergency • Advanced Pulmonology • Dermatology • Robotic Uro-Surgery", "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=600"),

        # Kochi
        ("CareSync Malabar Medical Institute", "Kochi", "Kakkanad", "Seaport-Airport Road, Kakkanad, Kochi, Kerala 682030", "+91 484 242 8000", 600.0,
         "24x7 Emergency • Gastroenterology, Women Health & Rehab • Pulmonology", "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=600"),
        ("CareSync Cochin Grand Hospital", "Kochi", "Edappally", "NH 66 Bypass, Edappally, Kochi, Kerala 682024", "+91 484 280 5000", 600.0,
         "24x7 Emergency • Interventional Cardiology • Neurology • Stroke Unit", "https://images.unsplash.com/photo-1587351021759-3e566b6af7cc?w=600"),
        ("CareSync Coastal Care Centre", "Kochi", "Kaloor", "Banerji Road, Kaloor, Kochi, Kerala 682017", "+91 484 234 6000", 550.0,
         "24x7 Emergency • Orthopedic Care • Sports Medicine • Dialysis Unit", "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=600"),
        ("CareSync Metro South Hospital", "Kochi", "Vyttila", "Subhash Chandra Bose Road, Vyttila, Kochi, Kerala 682019", "+91 484 230 7000", 550.0,
         "24x7 Emergency • General Medicine • ENT • Eye Clinic • Dental Center", "https://images.unsplash.com/photo-1512678080530-7760d81faba6?w=600")
    ]

    for name, city, locality, addr, phone, fee, services, img_url in hospitals_master:
        existing = query_one("SELECT id FROM hospitals WHERE name = ?", (name,))
        if not existing:
            execute_insert(
                """INSERT INTO hospitals (name, city, locality, address, contact_phone, starting_fee, services_json, opening_hours, departments_json, image_url, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, '24x7 Emergency • OPD 08:00 - 20:00', '[]', ?, ?)""",
                (name, city, locality, addr, phone, fee, json.dumps([s.strip() for s in services.split("•")]), img_url, now_iso)
            )
        else:
            execute_update(
                """UPDATE hospitals 
                   SET city = ?, locality = ?, address = ?, contact_phone = ?, starting_fee = ?,
                       services_json = ?, image_url = ?
                   WHERE id = ?""",
                (city, locality, addr, phone, fee, json.dumps([s.strip() for s in services.split("•")]), img_url, existing["id"])
            )

    print("Seeded all 32 Indian multi-specialty hospitals with exact required localities.")

    # 2. Ensure all 22 Indian Clinical Departments exist
    all_22_departments = [
        ("General Medicine", "GEN", "Primary care, chronic disease management, lifestyle clinics, and preventive health screenings.", "Floor 1 - Outpatient Pavilion", "101"),
        ("Cardiology", "CARD", "Adult cardiac diagnostics, interventional catheterization, ECG, echo, heart failure care.", "Floor 3 - Heart Center", "301"),
        ("Dermatology", "DERM", "Medical & cosmetic dermatology, trichology, allergy testing, clinical skin biopsies.", "Floor 2 - Derma Wing", "201"),
        ("Neurology", "NEUR", "Neurovascular intervention, EEG, epilepsy, stroke, migraine management.", "Floor 4 - Neuro Wing", "401"),
        ("Orthopedics", "ORTH", "Joint replacement, arthroscopy, spine care, trauma fracture, sports rehabilitation.", "Floor 2 - Ortho Center", "205"),
        ("Pediatrics", "PED", "Neonatal care, pediatric subspecialties, immunization, child developmental clinics.", "Floor 2 - Child Pavilion", "210"),
        ("Gynecology", "GYN", "Comprehensive women health, hormonal disorders, minimally invasive laparoscopy.", "Floor 3 - Women Wing", "305"),
        ("Obstetrics", "OBS", "Antenatal care, high-risk pregnancy monitoring, fetal medicine, modular labor suites.", "Floor 3 - Maternity Center", "310"),
        ("ENT", "ENT", "Ear, nose, throat diagnostics, audiology, endoscopic sinus surgery, voice clinic.", "Floor 1 - ENT Suite", "105"),
        ("Ophthalmology", "OPHTH", "Cataract, retina, glaucoma management, refractive laser, pediatric vision care.", "Floor 1 - Eye Center", "108"),
        ("Psychiatry", "PSYCH", "Clinical psychology, neuropsychiatry, mood & anxiety management, de-addiction.", "Floor 5 - Behavioral Health", "501"),
        ("Pulmonology", "PULM", "Respiratory care, asthma, COPD, sleep medicine, allergy, diagnostic bronchoscopy.", "Floor 4 - Pulmonary Wing", "405"),
        ("Gastroenterology", "GASTRO", "Hepatology, therapeutic endoscopy, colonoscopy, inflammatory bowel disease.", "Floor 4 - Digestive Center", "410"),
        ("Nephrology", "NEPH", "Renal care, hemodialysis unit, glomerulonephritis, kidney transplant follow-up.", "Floor 5 - Dialysis Pavilion", "505"),
        ("Urology", "UROL", "Laser kidney stone management, prostate care, andrology, uro-oncology.", "Floor 5 - Urology Center", "510"),
        ("Oncology", "ONC", "Medical oncology, chemotherapy infusion daycare, targeted immunotherapy.", "Floor 6 - Oncology Pavilion", "601"),
        ("Endocrinology", "ENDO", "Comprehensive diabetes management, thyroid disorders, metabolic health, obesity.", "Floor 2 - Metabolic Suite", "215"),
        ("Dentistry", "DENT", "Orthodontics, endodontics, dental implants, oral & maxillofacial surgery.", "Floor 1 - Dental Wing", "112"),
        ("Radiology", "RAD", "3.0T MRI, 128-Slice CT, 4D Ultrasound, digital radiography, interventional radiology.", "Basement 1 - Imaging Hub", "001"),
        ("General Surgery", "SURG", "Advanced laparoscopic surgery, hernia repair, gallbladder, acute trauma wound care.", "Floor 3 - Surgical Suites", "315"),
        ("Emergency Medicine", "EMERG", "24x7 Level-1 trauma resuscitation, acute cardiac emergency, stroke triage.", "Ground Floor - Gate 1", "100"),
        ("Physiotherapy", "PHYSIO", "Musculoskeletal physical therapy, post-stroke rehabilitation, ergonomics.", "Floor 2 - Rehab Center", "220")
    ]
    dept_map = {}
    for name, code, desc, floor, ext in all_22_departments:
        dep = query_one("SELECT id FROM departments WHERE code = ?", (code,))
        if not dep:
            d_id = execute_insert(
                """INSERT INTO departments (name, code, description, floor_location, contact_extension, is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?)""",
                (name, code, desc, floor, ext, now_iso)
            )
            dept_map[code] = d_id
        else:
            execute_update("UPDATE departments SET name = ?, description = ? WHERE code = ?", (name, desc, code))
            dept_map[code] = dep["id"]

    # 3. Comprehensive Indian Doctor Roster: MULTIPLE doctors for EVERY department
    # Unique, stable portrait image URLs and deterministic initials
    doctor_roster = [
        # === 1. CARDIOLOGY ===
        ("dr.rajesh.iyer@caresync.in", "Dr. Rajesh Iyer, MD, DM", "CARD", "Interventional Cardiology & Cardiac Catheterization", "NMC-TN-34011", 17, 1200.0,
         "English, Hindi, Tamil", "CareSync Apex Super-Specialty Hospital", "Chennai", "Adyar", "Suite 301", "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=150"),
        ("dr.suresh.reddy@caresync.in", "Dr. Suresh Reddy, MS, MCh", "CARD", "Cardiothoracic Surgery & Heart Failure", "NMC-TS-45122", 18, 1100.0,
         "English, Hindi, Telugu", "CareSync Continental Medical Centre", "Hyderabad", "Banjara Hills", "Suite 302", "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=150"),
        ("dr.karthik.venkat@caresync.in", "Dr. Karthik Venkat, MD, DM", "CARD", "Clinical Cardiology, Arrhythmia & Preventive Heart Care", "NMC-KA-99120", 12, 1000.0,
         "English, Hindi, Kannada, Tamil", "CareSync Heritage Health Institute", "Bengaluru", "Koramangala", "Suite 303", "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=150"),
        ("dr.arun.chatterjee@caresync.in", "Dr. Arun Chatterjee, MD, DM", "CARD", "Adult Interventional Cardiology & Angioplasty", "NMC-MH-88231", 15, 1250.0,
         "English, Hindi", "CareSync Western Multi-Specialty Hospital", "Mumbai", "Andheri", "Suite 304", "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=150"),

        # === 2. DERMATOLOGY ===
        ("dr.sneha.mukherjee@caresync.in", "Dr. Sneha Mukherjee, MD, DVD", "DERM", "Clinical Dermatology, Allergy & Trichology", "NMC-MH-77123", 11, 900.0,
         "English, Hindi", "CareSync Central Healthcare Pavilion", "Mumbai", "Bandra", "Suite 201", "https://images.unsplash.com/photo-1594824813627-2c140c83d6a1?w=150"),
        ("dr.divya.ranganathan@caresync.in", "Dr. Divya Ranganathan, MD, DNB", "DERM", "Medical Dermatology & Laser Therapeutics", "NMC-TN-88214", 9, 800.0,
         "English, Hindi, Tamil", "CareSync Mediversal Hospital", "Chennai", "Anna Nagar", "Suite 202", "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=150"),
        ("dr.swati.rao@caresync.in", "Dr. Swati Rao, MD, DVL", "DERM", "Pediatric Dermatology & Chronic Eczema Care", "NMC-TS-77199", 10, 850.0,
         "English, Hindi, Telugu", "CareSync Global Health City", "Hyderabad", "Gachibowli", "Suite 203", "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150"),

        # === 3. GENERAL MEDICINE ===
        ("dr.arvind.swami@caresync.in", "Dr. Arvind Swaminathan, MD", "GEN", "General Internal Medicine, Diabetology & Executive Checkups", "NMC-TN-44510", 15, 600.0,
         "English, Hindi, Tamil", "CareSync Mediversal Hospital", "Chennai", "Anna Nagar", "Suite 101", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"),
        ("dr.ananya.sen@caresync.in", "Dr. Ananya Sen, MD", "GEN", "Primary Adult Medicine, Hypertension & Lifestyle Clinics", "NMC-DL-50250", 12, 700.0,
         "English, Hindi", "CareSync Capital Care Hospital", "Delhi", "Saket", "Suite 102", "https://images.unsplash.com/photo-1567532939604-b6b5b0db2604?w=150"),
        ("dr.sandeep.varma@caresync.in", "Dr. Sandeep Varma, MD", "GEN", "Internal Medicine & Chronic Disease Management", "NMC-AP-44122", 13, 550.0,
         "English, Hindi, Telugu", "CareSync Amaravati Hospital", "Vijayawada", "Benz Circle", "Suite 103", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150"),

        # === 4. NEUROLOGY ===
        ("dr.mohan.das@caresync.in", "Dr. Mohan Das, MD, DM", "NEUR", "Neurovascular Interventions, Stroke & Epilepsy", "NMC-TN-99211", 16, 1200.0,
         "English, Hindi, Tamil", "CareSync Apex Super-Specialty Hospital", "Chennai", "Adyar", "Suite 401", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150"),
        ("dr.priya.sharma@caresync.in", "Dr. Priya Sharma, MD, DM", "NEUR", "Cognitive Disorders, Parkinsonism & Headache Clinic", "NMC-DL-88192", 14, 1100.0,
         "English, Hindi", "CareSync Ridge View Hospital", "Delhi", "Vasant Kunj", "Suite 402", "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150"),

        # === 5. ORTHOPEDICS ===
        ("dr.arjun.menon@caresync.in", "Dr. Arjun Menon, MS, MCh", "ORTH", "Joint Replacement, Robotic Knee & Hip Arthroplasty", "NMC-KL-77215", 15, 1000.0,
         "English, Hindi, Malayalam", "CareSync Malabar Medical Institute", "Kochi", "Kakkanad", "Suite 205", "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150"),
        ("dr.gautham.krishna@caresync.in", "Dr. Gautham Krishna, MS (Ortho)", "ORTH", "Arthroscopy, Sports Trauma & Spine Surgery", "NMC-KA-66311", 11, 950.0,
         "English, Hindi, Kannada", "CareSync Metro Care Hospital", "Bengaluru", "Indiranagar", "Suite 206", "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150"),
        ("dr.vijay.raghavan@caresync.in", "Dr. Vijay Raghavan, MS (Ortho)", "ORTH", "Complex Fracture Care & Pediatric Orthopedics", "NMC-TN-55410", 13, 850.0,
         "English, Hindi, Tamil", "CareSync Central Metro Hospital", "Chennai", "T Nagar", "Suite 207", "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150"),

        # === 6. PEDIATRICS ===
        ("dr.kavita.nair@caresync.in", "Dr. Kavita Nair, MD, DCH", "PED", "Neonatal Intensive Care & Pediatric Development", "NMC-KA-50240", 14, 800.0,
         "English, Hindi, Kannada, Malayalam", "CareSync Heritage Health Institute", "Bengaluru", "Koramangala", "Suite 210", "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=150"),
        ("dr.deepthi.cherukuri@caresync.in", "Dr. Deepthi Cherukuri, MD (Ped)", "PED", "Pediatric Pulmonology & Allergy Clinics", "NMC-TS-44219", 10, 750.0,
         "English, Hindi, Telugu", "CareSync Continental Medical Centre", "Hyderabad", "Banjara Hills", "Suite 211", "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150"),

        # === 7. GYNECOLOGY ===
        ("dr.deepa.chawla@caresync.in", "Dr. Deepa Chawla, MD, DGO", "GYN", "Minimally Invasive Laparoscopy & Endometriosis Care", "NMC-MH-66512", 15, 850.0,
         "English, Hindi", "CareSync Deccan Health Hospital", "Pune", "Kothrud", "Suite 305", "https://images.unsplash.com/photo-1551836022-deb4988cc6c0?w=150"),
        ("dr.lakshmi.narayan@caresync.in", "Dr. Lakshmi Narayan, MD, DGO", "GYN", "Adolescent Gynecology, Uro-Gynecology & Menopause", "NMC-TN-99301", 16, 900.0,
         "English, Hindi, Tamil", "CareSync Central Metro Hospital", "Chennai", "T Nagar", "Suite 306", "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=150"),

        # === 8. OBSTETRICS ===
        ("dr.meenakshi.sundaram@caresync.in", "Dr. Meenakshi Sundaram, MS, DGO", "OBS", "High-Risk Pregnancy & Maternal-Fetal Medicine", "NMC-TN-99310", 17, 1000.0,
         "English, Hindi, Tamil", "CareSync Apex Super-Specialty Hospital", "Chennai", "Adyar", "Suite 310", "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150"),
        ("dr.pooja.hegde@caresync.in", "Dr. Pooja Hegde, MD, DGO", "OBS", "Fetal Ultrasound & Comprehensive Antenatal Monitoring", "NMC-KA-88123", 11, 850.0,
         "English, Hindi, Kannada", "CareSync Greenview Medical Pavilion", "Bengaluru", "HSR Layout", "Suite 311", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"),

        # === 9. ENT ===
        ("dr.harish.verma@caresync.in", "Dr. Harish Verma, MS (ENT)", "ENT", "Endoscopic Sinus Surgery & Otology Micro-Surgery", "NMC-DL-55201", 13, 750.0,
         "English, Hindi", "CareSync Capital Care Hospital", "Delhi", "Saket", "Suite 105", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150"),
        ("dr.venkatesh.rao@caresync.in", "Dr. Venkatesh Rao, MS (ENT)", "ENT", "Voice Disorders, Laryngology & Vertigo Clinic", "NMC-TS-66190", 12, 700.0,
         "English, Hindi, Telugu", "CareSync Cyber Health Hospital", "Hyderabad", "Madhapur", "Suite 106", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150"),

        # === 10. OPHTHALMOLOGY ===
        ("dr.sunita.kulkarni@caresync.in", "Dr. Sunita Kulkarni, MS, DO", "OPHTH", "Cataract Phacoemulsification, Glaucoma & Medical Retina", "NMC-KA-44198", 14, 800.0,
         "English, Hindi, Kannada", "CareSync Metro Care Hospital", "Bengaluru", "Indiranagar", "Suite 108", "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=150"),
        ("dr.ganesh.prasad@caresync.in", "Dr. Ganesh Prasad, MS (Ophth)", "OPHTH", "Corneal Transplant & Laser Refractive Eye Surgery", "NMC-TN-33109", 15, 850.0,
         "English, Hindi, Tamil", "CareSync Mediversal Hospital", "Chennai", "Anna Nagar", "Suite 109", "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150"),

        # === 11. PSYCHIATRY ===
        ("dr.amitav.ghosh@caresync.in", "Dr. Amitav Ghosh, MD, DPM", "PSYCH", "Neuropsychiatry, Anxiety & Clinical Psychotherapy", "NMC-MH-33871", 14, 1200.0,
         "English, Hindi", "CareSync Western Multi-Specialty Hospital", "Mumbai", "Andheri", "Suite 501", "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150"),
        ("dr.shreya.menon@caresync.in", "Dr. Shreya Menon, MD (Psych)", "PSYCH", "Behavioral Medicine, Mood Disorders & De-addiction", "NMC-KL-55102", 10, 950.0,
         "English, Hindi, Malayalam", "CareSync Cochin Grand Hospital", "Kochi", "Edappally", "Suite 502", "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150"),

        # === 12. PULMONOLOGY ===
        ("dr.vikram.malhotra@caresync.in", "Dr. Vikram Malhotra, MD, DM", "PULM", "Pulmonology, Asthma, Sleep Medicine & Bronchoscopy", "NMC-TS-77812", 15, 1000.0,
         "English, Hindi, Telugu", "CareSync Global Health City", "Hyderabad", "Gachibowli", "Suite 405", "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150"),
        ("dr.radhika.shroff@caresync.in", "Dr. Radhika Shroff, MD, DNB", "PULM", "Interstitial Lung Disease & Critical Care Pulmonology", "NMC-DL-88310", 12, 950.0,
         "English, Hindi", "CareSync Ridge View Hospital", "Delhi", "Vasant Kunj", "Suite 406", "https://images.unsplash.com/photo-1551836022-deb4988cc6c0?w=150"),

        # === 13. GASTROENTEROLOGY ===
        ("dr.rohan.deshmukh@caresync.in", "Dr. Rohan Deshmukh, MD, DM", "GASTRO", "Gastroenterology, Hepatology & Therapeutic Endoscopy", "NMC-MH-88190", 13, 1100.0,
         "English, Hindi", "CareSync Western Multi-Specialty Hospital", "Mumbai", "Andheri", "Suite 410", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"),
        ("dr.murugan.chinnasamy@caresync.in", "Dr. Murugan Chinnasamy, MD, DM", "GASTRO", "Digestive Oncology, ERCP & Liver Disease Management", "NMC-TN-66201", 16, 1150.0,
         "English, Hindi, Tamil", "CareSync South Health Campus", "Chennai", "Velachery", "Suite 411", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150"),

        # === 14. NEPHROLOGY ===
        ("dr.manoj.bhat@caresync.in", "Dr. Manoj Bhat, MD, DM", "NEPH", "Nephrology, Chronic Kidney Disease & Dialysis Management", "NMC-AP-55219", 12, 850.0,
         "English, Hindi, Telugu", "CareSync Amaravati Hospital", "Vijayawada", "Benz Circle", "Suite 505", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150"),
        ("dr.pradeep.kumar@caresync.in", "Dr. Pradeep Kumar, MD, DM", "NEPH", "Renal Transplantation & Glomerular Kidney Disorders", "NMC-KA-77319", 14, 1000.0,
         "English, Hindi, Kannada", "CareSync Silicon City Hospital", "Bengaluru", "Whitefield", "Suite 506", "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150"),

        # === 15. UROLOGY ===
        ("dr.sanjay.kapoor@caresync.in", "Dr. Sanjay Kapoor, MS, MCh", "UROL", "Laser Kidney Stone Surgery, Prostate Care & Andrology", "NMC-DL-99215", 17, 1200.0,
         "English, Hindi", "CareSync Capital Care Hospital", "Delhi", "Saket", "Suite 510", "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150"),
        ("dr.balasubramanian@caresync.in", "Dr. R. Balasubramanian, MS, MCh", "UROL", "Endo-Urology & Reconstructive Urological Surgery", "NMC-TN-44109", 15, 1100.0,
         "English, Hindi, Tamil", "CareSync Coastal Care Hospital", "Chennai", "OMR", "Suite 511", "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150"),

        # === 16. ONCOLOGY ===
        ("dr.shalini.prasad@caresync.in", "Dr. Shalini Prasad, MD, DM", "ONC", "Medical Oncology, Chemotherapy & Targeted Immunotherapy", "NMC-TS-66120", 14, 1500.0,
         "English, Hindi, Telugu", "CareSync Continental Medical Centre", "Hyderabad", "Banjara Hills", "Suite 601", "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150"),
        ("dr.ashok.khanna@caresync.in", "Dr. Ashok Khanna, MS, MCh", "ONC", "Surgical Oncology, Head & Neck Tumors & Breast Surgery", "NMC-DL-77390", 18, 1400.0,
         "English, Hindi", "CareSync North Delhi Health Institute", "Delhi", "Rohini", "Suite 602", "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=150"),

        # === 17. ENDOCRINOLOGY ===
        ("dr.neha.agarwal@caresync.in", "Dr. Neha Agarwal, MD, DM", "ENDO", "Clinical Endocrinology, Thyroid & Diabetes Specialist", "NMC-KA-77312", 11, 950.0,
         "English, Hindi, Kannada", "CareSync Heritage Health Institute", "Bengaluru", "Koramangala", "Suite 215", "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=150"),
        ("dr.anand.kulkarni@caresync.in", "Dr. Anand Kulkarni, MD, DM", "ENDO", "Metabolic Health, Obesity & Pituitary Disorders", "NMC-MH-88102", 13, 900.0,
         "English, Hindi", "CareSync Baner Medical Pavilion", "Pune", "Baner", "Suite 216", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150"),

        # === 18. DENTISTRY ===
        ("dr.rakesh.nambiar@caresync.in", "Dr. Rakesh Nambiar, MDS", "DENT", "Orthodontics, Dental Implants & Smile Design", "NMC-KL-44120", 10, 600.0,
         "English, Hindi, Malayalam", "CareSync Malabar Medical Institute", "Kochi", "Kakkanad", "Suite 112", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150"),
        ("dr.saranya.muralidharan@caresync.in", "Dr. Saranya Muralidharan, MDS", "DENT", "Conservative Dentistry, Endodontics & Maxillofacial", "NMC-TN-88209", 8, 550.0,
         "English, Hindi, Tamil", "CareSync Mediversal Hospital", "Chennai", "Anna Nagar", "Suite 113", "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150"),

        # === 19. RADIOLOGY ===
        ("dr.anita.joshi@caresync.in", "Dr. Anita Joshi, MD, DNB", "RAD", "Diagnostic Neuro-Imaging, 3T MRI & Cross-Sectional Radiology", "NMC-MH-55198", 13, 800.0,
         "English, Hindi", "CareSync Deccan Health Hospital", "Pune", "Kothrud", "Suite 001", "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150"),
        ("dr.venkat.raman@caresync.in", "Dr. Venkat Ramanan, MD, DMRD", "RAD", "Interventional Radiology, Vascular Doppler & 4D Ultrasound", "NMC-TN-66290", 15, 850.0,
         "English, Hindi, Tamil", "CareSync Apex Super-Specialty Hospital", "Chennai", "Adyar", "Suite 002", "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150"),

        # === 20. GENERAL SURGERY ===
        ("dr.balaji.venkat@caresync.in", "Dr. Balaji Venkataraman, MS, FACS", "SURG", "Advanced Laparoscopic, Hernia & Abdominal Surgery", "NMC-TN-88301", 17, 1100.0,
         "English, Hindi, Tamil", "CareSync Apex Super-Specialty Hospital", "Chennai", "Adyar", "Suite 315", "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150"),
        ("dr.nirmal.sharma@caresync.in", "Dr. Nirmal Sharma, MS, DNB", "SURG", "Minimally Invasive Daycare Surgery & Acute Trauma", "NMC-DL-55218", 14, 1000.0,
         "English, Hindi", "CareSync Capital Care Hospital", "Delhi", "Saket", "Suite 316", "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150"),

        # === 21. EMERGENCY MEDICINE ===
        ("dr.ritu.menon@caresync.in", "Dr. Ritu Menon, MD, MEM", "EMERG", "Emergency Medicine, Acute Trauma & Cardiac Resuscitation", "NMC-KL-77210", 11, 700.0,
         "English, Hindi, Malayalam, Tamil", "CareSync Malabar Medical Institute", "Kochi", "Kakkanad", "Suite 100", "https://images.unsplash.com/photo-1551836022-deb4988cc6c0?w=150"),
        ("dr.praveen.kumar@caresync.in", "Dr. Praveen Kumar, MD (Emergency)", "EMERG", "Critical Emergency Triage, Toxicology & Resuscitation", "NMC-TS-66311", 12, 750.0,
         "English, Hindi, Telugu", "CareSync Continental Medical Centre", "Hyderabad", "Banjara Hills", "Suite 100B", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150"),

        # === 22. PHYSIOTHERAPY ===
        ("dr.preeti.balaji@caresync.in", "Dr. Preeti Balaji, BPT, MPT", "PHYSIO", "Orthopedic Physical Therapy, Post-Surgical Rehab & Ergonomics", "NMC-TN-33190", 9, 500.0,
         "English, Hindi, Tamil", "CareSync Apex Super-Specialty Hospital", "Chennai", "Adyar", "Suite 220", "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150"),
        ("dr.rohit.chavan@caresync.in", "Dr. Rohit Chavan, MPT (Neuro)", "PHYSIO", "Neuro-Rehabilitation, Post-Stroke Mobility & Sports Therapy", "NMC-MH-44120", 10, 550.0,
         "English, Hindi", "CareSync Sunrise Multi-Specialty Hospital", "Pune", "Viman Nagar", "Suite 221", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150")
    ]

    default_pw = hash_password("DoctorPass@2026")
    for idx, (email, full_name, dept_code, spec, lic, exp, fee, lang, hosp_name, city, locality, room, avatar) in enumerate(doctor_roster, 1):
        unique_avatar = f"{avatar}&doctor_id={idx}"
        hosp = query_one("SELECT id FROM hospitals WHERE name = ?", (hosp_name,))
        hosp_id = hosp["id"] if hosp else 1

        existing_user = query_one("SELECT id FROM users WHERE email = ?", (email,))
        if not existing_user:
            u_id = execute_insert(
                """INSERT INTO users (email, password_hash, role, full_name, phone, avatar_url, city, preferred_language, is_active, created_at)
                   VALUES (?, ?, 'doctor', ?, '+91 98401 ' || ?, ?, ?, 'English', 1, ?)""",
                (email, default_pw, full_name, str(10000 + (exp * 347) % 89999), unique_avatar, city, now_iso)
            )
            d_id = execute_insert(
                """INSERT INTO doctors (user_id, department_id, specialization, license_number, experience_years,
                                      consultation_fee, languages, bio, branch, hospital_name, hospital_id, city, locality,
                                      is_available, consultation_modes, room_number, max_daily_patients)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'Board-certified clinical specialist with extensive experience in evidence-based medicine.',
                           ?, ?, ?, ?, ?, 1, 'In-Person,Video', ?, 24)""",
                (u_id, dept_map.get(dept_code, 1), spec, lic, exp, fee, lang, f"{hosp_name}, {city}", hosp_name, hosp_id, city, locality, room)
            )
            # Add Monday-Saturday availability (09:00 to 17:00, 30m slots)
            for day in range(6):
                execute_insert(
                    """INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time, slot_duration_minutes, break_start, break_end, emergency_slots_enabled, is_active)
                       VALUES (?, ?, '09:00', '17:00', 30, '13:00', '14:00', 1, 1)""",
                    (d_id, day)
                )
        else:
            u_id = existing_user["id"]
            execute_update(
                """UPDATE users 
                   SET full_name = ?, city = ?, avatar_url = ?
                   WHERE id = ?""",
                (full_name, city, unique_avatar, u_id)
            )
            execute_update(
                """UPDATE doctors
                   SET specialization = ?, consultation_fee = ?, languages = ?, branch = ?, hospital_name = ?,
                       hospital_id = ?, city = ?, locality = ?, is_available = 1, room_number = ?
                   WHERE user_id = ?""",
                (spec, fee, lang, f"{hosp_name}, {city}", hosp_name, hosp_id, city, locality, room, u_id)
            )
            doc_rec = query_one("SELECT id FROM doctors WHERE user_id = ?", (u_id,))
            if doc_rec:
                avail_count = query_one("SELECT count(*) as cnt FROM doctor_availability WHERE doctor_id = ?", (doc_rec["id"],))
                if not avail_count or avail_count["cnt"] == 0:
                    for day in range(6):
                        execute_insert(
                            """INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time, slot_duration_minutes, break_start, break_end, emergency_slots_enabled, is_active)
                               VALUES (?, ?, '09:00', '17:00', 30, '13:00', '14:00', 1, 1)""",
                            (doc_rec["id"], day)
                        )

    # 4. Update hospitals departments_json based on doctors practicing there
    hospitals = query_all("SELECT id FROM hospitals")
    for h in hospitals:
        dept_names = query_all(
            """SELECT DISTINCT dep.name FROM doctors d
               JOIN departments dep ON d.department_id = dep.id
               WHERE d.hospital_id = ?""",
            (h["id"],)
        )
        if dept_names:
            d_list = [d["name"] for d in dept_names]
        else:
            d_list = ["General Medicine", "Emergency Medicine", "Cardiology", "Dermatology", "Pediatrics"]
        execute_update("UPDATE hospitals SET departments_json = ? WHERE id = ?", (json.dumps(d_list), h["id"]))

    # 5. Ensure default patient profile is strictly Arjun Sharma, Male, with no photo image
    execute_update(
        """UPDATE users 
           SET full_name = 'Arjun Sharma', avatar_url = NULL, phone = '+91 98401 23456', city = 'Chennai'
           WHERE email = 'patient.jane@aegiscare.health'"""
    )
    execute_update(
        """UPDATE patients
           SET mrn = 'CA-MRN-48912', gender = 'Male', date_of_birth = '1992-05-14',
               blood_group = 'O+', emergency_contact = 'Rajesh Sharma (Brother) - +91 98401 55210',
               address = 'Plot 42, 4th Cross Road, Adyar, Chennai, Tamil Nadu 600020',
               allergies = 'Penicillin, Dust Mites', chronic_conditions = 'Mild Seasonal Bronchitis',
               city = 'Chennai', preferred_language = 'English'
           WHERE user_id IN (SELECT id FROM users WHERE email = 'patient.jane@aegiscare.health')"""
    )

    print(f"All 22 Indian clinical departments, {len(hospitals_master)} hospitals, and {len(doctor_roster)} Indian doctors successfully initialized.")

