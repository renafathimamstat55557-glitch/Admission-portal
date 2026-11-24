import streamlit as st
import requests
import sqlite3
import json
import re
import base64
from pathlib import Path
from datetime import date
from PIL import Image, ImageDraw
from io import BytesIO
# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="BCM College | Registration Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# FILE PATHS
# ==========================================

BASE_DIR = Path(__file__).parent

LOGO_FILE = BASE_DIR / "bcm_logo.jpeg.jpeg"
DB_FILE = BASE_DIR / "bcm_registrations.db"

# ==========================================
# COURSE LISTS
# ==========================================

UG_COURSES = [
    "B.A. (Hons) English Language & Literature",
    "B.A. (Hons) Economics",
    "B.A. (Hons) Sociology",
    "B.A. (Hons) History",
    "B.Sc. (Hons) Statistics",
    "B.Sc. (Hons) Mathematics",
    "B.Sc. (Hons) Computer Science",
    "B.Sc. (Hons) Home Science",
    "B.Sc. (Hons) Food Science & Quality Control",
    "B.Sc. (Hons) Zoology",
    "B.Sc. (Hons) Physics",
    "B.Sc. (Hons) Chemistry",
    "B.Sc. (Hons) Botany",
    "B.Sc. (Hons) Applied Psychology",
    "B.Com. (Hons) ACCA",
    "B.Com. (Hons) CA",
    "B.Com. (Hons) Finance and Taxation"
]

PG_COURSES = [
    "M.A. English",
    "M.Sc. Mathematics",
    "M.Sc. Statistics with Data Science",
    "M.Sc. Home Science (Child Development)",
    "M.Com. Finance and Taxation / Business Analytics",
    "Master of Social Work"
]

BOARDS = [
    "Kerala State Board (SSLC)",
    "CBSE",
    "CISCE (ICSE)",
    "Tamil Nadu State Board (SSLC)",
    "Others"
]

PERCENTAGES = [
    "Above 90%",
    "80–90%",
    "70–80%",
    "60–70%",
    "50–60%",
    "40–50%",
    "Below 40%"
]

STREAMS = [
    "Science",
    "Commerce",
    "Humanities / Arts",
    "Vocational / VHSE",
    "Technical",
    "Other"
]




# ==========================================
# DATABASE
# ==========================================

def create_database():

    with sqlite3.connect(DB_FILE) as conn:

        cur = conn.cursor()

        # Create table if it does not exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT,
                applicant_name TEXT,
                email TEXT,
                phone TEXT,
                category TEXT,
                application_data TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Read existing database columns
        cur.execute("PRAGMA table_info(applications)")

        existing_columns = {
            row[1] for row in cur.fetchall()
        }

        # Columns required by the application
        required_columns = {
            "student_name": "TEXT",
            "applicant_name": "TEXT",
            "email": "TEXT",
            "phone": "TEXT",
            "category": "TEXT",
            "application_data": "TEXT",
            "submitted_at": "TIMESTAMP"
        }

        # Add only columns that are missing
        for column, dtype in required_columns.items():

            if column not in existing_columns:

                try:
                    cur.execute(
                        f"ALTER TABLE applications ADD COLUMN {column} {dtype}"
                    )

                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        raise

        conn.commit()


create_database()



# ==========================================
# IMAGE LOADING
# ==========================================


def load_logo(path):
    if not path.exists():
        return None

    image = Image.open(path).convert("RGBA")

    # Remove white background around the logo
    corners = [
        (0, 0),
        (image.width - 1, 0),
        (0, image.height - 1),
        (image.width - 1, image.height - 1)
    ]

    for corner in corners:
        ImageDraw.floodfill(
            image,
            corner,
            (255, 255, 255, 0),
            thresh=35
        )

    return image


logo_image = load_logo(LOGO_FILE)


# ==========================================
# SESSION STATE
# ==========================================

