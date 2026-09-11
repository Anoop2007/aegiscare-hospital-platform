import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "backend", "data", "aegiscare.db")

def upgrade():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Add columns to hospitals if not present
    cols = [r[1] for r in cursor.execute("PRAGMA table_info(hospitals)").fetchall()]
    if "latitude" not in cols:
        cursor.execute("ALTER TABLE hospitals ADD COLUMN latitude REAL DEFAULT 13.0067")
    if "longitude" not in cols:
        cursor.execute("ALTER TABLE hospitals ADD COLUMN longitude REAL DEFAULT 80.2573")
    if "image_url" not in cols:
        cursor.execute("ALTER TABLE hospitals ADD COLUMN image_url TEXT")

    # Add columns to doctors if not present
    doc_cols = [r[1] for r in cursor.execute("PRAGMA table_info(doctors)").fetchall()]
    if "shift_timing" not in doc_cols:
        cursor.execute("ALTER TABLE doctors ADD COLUMN shift_timing TEXT DEFAULT '09:00 AM – 01:00 PM & 02:00 PM – 05:30 PM'")

    # 2. Master Indian Premier Hospitals with exact coordinates and authentic hospital imagery
    premier_hospitals = [
        # Chennai
        {
            "id": 1,
            "name": "Apollo Hospitals, Greams Road",
            "city": "Chennai",
            "locality": "Adyar",
            "address": "21 Greams Lane, Thousand Lights / Adyar Link, Chennai, Tamil Nadu 600006",
            "contact_phone": "+91 44 2829 0200",
            "fee": 700.0,
            "services": ["24x7 Emergency & Trauma", "Interventional Cardiology", "Organ Transplant", "Advanced Robotic Surgery", "Comprehensive Oncology"],
            "lat": 13.0604,
            "lon": 80.2505,
            "image": "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 2,
            "name": "Fortis Malar Hospital",
            "city": "Chennai",
            "locality": "Adyar",
            "address": "52 1st Main Road, Gandhi Nagar, Adyar, Chennai, Tamil Nadu 600020",
            "contact_phone": "+91 44 4289 2222",
            "fee": 650.0,
            "services": ["24x7 Emergency", "Cardiology & Cardiac Surgery", "Neurology & Neuro Surgery", "Nephrology & Renal Transplant"],
            "lat": 13.0067,
            "lon": 80.2573,
            "image": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 3,
            "name": "Apollo Speciality Hospital, OMR",
            "city": "Chennai",
            "locality": "OMR",
            "address": "05/639 Old Mahabalipuram Road, Perungudi / OMR, Chennai, Tamil Nadu 600096",
            "contact_phone": "+91 44 3322 1111",
            "fee": 650.0,
            "services": ["24x7 Level-1 Trauma", "Critical Care Pavilion", "Orthopedics & Spine", "Pediatric Super-Specialty"],
            "lat": 12.9344,
            "lon": 80.2312,
            "image": "https://images.unsplash.com/photo-1587351021759-3e566b6af7cc?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 4,
            "name": "MIOT International Hospital",
            "city": "Chennai",
            "locality": "Anna Nagar",
            "address": "4/112 Mount Poonamallee Road, Manapakkam, Chennai, Tamil Nadu 600089",
            "contact_phone": "+91 44 4200 2288",
            "fee": 600.0,
            "services": ["24x7 Emergency", "Joint Replacement", "Gastroenterology", "Interventional Radiology"],
            "lat": 13.0232,
            "lon": 80.1764,
            "image": "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 5,
            "name": "Vijaya Super Speciality Hospital",
            "city": "Chennai",
            "locality": "T Nagar",
            "address": "434 N.S.K. Salai, Vadapalani / T Nagar Metro, Chennai, Tamil Nadu 600026",
            "contact_phone": "+91 44 6664 6664",
            "fee": 550.0,
            "services": ["24x7 Emergency", "Eye & ENT Pavilion", "Women Health & Maternity", "Diabetology"],
            "lat": 13.0524,
            "lon": 80.2120,
            "image": "https://images.unsplash.com/photo-1512678080530-7760d81faba6?w=800&auto=format&fit=crop&q=80"
        },
        # Delhi NCR
        {
            "id": 6,
            "name": "AIIMS (All India Institute of Medical Sciences)",
            "city": "Delhi",
            "locality": "Saket",
            "address": "Sri Aurobindo Marg, Ansari Nagar, New Delhi, Delhi 110029",
            "contact_phone": "+91 11 2658 8500",
            "fee": 500.0,
            "services": ["24x7 Apex Emergency & Trauma", "Quaternary Care", "Cardiothoracic Surgery", "Comprehensive Oncology & Radiation"],
            "lat": 28.5672,
            "lon": 77.2100,
            "image": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 7,
            "name": "Fortis Memorial Research Institute (FMRI)",
            "city": "Delhi",
            "locality": "Saket",
            "address": "Sector 44, Opposite HUDA City Centre, Gurugram, Delhi NCR 122002",
            "contact_phone": "+91 124 496 2200",
            "fee": 900.0,
            "services": ["24x7 Emergency", "Neurosciences", "Hematology & BMT", "Robotic Minimal Access Surgery"],
            "lat": 28.4595,
            "lon": 77.0725,
            "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 8,
            "name": "Medanta - The Medicity",
            "city": "Delhi",
            "locality": "Dwarka",
            "address": "CH Bakhtawar Singh Road, Sector 38, Gurugram / Delhi NCR 122001",
            "contact_phone": "+91 124 414 1414",
            "fee": 850.0,
            "services": ["24x7 Emergency", "Heart Institute", "Kidney & Urology Institute", "Liver Transplant & Regenerative Care"],
            "lat": 28.4395,
            "lon": 77.0427,
            "image": "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 9,
            "name": "Max Super Speciality Hospital",
            "city": "Delhi",
            "locality": "Saket",
            "address": "1 2 Press Enclave Marg, Saket District Centre, New Delhi 110017",
            "contact_phone": "+91 11 2651 5050",
            "fee": 800.0,
            "services": ["24x7 Emergency", "Cardiac Sciences", "Aesthetic & Reconstructive Surgery", "Pulmonology & Sleep Labs"],
            "lat": 28.5284,
            "lon": 77.2132,
            "image": "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=800&auto=format&fit=crop&q=80"
        },
        # Bengaluru
        {
            "id": 10,
            "name": "Manipal Hospital, Old Airport Road",
            "city": "Bengaluru",
            "locality": "Koramangala",
            "address": "98 HAL Old Airport Road, Kodihalli, Bengaluru, Karnataka 560017",
            "contact_phone": "+91 80 2502 4444",
            "fee": 750.0,
            "services": ["24x7 Emergency", "Cardiology & Vascular", "Organ Transplant", "Comprehensive Cancer Care"],
            "lat": 12.9592,
            "lon": 77.6534,
            "image": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 11,
            "name": "Manipal Hospital, Whitefield",
            "city": "Bengaluru",
            "locality": "Whitefield",
            "address": "ITPL Main Road, KIADB Export Promotion Industrial Area, Whitefield, Bengaluru 560066",
            "contact_phone": "+91 80 4960 7777",
            "fee": 700.0,
            "services": ["24x7 Emergency", "Orthopedics & Joint Replacement", "Women & Child Care", "Neuro ICU"],
            "lat": 12.9863,
            "lon": 77.7344,
            "image": "https://images.unsplash.com/photo-1587351021759-3e566b6af7cc?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 12,
            "name": "Fortis Hospital, Bannerghatta Road",
            "city": "Bengaluru",
            "locality": "Indiranagar",
            "address": "154/9 Bannerghatta Road, Opposite IIM-B, Bengaluru, Karnataka 560076",
            "contact_phone": "+91 80 6621 4444",
            "fee": 750.0,
            "services": ["24x7 Emergency", "Interventional Cardiology", "Nephrology & Urology", "Gastro Sciences"],
            "lat": 12.8943,
            "lon": 77.5982,
            "image": "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=800&auto=format&fit=crop&q=80"
        },
        # Mumbai
        {
            "id": 13,
            "name": "Kokilaben Dhirubhai Ambani Hospital",
            "city": "Mumbai",
            "locality": "Andheri",
            "address": "Rao Saheb Achutrao Patwardhan Marg, Four Bungalows, Andheri West, Mumbai 400053",
            "contact_phone": "+91 22 4269 6969",
            "fee": 850.0,
            "services": ["24x7 Emergency", "Full Time Specialist System", "Children's Heart Centre", "Centre for Bone & Joint"],
            "lat": 19.1311,
            "lon": 72.8252,
            "image": "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 14,
            "name": "Lilavati Hospital & Research Centre",
            "city": "Mumbai",
            "locality": "Bandra",
            "address": "A-791 Bandra Reclamation, Bandra West, Mumbai, Maharashtra 400050",
            "contact_phone": "+91 22 2675 1000",
            "fee": 900.0,
            "services": ["24x7 Emergency", "Executive Health Checkup", "Interventional Cardiology", "Neurosurgery"],
            "lat": 19.0514,
            "lon": 72.8295,
            "image": "https://images.unsplash.com/photo-1512678080530-7760d81faba6?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 15,
            "name": "Tata Memorial Hospital",
            "city": "Mumbai",
            "locality": "Powai",
            "address": "Dr. E Borges Road, Parel, Mumbai, Maharashtra 400012",
            "contact_phone": "+91 22 2417 7000",
            "fee": 600.0,
            "services": ["24x7 Emergency", "Apex Oncology Centre", "Nuclear Medicine", "Preventive Oncology & Research"],
            "lat": 19.0048,
            "lon": 72.8431,
            "image": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=800&auto=format&fit=crop&q=80"
        },
        # Hyderabad
        {
            "id": 16,
            "name": "Yashoda Hospitals, Somajiguda",
            "city": "Hyderabad",
            "locality": "Banjara Hills",
            "address": "Raj Bhavan Road, Somajiguda / Banjara Hills, Hyderabad, Telangana 500082",
            "contact_phone": "+91 40 4567 4567",
            "fee": 700.0,
            "services": ["24x7 Emergency", "Interventional Pulmonology", "Medical & Surgical Oncology", "Heart & Lung Transplant"],
            "lat": 17.4243,
            "lon": 78.4593,
            "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 17,
            "name": "KIMS Hospitals (Krishna Institute)",
            "city": "Hyderabad",
            "locality": "Gachibowli",
            "address": "1-8-31/1 Minister Road, Secunderabad & Gachibowli Wing, Hyderabad 500003",
            "contact_phone": "+91 40 4488 5000",
            "fee": 650.0,
            "services": ["24x7 Emergency", "Robotic Uro-Oncology", "Heart Failure Clinic", "Comprehensive Neurosciences"],
            "lat": 17.4375,
            "lon": 78.4983,
            "image": "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 18,
            "name": "AIG Hospitals (Asian Institute of Gastroenterology)",
            "city": "Hyderabad",
            "locality": "Madhapur",
            "address": "1-66/AIG/2/3 Mindspace Road, Gachibowli / Madhapur, Hyderabad 500032",
            "contact_phone": "+91 40 4244 4222",
            "fee": 700.0,
            "services": ["24x7 Emergency", "Digestive Diseases Institute", "Advanced Endoscopy", "Hepatology & Liver Transplant"],
            "lat": 17.4435,
            "lon": 78.3654,
            "image": "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=800&auto=format&fit=crop&q=80"
        },
        # Vijayawada
        {
            "id": 19,
            "name": "Manipal Hospital, Vijayawada",
            "city": "Vijayawada",
            "locality": "Benz Circle",
            "address": "Kanakadurga Varadhi, Near Toll Gate, Tadepalle, Vijayawada 522501",
            "contact_phone": "+91 8645 280 000",
            "fee": 500.0,
            "services": ["24x7 Emergency & Trauma", "Multi-Specialty OPD", "Dialysis Unit", "Pediatric Surgery"],
            "lat": 16.4912,
            "lon": 80.6087,
            "image": "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 20,
            "name": "Apollo Speciality Hospital, Vijayawada",
            "city": "Vijayawada",
            "locality": "Benz Circle",
            "address": "MG Road, Municipal Employees Colony, Benz Circle, Vijayawada 520010",
            "contact_phone": "+91 866 246 6666",
            "fee": 550.0,
            "services": ["24x7 Emergency", "Cardiology & CTVS", "Nephrology", "Critical Care & ICU"],
            "lat": 16.4971,
            "lon": 80.6558,
            "image": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=800&auto=format&fit=crop&q=80"
        },
        # Pune
        {
            "id": 21,
            "name": "Ruby Hall Clinic, Sassoon Road",
            "city": "Pune",
            "locality": "Kothrud",
            "address": "40 Sassoon Road, Sangamvadi / Kothrud Link, Pune, Maharashtra 411001",
            "contact_phone": "+91 20 6645 5100",
            "fee": 600.0,
            "services": ["24x7 Emergency", "Cardiology & Cardiac Surgery", "Oncology & BMT", "Organ Transplant Unit"],
            "lat": 18.5323,
            "lon": 73.8767,
            "image": "https://images.unsplash.com/photo-1587351021759-3e566b6af7cc?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 22,
            "name": "Jehangir Hospital, Pune",
            "city": "Pune",
            "locality": "Baner",
            "address": "32 Sassoon Road, Opposite Pune Railway Station, Pune 411001",
            "contact_phone": "+91 20 6681 1000",
            "fee": 600.0,
            "services": ["24x7 Emergency", "Orthopedics & Spine", "Pediatrics & NICU", "Gastroenterology"],
            "lat": 18.5284,
            "lon": 73.8741,
            "image": "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=800&auto=format&fit=crop&q=80"
        },
        # Kochi
        {
            "id": 23,
            "name": "Aster Medcity, Kochi",
            "city": "Kochi",
            "locality": "Kakkanad",
            "address": "Kuttisahib Road, Near Kothad Bridge, Cheranalloor, Kochi, Kerala 682027",
            "contact_phone": "+91 484 669 9999",
            "fee": 650.0,
            "services": ["24x7 Level-1 Emergency", "Cardiology & Vascular", "Neurosciences Institute", "Robotic Surgery & Oncology"],
            "lat": 10.0543,
            "lon": 76.2755,
            "image": "https://images.unsplash.com/photo-1512678080530-7760d81faba6?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": 24,
            "name": "Amrita Hospital (AIMS), Kochi",
            "city": "Kochi",
            "locality": "Edappally",
            "address": "AIMS Ponekkara P.O., Edappally, Kochi, Kerala 682041",
            "contact_phone": "+91 484 285 1234",
            "fee": 550.0,
            "services": ["24x7 Emergency", "Pediatric Heart Surgery", "Head & Neck Oncology", "Solid Organ Transplant"],
            "lat": 10.0326,
            "lon": 76.2917,
            "image": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=800&auto=format&fit=crop&q=80"
        }
    ]

    for h in premier_hospitals:
        cursor.execute(
            """INSERT INTO hospitals (id, name, city, locality, address, contact_phone, starting_fee, services_json, opening_hours, departments_json, latitude, longitude, image_url, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, '24x7 Emergency • OPD 08:00 - 20:00', '[]', ?, ?, ?, datetime('now'))
               ON CONFLICT(id) DO UPDATE SET
                   name = excluded.name,
                   city = excluded.city,
                   locality = excluded.locality,
                   address = excluded.address,
                   contact_phone = excluded.contact_phone,
                   starting_fee = excluded.starting_fee,
                   services_json = excluded.services_json,
                   latitude = excluded.latitude,
                   longitude = excluded.longitude,
                   image_url = excluded.image_url""",
            (
                h["id"], h["name"], h["city"], h["locality"], h["address"], h["contact_phone"],
                h["fee"], json.dumps(h["services"]), h["lat"], h["lon"], h["image"]
            )
        )

    # 3. Update doctors with real premier hospital names and shift timings
    hosp_rows = cursor.execute("SELECT id, name, city, locality FROM hospitals").fetchall()
    hosp_lookup = {r[0]: r for r in hosp_rows}

    # Shift timing templates
    shift_patterns = [
        "09:00 AM – 01:00 PM & 02:00 PM – 05:30 PM",
        "10:00 AM – 02:00 PM & 04:00 PM – 08:30 PM",
        "08:30 AM – 01:00 PM & 02:30 PM – 06:00 PM"
    ]

    docs = cursor.execute("SELECT id, department_id, specialization FROM doctors").fetchall()
    for doc_id, dept_id, spec in docs:
        h_id = ((doc_id - 1) % len(premier_hospitals)) + 1
        h_data = hosp_lookup.get(h_id, premier_hospitals[0])
        h_name = h_data[1] if isinstance(h_data, tuple) else h_data["name"]
        h_city = h_data[2] if isinstance(h_data, tuple) else h_data["city"]
        h_loc = h_data[3] if isinstance(h_data, tuple) else h_data["locality"]
        
        is_emerg = "Emergency" in spec or "Trauma" in spec or dept_id == 21
        shift = "24x7 Emergency On-Duty" if is_emerg else shift_patterns[doc_id % len(shift_patterns)]

        cursor.execute(
            """UPDATE doctors 
               SET hospital_id = ?, hospital_name = ?, city = ?, locality = ?, branch = ?, shift_timing = ?
               WHERE id = ?""",
            (h_id, h_name, h_city, h_loc, f"{h_name}, {h_city}", shift, doc_id)
        )

    # 4. Strictly Male default patient: Arjun Sharma (NO image, pure male vitals)
    # Check if patient.jane or patient.arjun exists in users
    p_user = cursor.execute("SELECT id FROM users WHERE role = 'patient' ORDER BY id ASC LIMIT 1").fetchone()
    if p_user:
        u_id = p_user[0]
        cursor.execute(
            """UPDATE users 
               SET full_name = 'Arjun Sharma',
                   email = 'patient.arjun@careaura.in',
                   phone = '+91 98401 23456',
                   avatar_url = NULL,
                   city = 'Chennai',
                   is_active = 1
               WHERE id = ?""",
            (u_id,)
        )
        cursor.execute(
            """UPDATE patients
               SET mrn = 'CA-MRN-48912',
                   date_of_birth = '1992-05-14',
                   gender = 'Male',
                   blood_group = 'O+',
                   emergency_contact = 'Rajesh Sharma (Brother) - +91 98401 55210',
                   address = 'Plot 42, 4th Cross Road, Adyar, Chennai, Tamil Nadu 600020',
                   allergies = 'Penicillin, Dust Mites',
                   chronic_conditions = 'Mild Seasonal Bronchitis',
                   city = 'Chennai',
                   preferred_language = 'English, Hindi, Tamil'
               WHERE user_id = ?""",
            (u_id,)
        )

    # Clean up any Jane Doe occurrences in consultation notes, health reports, prescriptions
    try:
        cursor.execute("UPDATE health_reports SET file_content_or_preview = REPLACE(file_content_or_preview, 'Jane Doe', 'Arjun Sharma') WHERE file_content_or_preview LIKE '%Jane Doe%'")
        cursor.execute("UPDATE health_reports SET summary = REPLACE(summary, 'Jane Doe', 'Arjun Sharma') WHERE summary LIKE '%Jane Doe%'")
        cursor.execute("UPDATE health_reports SET file_content_or_preview = REPLACE(file_content_or_preview, 'Female, 32', 'Male, 34') WHERE file_content_or_preview LIKE '%Female, 32%'")
    except Exception as e:
        print("Note on health reports cleanup:", e)

    conn.commit()
    conn.close()
    print("CareAura database upgrade successfully applied!")

if __name__ == "__main__":
    upgrade()