DEFAULTS = {
    "page": "home",
    "personal": {},
    "academic": {},
    "category": "Undergraduate (UG)",

    "p_name": "",
    "p_dob": date(2005, 1, 1),
    "p_gender": "Select Gender",
    "p_phone": "",
    "p_email": "",
    "p_address": "",
    "p_guardian": "",
    "p_guardian_phone": "",

    "ug_board": BOARDS[0],
    "ug_percentage": PERCENTAGES[0],
    "ug_plus_one": 0.0,

    "pg_stream": STREAMS[0],
    "pg_percentage": PERCENTAGES[0],
    "degree_category": "Science",
    "degree_course": "Select Degree Course"
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

for prefix in ["ug", "pg"]:
    for i in range(1, 6):
        key = f"{prefix}pref{i}"
        if key not in st.session_state:
            st.session_state[key] = "Not selected"

# ==========================================
# PROFESSIONAL DESIGN
# ==========================================

st.markdown("""
<style>
#MainMenu, footer, header {
    visibility: hidden;
}

.stApp {
    background: linear-gradient(
        135deg,
        #101b35,
        #172d50,
        #101b35
    );
    color: white;
}

.block-container {
    max-width: 1250px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4, p, label {
    color: white !important;
}

.section-title {
    font-size: 25px;
    color: white;
    border-bottom: 2px solid #d3b66a;
    padding-bottom: 8px;
    margin: 20px 0;
    font-weight: bold;
}

.portal-card {
    background: #203858;
    padding: 28px;
    border-radius: 16px;
    border: 1px solid #49617f;
    box-shadow: 0 5px 20px rgba(0,0,0,0.25);
}

.main-title {
    font-size: 34px;
    font-weight: bold;
    color: white;
}

.subtitle {
    font-size: 17px;
    color: #e9c5df;
}

.hero-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 22px;
    background: linear-gradient(
        transparent,
        rgba(10,20,40,0.95)
    );
}

.stButton > button,
.stFormSubmitButton > button {
    background: #c01883 !important;
    color: white !important;
    border: none !important;
    border-radius: 9px !important;
    min-height: 43px;
    font-weight: bold;
}

.stButton > button:hover {
    background: #8f105f !important;
}

.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stDateInput input {
    background: #304967 !important;
    color: white !important;
    border: 1px solid #8296ad !important;
    border-radius: 9px !important;
}

.stSelectbox div[data-baseweb="select"] > div {
    background: #304967 !important;
    color: white !important;
    border-radius: 9px !important;
}

.stRadio label {
    color: white !important;
}

.footer-text {
    text-align: center;
    padding: 18px;
    color: white;
    border-top: 1px solid #d3b66a;
    margin-top: 35px;
}

@media(max-width:700px) {
    .main-title {
        font-size: 23px;
    }
    .hero-banner {
        height: 190px;
    }
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# PROFESSIONAL COLLEGE HEADER
# ==========================================

st.markdown("""
<style>

/* Header alignment */
div[data-testid="stHorizontalBlock"] {
    align-items: center;
}

/* College heading */
.college-title {
    font-size: 30px;
    font-weight: 800;
    color: white;
    margin: 0;
    padding-top: 0;
}

/* Subtitle */
.college-subtitle {
    color: #ffb6d9;
    font-size: 17px;
    margin-top: 8px;
}

/* Logo image */
div[data-testid="stImage"] img {
    object-fit: contain;
}

</style>
""", unsafe_allow_html=True)


col1, col2 = st.columns(
    [1.2, 7],
    vertical_alignment="center"
)

with col1:
    if logo_image is not None:
        st.image(
            logo_image,
            width=130
        )
    else:
        st.warning("Logo not found")


with col2:
    st.markdown(
        '<h2 class="college-title">'
        'B.C.M. College Kottayam (Autonomous)'
        '</h2>',
        unsafe_allow_html=True
    )

    
st.divider()



# ==========================================
# HOME PAGE
# ==========================================

if st.session_state.page == "home":

   

    st.markdown("""
    <div class="portal-card">
        <h2 style="text-align:center;">
             REGISTRATION 2027-28
        </h2>
        <p style="text-align:center;font-size:17px;">
            Welcome to the B.C.M. College Kottayam (Autonomous)
            student registration portal.
            <br>
            Register for Undergraduate and Postgraduate
            programmes
        </p>
        <hr>
        <h3 style="text-align:center;">
            Begin Your Academic Journey With Us
        </h3>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    a, b, c = st.columns([2, 3, 2])

    with b:
        if st.button(
            "STUDENT REGISTRATION  →",
            use_container_width=True
        ):
            st.session_state.page = "personal"
            st.rerun()

# ================= PERSONAL INFORMATION PAGE =================

elif st.session_state.page == "personal":

    st.title("👤 Student Registration")
    st.subheader("Personal Information")

    st.progress(1 / 3)



    with st.form("personal_form"):

        name = st.text_input(
            "Full Name *",
            value=st.session_state.get("p_name", "")
        )

        gender_options = ["Select Gender", "Male", "Female", "Others"]

        gender = st.selectbox(
            "Gender *",
            gender_options,
            index=gender_options.index(
                st.session_state.get("p_gender", "Select Gender")
            )
        )

        dob = st.date_input(
            "Date of Birth *",
            value=st.session_state.get("p_dob", date(2005, 1, 1)),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            format="DD/MM/YYYY"
        )

        address = st.text_area(
            "Address *",
            value=st.session_state.get("p_address", "")
        )

        phone = st.text_input(
            "Contact Number / WhatsApp Number *",
            value=st.session_state.get("p_phone", ""),
            placeholder="Enter 10-digit number"
        )

        email = st.text_input(
            "Email Address *",
            value=st.session_state.get("p_email", ""),
            placeholder="Enter email address"
        )

        guardian = st.text_input(
            "Guardian Name *",
            value=st.session_state.get("p_guardian", "")
        )

        guardian_phone = st.text_input(
            "Guardian Mobile Number *",
            value=st.session_state.get("p_guardian_phone", ""),
            placeholder="Enter 10-digit number"
        )

        next_button = st.form_submit_button(
            "Next →",
            use_container_width=True
        )

    # VALIDATION AFTER CLICKING NEXT
    if next_button:

        if not all([
            name.strip(),
            gender != "Select Gender",
            address.strip(),
            phone.strip(),
            email.strip(),
            guardian.strip(),
            guardian_phone.strip()
        ]):

            st.error("Please fill in all mandatory fields.")

        elif not re.fullmatch(r"[0-9]{10}", phone.strip()):

            st.error("Please enter a valid 10-digit contact number.")

        elif not re.fullmatch(r"[0-9]{10}", guardian_phone.strip()):

            st.error("Please enter a valid 10-digit guardian number.")

        elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):

            st.error("Please enter a valid email address.")

        else:

            # SAVE PERSONAL INFORMATION
            st.session_state.p_name = name
            st.session_state.p_gender = gender
            st.session_state.p_dob = dob
            st.session_state.p_address = address
            st.session_state.p_phone = phone
            st.session_state.p_email = email
            st.session_state.p_guardian = guardian
            st.session_state.p_guardian_phone = guardian_phone

            st.session_state.personal = {
                "name": name,
                "dob": dob,
                "gender": gender,
                "phone": phone,
                "email": email,
                "address": address,
                "guardian": guardian,
                "guardian_phone": guardian_phone
            }

            st.session_state.page = "academic"
            st.rerun()

    # HOME BUTTON
    if st.button("← Back to Home", use_container_width=True):

        st.session_state.page = "home"
        st.rerun()

# ==========================================
# COURSE PREFERENCE FUNCTION
# ==========================================

def show_preferences(prefix, courses):

    selected = []

    options = ["Not selected"] + courses

    for i in range(1, 6):

        key = f"{prefix}pref{i}"

        available = [
            course for course in courses
            if course not in selected
        ]

        current_options = ["Not selected"] + available

        current_value = st.session_state.get(
            key, "Not selected"
        )

        if current_value not in current_options:
            st.session_state[key] = "Not selected"

        choice = st.selectbox(
            f"Preference {i}",
            current_options,
            key=key
        )

        if choice != "Not selected":
            selected.append(choice)

    return selected

# ==========================================
# ACADEMIC INFORMATION PAGE
# ==========================================

if st.session_state.page == "academic":

    st.markdown("## Academic Information")
    st.progress(0.66)

    st.markdown(
        '<div class="section-title">Course Application Details</div>',
        unsafe_allow_html=True
    )

    category = st.radio(
        "Select Admission Category",
        ["Undergraduate (UG)", "Postgraduate (PG)"],
        horizontal=True,
        key="category"
    )

    # --------------------------------------
    # UG FORM
    # --------------------------------------

    if category == "Undergraduate (UG)":

        st.markdown("### Undergraduate Admission")

        st.selectbox(
            "10th Standard Board *",
            BOARDS,
            key="ug_board"
        )

        st.selectbox(
            "10th Standard Percentage *",
            PERCENTAGES,
            key="ug_percentage"
        )

        st.number_input(
            "Plus One Percentage *",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            key="ug_plus_one"
        )

        st.markdown("### UG Course Preferences")

        st.write("Choose up to five courses in your preferred order.")

        preferences = show_preferences("ug", UG_COURSES)

        if st.button("Next →", key="ug_next"):

            if st.session_state.ug_plus_one <= 0:
                st.error("Enter your Plus One percentage.")

            elif not preferences:
                st.error("Please select at least one course.")

            else:
                st.session_state.academic = {
                    "category": "UG",
                    "board": st.session_state.ug_board,
                    "10th_percentage": st.session_state.ug_percentage,
                    "plus_one_percentage": st.session_state.ug_plus_one,
                    "preferences": preferences
                }

                st.session_state.page = "summary"
                st.rerun()

    # --------------------------------------
    # PG FORM
    # --------------------------------------

    else:

     st.markdown("### Postgraduate Admission")

     st.selectbox(
        "12th Standard Stream *",
        STREAMS,
        key="pg_stream"
     )

     st.selectbox(
        "12th Standard Percentage *",
        PERCENTAGES,
        key="pg_percentage"
     )

     st.selectbox(
        "Current Degree Programme Category *",
        [
            "Science",
            "Arts / Humanities",
            "Commerce / Management",
            "Other"
         ],
         key="degree_category"
     )

     current_category = st.session_state.degree_category

     st.text_input(
        "What degree programme are you currently pursuing or have completed? *",
        key="degree_course",
        placeholder="Enter your degree programme"
     )

     st.markdown("### Preferred Master's Degree Courses")

     preferences = show_preferences("pg", PG_COURSES)

    if st.button("Next →", key="pg_next"):

        if not st.session_state.degree_course.strip():

            st.error("Please enter your degree programme.")

        elif not preferences:

            st.error("Please select at least one Master's course.")

        else:

            st.session_state.academic = {
                "category": "PG",
                "stream": st.session_state.pg_stream,
                "12th_percentage": st.session_state.pg_percentage,
                "degree_category": current_category,
                "degree_course": st.session_state.degree_course.strip(),
                "preferences": preferences
            }

            st.session_state.page = "summary"
            st.rerun()


# ==========================================
# APPLICATION SUMMARY PAGE
# ==========================================
    # BACK BUTTON - ACADEMIC PAGE ONLY
    st.divider()

    if st.button(
        "← Back to Personal Information",
        use_container_width=True
    ):
        st.session_state.page = "personal"
        st.rerun()
elif st.session_state.page == "summary":

    st.title("📋 Application Summary")
    st.progress(1.0)

    p = st.session_state.personal
    a = st.session_state.academic

    # --------------------------------------
    # PERSONAL INFORMATION
    # --------------------------------------

    st.subheader("Personal Information")

    personal_fields = [
        ("Full Name", "name"),
        ("Gender", "gender"),
        ("Date of Birth", "dob"),
        ("Address", "address"),
        ("Contact Number", "phone"),
        ("Email Address", "email"),
        ("Guardian Name", "guardian"),
        ("Guardian Phone Number", "guardian_phone")
    ]

    for label, key in personal_fields:
        st.write(f"**{label}:** {p.get(key, '')}")

    st.divider()

    # --------------------------------------
    # ACADEMIC INFORMATION
    # --------------------------------------

    st.subheader("Academic Information")

    st.write(f"**Admission Level:** {a.get('category', '')}")

    # UG SUMMARY
    if a.get("category") == "UG":

        st.write(f"**10th Board:** {a.get('board', '')}")

        st.write(
            f"**10th Percentage Range:** "
            f"{a.get('10th_percentage', '')}"
        )

        st.write(
            f"**Plus One Percentage:** "
            f"{a.get('plus_one_percentage', '')}%"
        )

        st.subheader("UG Course Preferences")

        for i, course in enumerate(
            a.get("preferences", []), 1
        ):
            if course:
                st.write(f"{i}. {course}")

    # PG SUMMARY
    else:

        st.write(
            f"**12th Stream:** "
            f"{a.get('stream', '')}"
        )

        st.write(
            f"**12th Percentage Range:** "
            f"{a.get('12th_percentage', '')}"
        )

        st.write(
            f"**Degree Stream:** "
            f"{a.get('degree_category', '')}"
        )

        st.write(
            f"**Degree Course:** "
            f"{a.get('degree_course', '')}"
        )

        st.subheader("PG Course Preferences")

        for i, course in enumerate(
            a.get("preferences", []), 1
        ):
            if course:
                st.write(f"{i}. {course}")

    st.divider()

    # --------------------------------------
    # EDIT BUTTONS
    # --------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "✏️ Edit Personal Information",
            use_container_width=True
        ):

            st.session_state.page = "personal"
            st.rerun()

    with col2:

        if st.button(
            "✏️ Edit Academic Information",
            use_container_width=True
        ):

            st.session_state.page = "academic"
            st.rerun()

    st.divider()

    # --------------------------------------
    # BACK AND SUBMIT BUTTONS
    # --------------------------------------

    submit = st.columns(1)
    with submit[0]:
        if st.button(
            "✅ SAVE AND SUBMIT",
            use_container_width=True
        ):

            if not p or not a:

                st.error(
                    "Please complete all application details."
                )

            else:

                # SAVE APPLICATION INTO SQLITE DATABASE
                with sqlite3.connect(DB_FILE) as conn:

                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT INTO applications (
    student_name,
    applicant_name,
    email,
    phone,
    category,
    application_data,
    submitted_at
)
VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        p["name"],
                        p["name"],
                        p["email"],
                        p["phone"],
                        a["category"],
                        json.dumps({
                            "personal": {
                                **p,
                                "dob": str(p["dob"])
                            },
                            "academic": a
                        })
                    ))

                    
                # SAVE APPLICATION TO GOOGLE SHEETS

                p = st.session_state.personal
                a = st.session_state.academic

                is_ug = a["category"] == "UG"

                payload = {
                    "name": p.get("name", ""),
                    "gender": p.get("gender", ""),
                    "dob": str(p.get("dob", "")),
                    "address": p.get("address", ""),
                    "contact": p.get("phone", ""),
                    "guardian_name": p.get("guardian", ""),
                    "guardian_phone": p.get("guardian_phone", ""),
                    "email": p.get("email", ""),
                    "category": a.get("category", ""),
                    "tenth_board": a.get("board", ""),
                    "tenth_percentage": a.get("10th_percentage", ""),
                    "plus_one_percentage": a.get("plus_one_percentage", ""),
                    "ug_preferences": a.get("preferences", []) if is_ug else [],
                    "twelfth_stream": a.get("stream", ""),
                    "twelfth_percentage": a.get("12th_percentage", ""),
                    "current_degree": a.get("degree_category", ""),
                    "degree_details": a.get("degree_course", ""),
                    "pg_preferences": a.get("preferences", []) if not is_ug else []
                }

                try:
                    response = requests.post(
                        st.secrets["GOOGLE_SCRIPT_URL"],
                        json=payload,
                        timeout=15
                    )

                    response.raise_for_status()
                    result = response.json()

                    if result.get("status") != "success":
                        raise Exception("Google Sheets rejected the submission.")

                    st.session_state.sheets_saved = True

                except Exception:
                    st.session_state.sheets_saved = False

                # MOVE TO SUCCESS PAGE
                st.session_state.page = "success"
                st.rerun()
              
    
   

# ==========================================
# SUCCESS PAGE
# ==========================================

if st.session_state.page == "success":

    st.progress(1.0)

    st.markdown("---")

    # Center the success card
    left, center, right = st.columns([1, 4, 1])

    with center:

        with st.container(border=True):

            st.markdown(
                "<h1 style='text-align:center;'>🎉</h1>",
                unsafe_allow_html=True
            )

            st.markdown(
                "<h2 style='text-align:center;'>"
                "Registration Submitted Successfully!"
                "</h2>",
                unsafe_allow_html=True
            )

            
           
            st.divider()

            st.markdown(
                "<h4 style='text-align:center;'>"
                "Thank You for Choosing B.C.M. College Kottayam (Autonomous)!"
                "</h4>",
                unsafe_allow_html=True
            )

           

            st.write("")

            if st.button(
                "Register another student",
                use_container_width=True,
                type="primary"
            ):

                for key, value in DEFAULTS.items():
                    st.session_state[key] = value

                for prefix in ["ug", "pg"]:
                    for i in range(1, 6):
                        st.session_state[
                            f"{prefix}pref{i}"
                        ] = "Not selected"

                st.session_state.page = "home"

                st.rerun()


# ==========================================
# FOOTER
# ==========================================

st.markdown("""
<div class="footer-text">
    B.C.M. College Kottayam (Autonomous)
    <br>
    Student Registration Portal
</div>
""", unsafe_allow_html=True)
