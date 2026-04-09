import streamlit as st
import json
import os
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import html
import re
import shutil

# --- STREAMLIT CLOUD GITHUB DEPLOYMENT FIX ---
# GitHub's drag-and-drop web uploader intentionally ignores hidden folders (like .streamlit)
# Since Streamlit themes require this hidden folder, we allow the user to upload 'theme_config.toml' 
# in the main directory, and then we auto-create the hidden folder and move the file as soon as the server boots.
if not os.path.exists(".streamlit"):
    os.makedirs(".streamlit", exist_ok=True)
if os.path.exists("theme_config.toml"):
    shutil.copy2("theme_config.toml", ".streamlit/config.toml")

# --- Setup & Constraints ---
st.set_page_config(page_title="TNPSC AEQuiz", layout="wide", initial_sidebar_state="expanded")

DB_FILE = "questions_v2.json"
USER_DATA_FILE = "user_performance.json"
SETTINGS_FILE = "app_settings.json"
RESULTS_FILE  = "student_results.json"
STUDENTS_FILE  = "students.json"

SYLLABUS_ORDER = {
    "Building Materials & Construction Practices": [
        "Brick", "Stones", "Aggregates & M-Sand", "Cement", "Admixtures",
        "Concrete (Self-compacting concrete)", "Mix Design", "Timber",
        "Recycled and modern materials - glass, plastic FRP, ceramic, steel",
        "Construction Practices: Masonry", "Construction Equipments", "Building bye-laws",
        "Provisions for fire safety, lighting and ventilation", "Acoustics"
    ],
    "Engineering Survey": [
        "Basics of Surveying", "Chain Surveying", "Compass Surveying", "Plane Table Surveying",
        "Levelling", "Computation of area and volume: L.S. and C.S.", "Contouring",
        "Theodolite surveying", "Traversing", "Tacheometry", "Triangulation", "Modern Surveying Techniques"
    ],
    "Engineering Mechanics & Strength of Materials": [
        "Forces: Types & Laws", "CoG & MI", "Friction", "Stresses and Strains",
        "Beams: SFD & BMD", "Theory of simple bending", "Deflection of beams", "Torsion",
        "Combined stresses", "Stress Transformations & Failure Theories", "Analysis of plane trusses"
    ],
    "Structural Analysis": [
        "Introduction to Analysis of Structures", "Force/Flexibility Methods of Analysis",
        "Displacement/Stiffness Methods of Analysis", "Arches", "Suspension cables",
        "Theory of columns", "Moving Loads and Influence Lines", "Matrix method",
        "Plastic theory", "Seismic analysis of high rise building"
    ],
    "Geotechnical Engineering": [
        "Formation & Types of soils", "Physical properties and testing of soils",
        "Classification of Soils for Engineering Practice", "Permeability of Soil",
        "Stress distribution in Soil", "Theory of Consolidation", "Shear strength of Soil",
        "Stability analysis of slope", "Shallow foundations", "Pile foundation",
        "Soil exploration & Sampling techniques", "Compaction of Soil", "Stabilization of soil",
        "Ground Improvement techniques"
    ],
    "Environmental Engineering": [
        "Sources & Demand of water", "Hydraulics for conveyance and transmission",
        "Characteristics, analysis of water & water borne diseases", "Functional design of water treatment",
        "Desalination plant", "Water distribution system & Pipe network analysis",
        "Planning and design of sewerage system & storm water drain",
        "Sewer appurtenances - Pumping & plumbing system in high rise building",
        "Characteristics and composition of sewage", "Sewage treatment and disposal",
        "Industrial waste water treatment", "Solid waste management",
        "Air and Noise pollution control", "E-Waste management"
    ],
    "RCC / Prestressed Concrete & Steel Structures": [
        "Working stress design concepts", "Limit state design concepts",
        "Design of Slabs (one way, Two way & Flat slabs)",
        "Design of Beam (singly, doubly reinforced & flanged sections)",
        "Design of Columns & Footings", "Staircase & Lintel",
        "Design of liquid storage structures (elevated and underground)",
        "Design of Retaining wall", "Pre-stressing - systems and Methods",
        "Design of Pre-Stressed Members for Flexure & Post tensioning slabs",
        "Design of Bolted and Welded connections", "Design of Tension members",
        "Design of Columns and Bases", "Design of Beams",
        "Design of Plate girder and Gantry girders", "Design of Members of Truss"
    ],
    "Hydraulics & Water Resources": [
        "Fluid Properties (Basics)", "Hydrostatic Pressure", "Kinematics of flow",
        "Fluid Dynamics (Applications of Bernoulli & Momentum equation)",
        "Flow through Pipes (Losses)", "Flow measurement in Channel", "Open Channel Flow",
        "Types of Pumps and Characteristics", "Water resources Planning and Management",
        "Runoff Estimation", "Hydrograph", "Flood Routing", "Flood Control",
        "Soil plant water relationship & Water requirements", "Irrigation Methods",
        "Design of Alluvial Canals", "Design of Head works",
        "Water logging and Land reclamation", "Cross Drainage works"
    ],
    "Urban & Transportation Engineering": [
        "Geometric Design of Highways", "Pavement Materials and Testing",
        "Design, Construction & Maintenance of Roads", "Railway Engineering",
        "Airport Engineering", "Harbour and Docks", "Urbanization and Slum",
        "Traffic Engineering"
    ],
    "Project Management & Estimating": [
        "Construction Management", "Project Management", "Estimation",
        "Tender", "Building Valuation"
    ]
}

SUBJECTS = [
    "Building Materials & Construction Practices",
    "Engineering Survey",
    "Engineering Mechanics & Strength of Materials",
    "Structural Analysis",
    "Geotechnical Engineering",
    "Environmental Engineering",
    "RCC / Prestressed Concrete & Steel Structures",
    "Hydraulics & Water Resources",
    "Urban & Transportation Engineering",
    "Project Management & Estimating"
]

# --- Custom Styling (Design System) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    /* ===== CLEAN LIGHT THEME ===== */
    :root {
        --primary: #0B2F9F;
        --accent:  #F97316;
        --success: #22C55E;
        --error:   #C62828;
    }

    /* Cream background - text deep navy for contrast */
    .stApp, .stApp > *, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], .main, .block-container {
        background-color: #FAF6EE !important;
        color: #1A1A2E !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Sidebar: deep blue with white text */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B2F9F 0%, #0D3461 100%) !important;
    }
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label { color: #FFFFFF !important; }
    [data-testid="stSidebar"] .stButton>button {
        background-color: #F97316 !important;
        color: #1A237E !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        border: none !important;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #22C55E !important;
        color: #FFFFFF !important;
    }

    /* Headers */
    h1 { color: #0B2F9F !important; font-weight: 700 !important;
         border-bottom: 3px solid #F97316; padding-bottom: 8px; }
    h2, h3, h4 { color: #0B2F9F !important; font-weight: 700 !important; }

    /* All body text: deep navy - maximum contrast on yellow */
    p, span, div, li, label { color: #0D1B4B !important; }

    /* Subject Cards */
    .subject-card {
        background: #FFFFFF;
        border-radius: 14px; padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-bottom: 18px;
        border-left: 6px solid #0B2F9F; transition: all 0.2s ease;
    }
    .subject-card:hover { transform: translateY(-4px); box-shadow: 0 6px 18px rgba(0,0,0,0.14); border-left-color: #F97316; }
    .subject-title { font-size: 16px; font-weight: 700; color: #0B2F9F !important; }
    .metric { font-size: 13px; color: #444444 !important; margin-bottom: 4px; }

    .stButton>button {
        background: #1B3F72 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        transition: all 0.2s;
        box-shadow: 0 2px 8px rgba(27,63,114,0.3);
    }
    .stButton>button * { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }
    .stButton>button:hover { background: #254E8F !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }

    /* Timer */
    .timer {
        font-size: 34px; font-weight: 700; color: #0B2F9F !important;
        text-align: center; background: #FFFDE7;
        padding: 10px 18px; border-radius: 12px;
        border: 2px solid #F97316; box-shadow: 0 2px 6px rgba(245,166,35,0.3);
    }

    /* Quiz Container */
    .quiz-container {
        background: #FFFFFF; border-radius: 14px; padding: 28px;
        box-shadow: 0 3px 14px rgba(0,0,0,0.08); margin-top: 18px;
        border-top: 4px solid #0B2F9F;
    }
    .question-number { color: #F97316 !important; font-weight: 700; font-size: 17px; }
    .question-text   { font-size: 19px; font-weight: 600; color: #0D1B4B !important; }

    /* Progress bar */
    .stProgress > div > div { background-color: #F97316 !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab"] { color: #0B2F9F; font-weight: 600; }
    .stTabs [aria-selected="true"] { border-bottom-color: #F97316 !important; color: #F97316 !important; }

    /* ====== RADIO BUTTON OPTIONS ====== */
    div[data-testid="stRadio"] label {
        font-size: 16px !important; font-weight: 600 !important;
        color: #111111 !important; background: #F8F9FA !important;
        border: 2px solid #0B2F9F !important; border-radius: 10px !important;
        padding: 10px 16px !important; margin-bottom: 8px !important;
        display: block !important; cursor: pointer !important; transition: all 0.18s ease !important;
    }
    div[data-testid="stRadio"] label:hover { background: #E3F2FD !important; border-color: #F97316 !important; color: #0D3461 !important; }
    div[data-testid="stRadio"] label p { color: #0D1B4B !important; font-size: 15px !important; font-weight: 600 !important; margin: 0 !important; }

    /* Form inputs */
    .stSelectbox label, .stTextInput label, .stTextArea label, .stNumberInput label {
        color: #0B2F9F !important; font-weight: 600 !important;
    }
    /* ====== MOBILE RESPONSIVENESS ====== */
    @media only screen and (max-width: 768px) {
        .block-container { padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 2rem !important; }
        h1 { font-size: 22px !important; }
        h2 { font-size: 20px !important; }
        h3 { font-size: 18px !important; }
        .question-text { font-size: 16px !important; }
        
        /* Stack main layout columns on mobile but PRESERVE question grid */
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        /* EXCEPTIONS: Keep the 5/6 column palette as a grid */
        div[data-testid="stHorizontalBlock"] div[data-testid="column"] button {
             width: auto !important;
        }
        
        /* Compact UI for Mobile */
        .timer { font-size: 22px !important; padding: 6px 10px !important; }
        .quiz-container { padding: 16px !important; margin-top: 10px !important; }
        .subject-card { padding: 12px !important; margin-bottom: 12px !important; }
        
        /* Radio labels more finger-friendly but compact */
        div[data-testid="stRadio"] label {
            padding: 8px 12px !important;
            font-size: 14px !important;
            margin-bottom: 6px !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# --- Data Handling ---

import google.generativeai as genai
GENAI_API_KEY = os.environ.get("GEMINI_API_KEY", "") 

if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)

def generate_questions_from_src(src_path, subject, unit, topic, subtopic, num_questions=5, dynamic_api_key=None):
    """
    Source-grounded Question Generation (NotebookLM Style)
    Strictly follows content flow of provided handwritten notes/PDFs.
    """
    active_key = dynamic_api_key.strip() if dynamic_api_key and dynamic_api_key.strip() else GENAI_API_KEY
    if not active_key:
        return {"error": "Google Gemini API key required for Source-Grounded Generation."}
        
    try:
        genai.configure(api_key=active_key)
        
        # Decide content part (PDF vs Image)
        is_pdf = src_path.lower().endswith('.pdf')
        if is_pdf:
            content_part = genai.upload_file(path=src_path)
            # Wait for the file to be processed (crucial for large PDFs)
            import time
            while content_part.state.name == "PROCESSING":
                time.sleep(2)
                content_part = genai.get_file(content_part.name)
            if content_part.state.name == "FAILED":
                return {"error": "PDF processing failed on Google servers."}
        else:
            from PIL import Image
            content_part = Image.open(src_path)
        
        # Use gemini-1.5-flash as default (fast and reliable)
        model_name = 'gemini-1.5-flash'
        model = genai.GenerativeModel(model_name)
        
        system_instruction = f"""
        You are a prestigious TNPSC AE (Civil Engineering) Exam Setter.
        BEHAVIOR: You act like Google NotebookLM—completely source-grounded.
        
        SOURCE MATERIAL: You are analyzing handwritten notes/PDFs for:
        Unit: {unit} 
        Topic: {topic}
        Subtopic: {subtopic}
        
        STRICT RULES:
        1. Generate exactly {num_questions} questions.
        2. SOURCE-BOUND: Every question MUST be derivable from the provided document. If the document is insufficient, return "Insufficient source material".
        3. CONTENT FLOW: Follow the logical progression of the handwritten notes.
        4. LEVEL: Moderate to Hard (Assistant Engineer Standard).
        5. ANTI-HALLUCINATION: Do not use external knowledge or general engineering facts if not mentioned or implied by formulas in the notes.
        6. NO DUPLICATES: Every question must be distinct.
        7. MATH NOTATION: Use actual Greek symbols (σ, τ, ε, θ, π, ϕ, Δ, λ) and math symbols (√, ±, ≠, ≤, ≥, ÷, ×) instead of writing them out as words like "sigma" or "root".
        """
        
        prompt = f"""
        Produce a balanced mix of these Question Types from the source:
        1. Theory-based MCQ
        2. Numerical / Problem-based (Show steps in explanation)
        3. Assertion–Reason (A: ..., R: ...)
        4. Match the Following (P,Q,R vs 1,2,3)
        5. Statement Combination (Select i, ii only, etc.)
        6. Diagram-based (Ask about specific symbols/sketches in the notes)

        OUTPUT SCHEMA (STRICT JSON ARRAY):
        [
            {{
                "questionText": "Full text of the question",
                "options": {{"a": "...", "b": "...", "c": "...", "d": "..."}},
                "correctAnswer": "a", 
                "detailedExplanation": "Cite relevant section from notes + full calculation steps if numerical.",
                "questionType": "Numerical",
                "difficultyLevel": "Hard",
                "diagramReference": "Mention specific sketch found in notes or 'None'",
                "unitTag": "{unit}",
                "topicTag": "{topic}",
                "subtopicTag": "{subtopic}"
            }}
        ]

        Return RAW JSON ONLY. No markdown wrappers.
        """
        
        response = model.generate_content([system_instruction, content_part, prompt])
        raw_text = response.text.strip()
        
        # Safety check for "Insufficient source material"
        if "Insufficient source material" in raw_text:
            return {"error": "The uploaded document does not contain enough information to generate questions for this subtopic."}

        # Robust JSON cleaning
        clean_text = re.sub(r'```json\s*|```', '', raw_text)
        json_data = json.loads(clean_text)
        
        return {"success": True, "questions": json_data}
        
    except Exception as e:
        return {"error": str(e)}

def generate_from_text_content(text_content, subject, subtopic, num_questions=25, dynamic_api_key=None):
    """
    Generates MCQs strictly from pasted Notebook LLM text content.
    """
    active_key = dynamic_api_key.strip() if dynamic_api_key and dynamic_api_key.strip() else GENAI_API_KEY
    if not active_key:
        return {"error": "Google Gemini API key required for AI Generation."}
        
    if not text_content or len(text_content.strip()) < 100:
        return {"error": "Content box is empty or too short. Please paste the Notebook LLM content."}

    try:
        genai.configure(api_key=active_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        system_msg = f"""
        You are a high-fidelity Question Extractor and Generator for TNPSC AE civil engineering exams.
        
        INPUT ANALYSIS:
        The text below contains content from Notebook LLM. It could be raw study notes OR a list of pre-written MCQs.
        
        YOUR MISSION:
        1. **STRICT EXTRACTION**: If the text already has questions using labels like "Question Text:", "Options:", "Correct Answer:", and "Detailed Explanation:", you MUST extract them exactly as written.
        2. **STRICT GENERATION**: If the text is raw notes, generate exactly {num_questions} new MCQs.
        
        TECHNICAL CONTEXT:
        Subject: {subject}, Subtopic: {subtopic}
        
        SYMBOLS RULE: Always use actual Unicode symbols (σ, ε, τ, θ, π, √, ≤, ≥, Δ) instead of writing "sigma", "epsilon", "tau", etc.
        
        TEXT SOURCE:
        {text_content}
        """
        
        prompt = """
        Output JSON in this structure:
        [
            {
                "question": "Question text",
                "options": {"a": "...", "b": "...", "c": "...", "d": "..."},
                "correct_answer": "a", 
                "explanation": "Reasoning...",
                "type": "Theory-based MCQ"
            }
        ]
        Return RAW JSON only.
        """
        
        response = model.generate_content([system_msg, prompt])
        raw_text = response.text.strip()
        
        # Clean JSON
        clean_text = re.sub(r'```json\s*|```', '', raw_text)
        json_data = json.loads(clean_text)
        
        # Add tags 
        for q in json_data:
            q["subject"] = subject
            q["subcategory"] = subtopic
            
        return {"success": True, "questions": json_data}
        
    except Exception as e:
        return {"error": str(e)}

def local_smart_extract(text_content, subject, subtopic):
    """
    Version 9.0: Enhanced Assertion-Reason & Match-the-Following Splitter.
    Solves the bug where "Assertion (A)" blocked the discovery of real options.
    Removes newline restriction on "Options:" divider.
    """
    import re
    questions = []
    # Normalize ALL line endings including single \r
    text_content = text_content.replace('\r\n', '\n').replace('\r', '\n')
    
    # 1. SPLIT INTO QUESTION BLOCKS (More lenient: Digit + space is enough)
    blocks = re.split(r'(?:\n|^)\s*\d+[.\)]?\s+', text_content)
    
    for block in blocks:
        block = block.strip()
        if not block or len(block) < 30: continue
        
        try:
            # Anchor detection (More flexible - can be middle of line)
            a_marker = re.search(r'\n\s*(?:Correct Answer|Correct|Ans|Key):', block, re.IGNORECASE)
            e_marker = re.search(r'\n\s*(?:Detailed Explanation|Explanation|Exp|Reasoning):', block, re.IGNORECASE)
            o_marker = re.search(r'\s*Options:', block, re.IGNORECASE)

            # --- Q-TEXT vs OPTIONS CORE SPLIT ---
            ans_start_root = a_marker.start() if a_marker else (e_marker.start() if e_marker else len(block))
            
            q_text = block
            opts_part = ""

            if o_marker:
                q_text = block[:o_marker.start()].strip()
                opts_part = block[o_marker.end():ans_start_root].strip()
            else:
                # Fallback: Find the first (a) marker. Optimized to find markers at start of line or after space.
                markers = list(re.finditer(r'(?:\n|\s|^)[(\[]?[aA][.\)\]]\s*', block))
                valid_a = None
                for m in markers:
                    # Ignore if surrounded by common non-option words
                    lb = block[max(0, m.start()-20) : m.start()].lower()
                    if any(k in lb for k in ["assertion", "statement", "list", "table", "group"]):
                        continue
                    valid_a = m
                    break
                
                if valid_a:
                    q_text = block[:valid_a.start()].strip()
                    opts_part = block[valid_a.start():ans_start_root].strip()

            # Final cleanup of Q_TEXT
            q_text = re.sub(r'^(?:Question\s*Text:\s*|Result:\s*)', '', q_text, flags=re.IGNORECASE).strip()
            q_text = re.sub(r'Options:\s*$', '', q_text, flags=re.IGNORECASE).strip()

            # --- OPTION PARSING (High-Precision Chronological Discovery) ---
            options = {"a": "Not found", "b": "Not found", "c": "Not found", "d": "Not found"}
            if opts_part:
                clean_opts_blob = re.sub(r'(?:Correct Answer|Correct|Ans|Key):.*$', '', opts_part, flags=re.IGNORECASE | re.DOTALL).strip()
                
                # Find ALL potential marker candidates (Lighter requirement on spaces)
                marker_pats = r'[(\[]?([a-dA-D])[.\)\]]\s*'
                all_matches = list(re.finditer(marker_pats, clean_opts_blob))
                
                # SEQUENCE-LOCKING: Force markers to appear in 'a -> b -> c -> d' order.
                # This prevents 'A.' at the end of 'explanation of A.' from stealing the A slot.
                valid_seq = []
                current_search_pos = 0
                for letter_goal in ['a', 'b', 'c', 'd']:
                    target = None
                    for m in all_matches:
                        if m.group(1).lower() == letter_goal and m.start() >= current_search_pos:
                            target = m
                            break
                    if target:
                        valid_seq.append(target)
                        current_search_pos = target.end()

                # Content Extraction based on Locked sequence
                for i in range(len(valid_seq)):
                    m = valid_seq[i]
                    letter = m.group(1).lower()
                    start_idx = m.end()
                    end_idx = valid_seq[i+1].start() if i+1 < len(valid_seq) else len(clean_opts_blob)
                    
                    if letter in options:
                        options[letter] = clean_opts_blob[start_idx:end_idx].strip()

            # --- ANSWER & EXPLANATION ---
            correct_ans = "a"
            if a_marker:
                ans_text = block[a_marker.end() : (e_marker.start() if e_marker else len(block))].strip()
                ltr = re.search(r'[a-dA-D]', ans_text, re.IGNORECASE)
                if ltr: correct_ans = ltr.group(0).lower()
                
            explanation = "Extracted from source content."
            if e_marker:
                explanation = block[e_marker.end():].strip()
            
            if all(v == "Not found" for v in options.values()): continue

            questions.append({
                "question": q_text,
                "options": options,
                "correct_answer": correct_ans,
                "explanation": explanation,
                "type": "Theory-based MCQ",
                "subject": subject,
                "subcategory": subtopic
            })
            
        except Exception:
            continue
            
    return {"success": True, "questions": questions}


# --- Data Handling ---
def load_db(file_path):
    if not os.path.exists(file_path): return []
    try:
        with open(file_path, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def save_db(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

def get_base64_image(image_path):
    import base64
    if not image_path or not isinstance(image_path, str): return None
    # If it's a URL, return as is
    if image_path.startswith(("http://", "https://")):
        return image_path
    
    # Check absolute or relative to CWD
    target_path = image_path
    if not os.path.isfile(target_path):
        # Check relative to this script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        target_path = os.path.join(base_dir, image_path)
    
    if os.path.isfile(target_path):
        try:
            with open(target_path, "rb") as f:
                data = f.read()
                ext = os.path.splitext(target_path)[1].lower().replace('.', '')
                if not ext: ext = "jpeg"
                b64 = base64.b64encode(data).decode()
                return f"data:image/{ext};base64,{b64}"
        except: return None
    return None

def sync_to_physical_vault(questions):
    """
    Ensures the physical ./MASTER_VAULT/ structure is an EXACT mirror of the provided question set.
    This fixes the 'indefinite appending' bug and strictly preserves publication order.
    """
    base_dir = "MASTER_VAULT"
    if not os.path.exists(base_dir): os.makedirs(base_dir)
    
    # 1. Group the provided questions by their target folder
    target_groups = {} # folder_path -> list of questions
    for q in questions:
        subj_name = "".join([c if c.isalnum() or c in " _-" else "_" for c in q.get("subject", "Uncategorized")])
        topic_name = "".join([c if c.isalnum() or c in " _-" else "_" for c in q.get("subcategory", "Uncategorized")])
        topic_dir = os.path.join(base_dir, subj_name, topic_name)
        
        if topic_dir not in target_groups:
            target_groups[topic_dir] = []
        target_groups[topic_dir].append(q)
    
    # 2. For each folder that has questions in this batch, update the file
    for folder, qs in target_groups.items():
        if not os.path.exists(folder): os.makedirs(folder)
        file_path = os.path.join(folder, "published_questions.json")
        
        # Load existing ONLY if we are doing a partial sync (usually we sync the whole 25-pack now)
        # But for 'Approve & Publish', we want to merge then prune.
        # Actually, the 'Approve & Publish' logic in the UI already gives us the FINAL 25.
        # So we should OVERWRITE to ensure strict 25-cap and order.
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(qs, f, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = load_db(DB_FILE)

if 'user_data' not in st.session_state:
    st.session_state.user_data = load_db(USER_DATA_FILE)

if 'settings' not in st.session_state:
    curr_settings = load_db(SETTINGS_FILE)
    if not curr_settings:
        curr_settings = {"quiz_duration_minutes": 22.5}
    st.session_state.settings = curr_settings

# --- Navigation & Auth State ---
if 'current_screen' not in st.session_state:
    st.session_state.current_screen = "LOGIN"
if 'login_user' not in st.session_state:
    st.session_state.login_user = None
if 'login_role' not in st.session_state:
    st.session_state.login_role = None  # 'student' or 'admin'
if 'selected_subject' not in st.session_state:
    st.session_state.selected_subject = None
if 'quiz_state' not in st.session_state:
    st.session_state.quiz_state = {}

def navigate(screen, **kwargs):
    st.session_state.current_screen = screen
    for k, v in kwargs.items():
        st.session_state[k] = v

# --- ADMIN PASSWORD ---
ADMIN_PASSWORD = "c3admin2024"

# --- LOGIN SCREEN ---
def screen_login():
    st.markdown("<h1 style='text-align: center; color:var(--primary); margin-bottom: 30px;'>C³ Institute – TNPSC AE Pro</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        tab_s, tab_a = st.tabs(["🎓 Student Login", "🔐 Admin Login"])
        
        with tab_s:
            st.markdown("### Student Login")
            s_name = st.text_input("Full Name", placeholder="Enter your registered name", key="s_name")
            s_roll = st.text_input("Roll Number", placeholder="Enter your roll number", key="s_roll")
            s_email = st.text_input("Email ID", placeholder="Enter your registered email", key="s_email")
            s_pwd = st.text_input("Password", type="password", placeholder="Enter your password", key="s_pwd")
            if st.button("Login as Student →", key="btn_student"):
                if s_name.strip() and s_roll.strip() and s_email.strip() and s_pwd.strip():
                    students = load_db(STUDENTS_FILE)
                    if not isinstance(students, list): students = []
                    
                    found_user = None
                    for s in students:
                        if (s.get("email") == s_email.strip() and 
                            s.get("password") == s_pwd.strip() and 
                            s.get("name") == s_name.strip() and 
                            s.get("roll_no") == s_roll.strip()):
                            found_user = s.get("name")
                            break
                            
                    if found_user:
                        st.session_state.login_user = found_user
                        st.session_state.login_role = "student"
                        navigate("HOME")
                        st.rerun()
                    else:
                        st.error("Invalid Credentials. Please ensure Name, Roll No, Email, and Password match exactly.")
                else:
                    st.error("Please fill in all fields (Name, Roll No, Email, Password).")
        with tab_a:
            st.markdown("### Admin Login")
            a_pwd = st.text_input("Admin Password", type="password", key="a_pwd")
            if st.button("Login as Admin →", key="btn_admin"):
                if a_pwd == ADMIN_PASSWORD:
                    st.session_state.login_user = "Admin"
                    st.session_state.login_role = "admin"
                    navigate("HOME")
                    st.rerun()
                else:
                    st.error("Incorrect admin password.")

# --- Sidebar (only shown after login) ---
if st.session_state.login_role:  # logged in
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "c3_logo.png")
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, use_container_width=True)
    st.sidebar.markdown("---")
    role = st.session_state.login_role
    user = st.session_state.login_user
    st.sidebar.markdown(f"**{'👨‍💻 Admin' if role == 'admin' else '🎓 Student'}:** {user}")
    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 Home Dashboard"): navigate("HOME")
    if role == "student":
        if st.sidebar.button("📈 My Analytics"): navigate("ANALYTICS")
    if role == "admin":
        if st.sidebar.button("⚙️ Settings"): navigate("SETTINGS")
        if st.sidebar.button("👨‍💻 Admin Panel"): navigate("ADMIN")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.login_user = None
        st.session_state.login_role = None
        navigate("LOGIN")
        st.rerun()

# --- SCREENS ---

def screen_home():
    st.markdown("<h1>👋 Welcome back to C³ Institute App</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:var(--secondary)'>Track your syllabus completion and subject-wise accuracy in real-time.</p>", unsafe_allow_html=True)
    
    user_name = st.session_state.get("login_user", "")
    all_results = load_db(RESULTS_FILE)
    if not isinstance(all_results, list): all_results = []
    
    # Group best accuracy per subcategory for the current user
    user_stats = {} # {subject: {subcategory: max_accuracy}}
    for r in all_results:
        if r.get("student_name") == user_name:
            s, sc = r.get("subject"), r.get("subcategory")
            acc = float(r.get("accuracy", 0))
            if s not in user_stats: user_stats[s] = {}
            if acc > user_stats[s].get(sc, 0):
                user_stats[s][sc] = acc

    cols = st.columns(2)
    for i, subj in enumerate(SUBJECTS):
        col = cols[i % 2]
        
        # Calculate dynamic metrics
        subcats = SYLLABUS_ORDER.get(subj, [])
        total_modules = len(subcats)
        
        subj_results = user_stats.get(subj, {})
        avg_score = sum(subj_results.values()) / len(subj_results) if subj_results else 0
        cleared_modules = sum(1 for acc in subj_results.values() if acc >= 90)
        progress_pct = (cleared_modules / total_modules * 100) if total_modules > 0 else 0
        
        # Admin override
        if user_name == "Admin":
            progress_pct = 100
            avg_score = 100

        with col:
            st.markdown(f"""
            <div class="subject-card">
                <div class="subject-title">{subj}</div>
                <div class="metric">📚 Modules: {total_modules} Subtopics</div>
                <div class="metric">✅ Average Score: {avg_score:.1f}%</div>
                <div class="metric">🏁 Completion: {cleared_modules}/{total_modules} Modules (90% threshold)</div>
                <div style="width: 100%; background-color: #eee; border-radius: 4px; height: 10px; margin-top: 10px;">
                  <div style="width: {progress_pct}%; background-color: var(--accent); height: 100%; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Open {subj}", key=f"open_{i}"):
                navigate("SUBJECT_DETAIL", selected_subject=subj)

def screen_subject_detail():
    subj = st.session_state.selected_subject
    st.button("⬅ Back to Home", on_click=navigate, args=("HOME",))
    st.markdown(f"<h1>📘 {subj}</h1>", unsafe_allow_html=True)
    
    st.subheader("Syllabus Modules (Locked until 90% cleared)")
    subj_quests = [q for q in st.session_state.db if q.get("subject") == subj]
    subcats = SYLLABUS_ORDER.get(subj, ["Core Concepts"])
    
    # Check student progression (90% to unlock)
    user_name = st.session_state.get("login_user", "")
    all_results = load_db(RESULTS_FILE)
    if not isinstance(all_results, list): all_results = []
    
    # Find max score percentage for each subcategory for this user
    user_max_scores = {}
    for r in all_results:
        if r.get("student_name") == user_name and r.get("subject") == subj:
            sc_name = r.get("subcategory", "")
            acc = float(r.get("accuracy", 0))
            if acc > user_max_scores.get(sc_name, 0):
                user_max_scores[sc_name] = acc

    is_unlocked = True # First subtopic is always unlocked
    
    for i, sc in enumerate(subcats):
        col_title, col_badge = st.columns([3, 1])
        
        # 25-Question Constraint Check (Strict Matching)
        sc_qs_total = [q for q in subj_quests if q.get("subcategory") == sc]
        # Published for students specifically
        sc_qs_pub = [q for q in sc_qs_total if q.get("is_published", True)]
        
        q_count = len(sc_qs_total)
        q_count_pub = len(sc_qs_pub)
        is_ready = (q_count_pub >= 25)
        
        # Admin sees logic for ready, Student sees logic for published
        sc_qs = sc_qs_pub if user_name != "Admin" else sc_qs_total
        
        # Calculate status badge
        status = "🔒 Locked"
        status_color = "#555555"
        
        max_score = user_max_scores.get(sc, 0)
        
        if user_name == "Admin":
            status = f"🔵 Active ({q_count}/25)"
            status_color = "#0B2F9F"
            is_unlocked = True
        elif not is_ready:
            status = "🔜 Under Review"
            status_color = "#9E9E9E"  # Grey for incomplete
            # If not ready, it's effectively locked for student progression too
        elif is_unlocked:
            if max_score >= 90:
                status = "🟢 Cleared"
                status_color = "var(--success)"
            elif max_score > 0:
                status = "🟡 Attempted"
                status_color = "var(--accent)"
            else:
                status = "🔵 Active"
                status_color = "#0B2F9F"
        
        with col_title:
            if not is_unlocked or (not is_ready and user_name != "Admin"):
                st.markdown(f"<h3 style='color: #999; text-decoration: line-through;'>• {sc}</h3>", unsafe_allow_html=True)
                if not is_ready and user_name != "Admin":
                    st.caption(f"Waiting for Admin to publish 25 questions (Current: {q_count})")
            else:
                st.markdown(f"### • {sc}")
                
        with col_badge:
            st.markdown(f"<div style='background-color: {status_color}; color: white; padding: 4px 12px; border-radius: 20px; text-align: center; font-weight: bold; font-size: 13px; margin-top: 15px;'>{status}</div>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([2, 1, 1])
        # Always show 25 if ready, actual count if under review (to help admin)
        display_count = 25 if q_count_pub >= 25 else q_count_pub
        if user_name == "Admin":
            admin_display_count = 25 if q_count >= 25 else q_count
            col1.write(f"📊 **Admin Bank:** {admin_display_count}/25 | **Student Portal:** {'✅ Live' if is_ready else '🔜 Draft'}")
        else:
            col1.write(f"Questions: {display_count} | Time: 22.5 mins")
        
        # Determine if student can click Start
        can_start = is_unlocked and (is_ready or user_name == "Admin")
        
        if not can_start:
            col2.button("Start Quiz", key=f"start_{sc}", disabled=True)
        elif col2.button("Start Quiz", key=f"start_{sc}"):
            # SHUFFLE AND PRUNE TO EXACTLY 25 FOR THE USER
            import random
            random.shuffle(sc_qs)
            
            qs = sc_qs
            if len(qs) > 25:
                qs = qs[:25]
            elif len(qs) < 25 and len(qs) > 0:
                # Pad if needed (though is_ready ensures at least 25 for students)
                needed = 25 - len(qs)
                pool = list(qs)
                while len(qs) < 25:
                    qs.append(random.choice(pool))
            
            st.session_state.quiz_state = {
                "questions": qs,
                "answers": {},
                "status": {str(i): 0 for i in range(len(qs))},
                "start_time": time.time(),
                "idx": 0
            }
            st.session_state.quiz_state["status"]["0"] = 2
            navigate("QUIZ")
        col3.button("Analytics", key=f"stat_{sc}", on_click=navigate, args=("ANALYTICS",))
        st.divider()
        
        # Next subtopic is only unlocked if the current one has a score >= 90% (unless Admin)
        if max_score < 90 and user_name != "Admin":
            is_unlocked = False

def screen_quiz():
    qs = st.session_state.quiz_state["questions"]
    idx = st.session_state.quiz_state["idx"]
    start_t = st.session_state.quiz_state["start_time"]
    
    # Timer logic
    elapsed = time.time() - start_t
    duration = st.session_state.settings.get("quiz_duration_minutes", 22.5)
    max_time = duration * 60 
    rem = max_time - elapsed
    
    if rem <= 0:
        st.warning("Time is up!")
        navigate("SUMMARY")
        st.rerun()
        
    mins, secs = divmod(int(rem), 60)
    
    # Force the current question to at least "Not Answered" (2) if it was "Not Visited" (0)
    if st.session_state.quiz_state["status"].get(str(idx), 0) == 0:
        st.session_state.quiz_state["status"][str(idx)] = 2
        
    # --- CBT SPLIT LAYOUT ---
    left_col, right_col = st.columns([2.5, 1.5], gap="medium")
    
    with right_col:
        # Profile & Timer Block (Compact for Mobile)
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 6px; border-radius: 6px; border: 1px solid #ddd; text-align: center; margin-bottom: 10px;">
            <div style="font-size: 14px; font-weight: bold; color: #0B2F9F;">👤 {st.session_state.get('login_user', 'Student')}</div>
            <div style="color: var(--error); font-weight: bold; font-size: 16px; margin-top:4px;">⏱️ {mins:02d}:{secs:02d}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Shortened Palette Title for Mobile
        st.markdown("<div style='font-size:14px; font-weight:700; color:#0B2F9F; margin-bottom:5px;'>Question Palette</div>", unsafe_allow_html=True)
        
        # Calculate Stats for the Legend
        stats = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        for s in st.session_state.quiz_state["status"].values():
            stats[s] = stats.get(s, 0) + 1
            
        # Compact Legend using Grid
        st.markdown(f"""
        <div style="font-size: 11px; margin-bottom: 10px; line-height: 1.3; display: grid; grid-template-columns: 1fr 1fr; gap: 4px; color: #555;">
            <div>🟢 {stats[1]} Ans</div>
            <div>🔴 {stats[2]} No Ans</div>
            <div>⚪ {stats[0]} Open</div>
            <div>🟣 {stats[3]} Mark</div>
            <div style="grid-column: span 2;">✅ {stats[4]} Ans+Mark</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Ultra-compact Question Palette for Mobile (Final Form)
        st.markdown('''
        <style>
        div[data-testid="column"] button {
            margin: 1px 0px !important;
            padding: 1px 0px !important;
            min-height: 38px !important;
            height: 38px !important;
            background: #1B3F72 !important;
            border-radius: 4px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border: 1px solid #0B2F9F !important;
        }
        div[data-testid="column"] button p {
            font-size: 10px !important;
            white-space: pre-wrap !important;
            word-break: keep-all !important;
            margin: 0 !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            line-height: 1.0 !important;
            gap: 1px !important;
            color: #FFFFFF !important;
        }
        /* Mobile Question Text Scaling */
        @media only screen and (max-width: 600px) {
            .question-text { font-size: 15px !important; line-height: 1.5 !important; }
            h3 { font-size: 18px !important; }
        }
        </style>
        ''', unsafe_allow_html=True)
        
        # Grid Rendering (6 Columns for better horizontal spread on mobile)
        grid_cols = st.columns(6, gap="small")
        for i in range(len(qs)):
            state = st.session_state.quiz_state["status"].get(str(i), 0)
            
            col_idx = i % 6
            with grid_cols[col_idx]:
                btn_emoji = ""
                if state == 1: btn_emoji = "🟢"
                elif state == 2: btn_emoji = "🔴"
                elif state == 3: btn_emoji = "🟣"
                elif state == 4: btn_emoji = "✅"
                else: btn_emoji = "⚪"

                # Use newline to guarantee vertical stack as requested
                if st.button(f"{btn_emoji}\n{i+1}", key=f"grid_btn_{i}", use_container_width=True):
                    st.session_state.quiz_state["idx"] = i
                    st.rerun()

        st.divider()
        if st.button("Submit Profile", use_container_width=True, type="primary"):
            navigate("SUMMARY")
            
            
    with left_col:
        # Question Rendering
        q = qs[idx]
        
        # 1. Escape HTML FIRST to protect symbols like < or σ
        safe_q = html.escape(q['question'])
        
        # 2. THEN apply Smart Formatting (so our tags remain valid HTML)
        if re.search(r'\s([1-4]{1}\.\s)', safe_q):
            safe_q = re.sub(r'\s([1-4]{1}\.\s)', r'<br/><br/><b>\1</b>', safe_q)

        header_col1, header_col2 = st.columns([3, 1])
        header_col1.markdown(f"<h3 style='margin-top:0px; color:#0B2F9F;'>Question {idx+1}</h3>", unsafe_allow_html=True)
        header_col2.markdown(f"<div style='text-align:right; color:grey; font-size:12px; margin-top:10px;'>Type: {q.get('type','MCQ')}</div>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='question-text' style='font-size: 18px; margin-bottom: 25px; line-height:1.6;'>{safe_q}</div>", unsafe_allow_html=True)
        
        if q.get('imageUrl'):
            img_src = get_base64_image(q['imageUrl'])
            if img_src:
                st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
                st.image(img_src, width=500, caption="Study the diagram carefully")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                # Silently fail for students, but ALERT admins
                if st.session_state.get("login_role") == "admin":
                    st.error(f"🚨 ADMIN ALERT: This '{q.get('type')}' question is MISSING its image file! Path: {q.get('imageUrl')}")
                elif q.get('type') == 'Diagram Based':
                    st.warning("⚠️ Diagram loading... (If it doesn't appear, please contact the administrator)")
            
        # Render Options
        raw_opts = q.get("options", {})
        opt_keys = [k for k in raw_opts.keys() if raw_opts[k].strip()]
        opt_lbls = [f"{k.upper()}) {raw_opts[k].strip()}" for k in opt_keys]
        
        if not opt_lbls:
            st.warning("This question has no options.")
            ans = None
        else:
            prev_ans_i = None
            if str(idx) in st.session_state.quiz_state["answers"]:
                prev_ans_val = st.session_state.quiz_state["answers"][str(idx)]
                for i, ok in enumerate(opt_keys):
                    if ok == prev_ans_val: prev_ans_i = i

            ans = st.radio("Select your active answer:", opt_lbls, index=prev_ans_i, key=f"q_radio_{idx}")
        
        # --- CBT Bottom Action Ribbon ---
        st.markdown("<hr style='margin: 10px 0px;'/>", unsafe_allow_html=True)
        action_c1, action_c2, action_c3 = st.columns([1, 1, 1])
        
        # Calculate Next Index safely
        next_idx = idx + 1 if idx < len(qs) - 1 else 0
        
        with action_c1:
            if st.button("Save & Next", use_container_width=True):
                # Save answer if selected
                if ans:
                    ans_key = ans.split(")")[0].lower().strip()
                    st.session_state.quiz_state["answers"][str(idx)] = ans_key
                    # Update status to Answered (1) ONLY if it wasn't marked for review
                    current_status = st.session_state.quiz_state["status"].get(str(idx), 0)
                    if current_status == 3 or current_status == 4:
                        st.session_state.quiz_state["status"][str(idx)] = 4 # Answered & Marked
                    else:
                        st.session_state.quiz_state["status"][str(idx)] = 1 # Answered purely
                else:
                    # If they hit Save without selecting, it remains Not Answered (2)
                    st.session_state.quiz_state["status"][str(idx)] = 2
                    
                st.session_state.quiz_state["idx"] = next_idx
                st.rerun()
                
        with action_c2:
            if st.button("Clear Response", use_container_width=True):
                # Wipe answer
                if str(idx) in st.session_state.quiz_state["answers"]:
                    del st.session_state.quiz_state["answers"][str(idx)]
                # Reset status strictly to Not Answered (2) since they are viewing it
                st.session_state.quiz_state["status"][str(idx)] = 2
                st.rerun()
                
        with action_c3:
            if st.button("Mark for Review & Next", use_container_width=True):
                if ans:
                    ans_key = ans.split(")")[0].lower().strip()
                    st.session_state.quiz_state["answers"][str(idx)] = ans_key
                        
                # Ensure status accounts for whether there's an answer actively saved
                if str(idx) in st.session_state.quiz_state["answers"]:
                    st.session_state.quiz_state["status"][str(idx)] = 4 # Answered & Marked
                else:
                    st.session_state.quiz_state["status"][str(idx)] = 3 # Only Marked
                    
                st.session_state.quiz_state["idx"] = next_idx
                st.rerun()

def screen_summary():
    st.markdown("<h1>📊 Quiz Summary</h1>", unsafe_allow_html=True)
    
    qs = st.session_state.quiz_state["questions"]
    ans = st.session_state.quiz_state.get("answers", {})
    elapsed = time.time() - st.session_state.quiz_state["start_time"]
    
    correct = 0
    incorrect = 0
    skipped = len(qs) - len(ans)
    
    for i, q in enumerate(qs):
        u_ans = ans.get(str(i))
        if u_ans == q.get("correct_answer"):
            correct += 1
        elif u_ans is not None:
            incorrect += 1
            
    score_pct = (correct / len(qs)) * 100 if len(qs) > 0 else 0
    
    # Calculate 5-State breakdown
    stats = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    for s in st.session_state.quiz_state.get("status", {}).values():
        stats[s] = stats.get(s, 0) + 1
        
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 25px;">
        <h4 style="margin-top:0px; color:#0B2F9F;">Question Status Breakdown</h4>
        <ul style="list-style-type: none; padding: 0; line-height: 1.8;">
            <li><span style="background-color:#4CAF50; color:white; padding:2px 8px; border-radius:4px; margin-right:10px;">{stats[1]}</span> Answered</li>
            <li><span style="background-color:#F44336; color:white; padding:2px 8px; border-radius:4px; margin-right:10px;">{stats[2]}</span> Not Answered</li>
            <li><span style="background-color:#EEEEEE; color:black; border:1px solid #ccc; padding:2px 8px; border-radius:4px; margin-right:10px;">{stats[0]}</span> Not Visited</li>
            <li><span style="background-color:#9C27B0; color:white; padding:2px 8px; border-radius:20px; margin-right:10px;">{stats[3]}</span> Marked for Review</li>
            <li><span style="background-color:#9C27B0; color:white; border-bottom:3px solid #4CAF50; padding:2px 8px; border-radius:20px; margin-right:10px;">{stats[4]}</span> Answered & Marked</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    rating = "Needs Improvement 🔴"
    if score_pct > 80: rating = "Excellent 🌟"
    elif score_pct >= 60: rating = "Good 👍"
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Score", f"{correct} / {len(qs)}")
    c2.metric("Accuracy", f"{score_pct:.1f}%")
    c3.metric("Time Taken", f"{int(elapsed//60)}m {int(elapsed%60)}s")
    c4.metric("Rating", rating)
    
    # --- Save result to file ---
    from datetime import datetime
    result_entry = {
        "student_name": st.session_state.get("login_user", "Unknown"),
        "student_id":   st.session_state.get("login_user", "?"),
        "subject":      qs[0].get("subject", "?") if qs else "?",
        "subcategory":  qs[0].get("subcategory", "?") if qs else "?",
        "score":        correct,
        "total":        len(qs),
        "accuracy":     round(score_pct, 1),
        "time_taken":   f"{int(elapsed//60)}m {int(elapsed%60)}s",
        "rating":       rating,
        "date":         datetime.now().strftime("%Y-%m-%d"),
        "time":         datetime.now().strftime("%H:%M")
    }
    # Load existing, append, save
    existing = load_db(RESULTS_FILE)
    if not isinstance(existing, list): existing = []
    existing.append(result_entry)
    save_db(existing, RESULTS_FILE)
    
    st.markdown("---")
    res_cols = st.columns(3)
    if res_cols[0].button("🔍 Review Answers"): navigate("REVIEW")
    if res_cols[1].button("🔄 Retake Quiz"): 
        st.session_state.quiz_state["answers"] = {}
        st.session_state.quiz_state["idx"] = 0
        st.session_state.quiz_state["start_time"] = time.time()
        navigate("QUIZ")
    if res_cols[2].button("🚪 Back to Subject"): navigate("SUBJECT_DETAIL")

def screen_review():
    st.button("⬅ Back to Summary", on_click=navigate, args=("SUMMARY",))
    st.markdown("<h1>🔍 Answer Review</h1>", unsafe_allow_html=True)
    
    qs = st.session_state.quiz_state["questions"]
    ans = st.session_state.quiz_state.get("answers", {})
    
    for i, q in enumerate(qs):
        u_ans = ans.get(str(i), "Skipped")
        c_ans = q.get("correct_answer")
        
        is_corr = u_ans == c_ans
        bg = "#e8f5e9" if is_corr else "#ffebee"
        border = "var(--success)" if is_corr else "var(--error)"
        img_src = get_base64_image(q.get("imageUrl"))
        
        # Escape symbols FIRST
        safe_q_rev = html.escape(q['question'])
        # Optional: apply formatting if needed in review
        if re.search(r'\s([1-4]{1}\.\s)', safe_q_rev):
            safe_q_rev = re.sub(r'\s([1-4]{1}\.\s)', r'<br/><br/><b>\1</b>', safe_q_rev)

        st.markdown(f"""
<div style="background:{bg}; border-left:5px solid {border}; padding:15px; border-radius:8px; margin-bottom:15px;">
    <b>Q{i+1}: {safe_q_rev}</b><br/><br/>
    {f'<img src="{img_src}" style="max-width:400px; border-radius:8px; margin-bottom:15px; border:1px solid #ddd;"><br/>' if img_src else ""}
    <span style="color:grey;">Your Answer:</span> {u_ans.upper() if u_ans != 'Skipped' else 'Skipped'}<br/>
    <span style="color:var(--success); font-weight:bold;">Correct Answer:</span> {c_ans.upper() if c_ans else 'N/A'}<br/>
    <hr/>
    <b>Explanation:</b> {q.get('explanation', 'No explanation provided.')}
</div>
""", unsafe_allow_html=True)

def screen_admin():
    st.title("Admin Dashboard - Question Bank Management")
    st.warning("C³ Institute Master Database Control")
    
    # MASTER ADMIN STATE SYNC
    if "admin_subj" not in st.session_state: st.session_state.admin_subj = SUBJECTS[0]
    if "admin_subcat" not in st.session_state: st.session_state.admin_subcat = SYLLABUS_ORDER.get(st.session_state.admin_subj, ["General"])[0]

    t1, t_ai, t2, t3, t_student, t4, t5 = st.tabs(["Add Question", "🤖 AI Generator", "Edit Question", "Student Stats", "🎓 Students", "📑 Question Bank", "⚙️ Settings"])
    
    with t1:
        st.subheader("Add Question (All Formats)")
        # Sync index with master state
        s_idx_t1 = SUBJECTS.index(st.session_state.admin_subj) if st.session_state.admin_subj in SUBJECTS else 0
        subj = st.selectbox("Subject", SUBJECTS, index=s_idx_t1, key="admin_subj_t1", label_visibility="collapsed")
        st.session_state.admin_subj = subj
        
        subcat_opts = SYLLABUS_ORDER.get(subj, ["Core Concepts"])
        sc_idx_t1 = subcat_opts.index(st.session_state.admin_subcat) if st.session_state.admin_subcat in subcat_opts else 0
        subcat = st.selectbox("Subcategory", subcat_opts, index=sc_idx_t1, key="admin_subcat_t1")
        st.session_state.admin_subcat = subcat
        
        q_type = st.selectbox("Question Type", [
            "Theory-based MCQ", "Numerical/Problem-based", "Assertion-Reason", 
            "Match the Following", "Statement type (True/False)", "Diagram-based"
        ])
        
        q_text = st.text_area("Question Text")
        
        # Image Upload (Available for ALL types)
        st.markdown("---")
        st.write("🖼️ **Question Image / Diagram (Optional)**")
        img_file = st.file_uploader("Upload Diagram (JPEG/PNG)", type=["jpg", "jpeg", "png"], key="t1_img_upload")
        
        # Initialize default or uploaded path
        img_url = ""
        if img_file:
            save_path = os.path.join("assets", "question_images", img_file.name)
            if not os.path.exists(os.path.dirname(save_path)): os.makedirs(os.path.dirname(save_path))
            with open(save_path, "wb") as f:
                f.write(img_file.getbuffer())
            img_url = save_path
            # Force injection into session state to prevent stale values
            st.session_state["t1_img_url_manual"] = img_url
            st.success(f"✅ Diagram '{img_file.name}' Ready!")

        # Always show text input to allow URLs or manual paths, pre-filled with upload result
        img_url = st.text_input("Final Image Path or URL (Auto-filled on upload)", value=img_url, key="t1_img_url_manual")
        
        if img_url:
            preview_src = get_base64_image(img_url)
            if preview_src:
                st.image(preview_src, width=250, caption="Preview of Selected Diagram")
            else:
                st.error("❌ Image path found but cannot be loaded.")
        st.markdown("---")
            
        c1, c2 = st.columns(2)
        oa = c1.text_input("Option A")
        ob = c2.text_input("Option B")
        oc = c1.text_input("Option C")
        od = c2.text_input("Option D")
        
        corr = st.selectbox("Correct Option", ["a", "b", "c", "d"])
        exp = st.text_area("Explanation (Critical for performance review)")
        
        pub_live = st.checkbox("🚀 Publish Directly to Student Portal", value=True)
        
        # LIVE PREVIEW CARD (Below the form)
        st.markdown("---")
        st.subheader("👀 Live Question Preview (As Student Sees It)")
        p_img_src = get_base64_image(img_url)
        # Smart formatting for civil engineering statements
        p_disp_q = q_text
        import re
        if re.search(r'\s([1-4]{1}\.\s)', p_disp_q):
            p_disp_q = re.sub(r'\s([1-4]{1}\.\s)', r'<br/><br/><b>\1</b>', p_disp_q)
            
        p_html = f"""
<div style='background:white; border-radius:12px; padding:28px; border-top:5px solid #0B2F9F; border-right:1px solid #ddd; border-bottom:1px solid #ddd; border-left:1px solid #ddd; box-shadow: 0 4px 10px rgba(0,0,0,0.05);'>
<div style='color: #F97316; font-weight:700; font-size:16px; margin-bottom:10px;'>{html.escape(q_type)} Preview</div>
<div style='font-size:19px; font-weight:600; color:#0D1B4B; margin-bottom:20px; line-height:1.6;'>{html.escape(p_disp_q)}</div>
{(f'<div style="text-align:center;"><img src="{p_img_src}" style="max-width:450px; border-radius:8px; margin-bottom:20px; border:1px solid #ccc;"></div>' if p_img_src else "")}
<div style='background: #F8F9FA; border: 2px solid #0B2F9F; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;'><b>A)</b> {html.escape(oa)}</div>
<div style='background: #F8F9FA; border: 2px solid #0B2F9F; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;'><b>B)</b> {html.escape(ob)}</div>
<div style='background: #F8F9FA; border: 2px solid #0B2F9F; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;'><b>C)</b> {html.escape(oc)}</div>
<div style='background: #F8F9FA; border: 2px solid #0B2F9F; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;'><b>D)</b> {html.escape(od)}</div>
</div>
"""
        st.markdown(p_html, unsafe_allow_html=True)
        st.markdown("---")
        
        if st.button("Save Question to Master Bank"):
            new_q = {
                "subject": subj, "subcategory": subcat,
                "type": q_type, "question": q_text,
                "options": {"a": oa, "b": ob, "c": oc, "d": od},
                "correct_answer": corr, "explanation": exp,
                "imageUrl": img_url,
                "is_published": pub_live,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.db.append(new_q)
            save_db(st.session_state.db, DB_FILE)
            # Re-sync physical vault
            sync_to_physical_vault(st.session_state.db)
            st.success("Appended to Admin Master Bank and Synced to Vault.")
            time.sleep(1); st.rerun()
            
    with t_ai:
        st.subheader("🛠️ Admin Control Panel – Generative AI Module")
        st.info("Follow the 2-step source board process to generate and moderate TNPSC items.")
        
        st.markdown("### 🔹 1. Subject & Subtopic Mapping")
        c_map1, c_map2 = st.columns(2)
        s_idx_ai = SUBJECTS.index(st.session_state.admin_subj) if st.session_state.admin_subj in SUBJECTS else 0
        sel_subj = c_map1.selectbox("Select Subject", SUBJECTS, index=s_idx_ai, key="admin_subj_ai", label_visibility="collapsed")
        st.session_state.admin_subj = sel_subj
        
        subcats_in_subj = SYLLABUS_ORDER.get(sel_subj, ["General"])
        sc_idx_ai = subcats_in_subj.index(st.session_state.admin_subcat) if st.session_state.admin_subcat in subcats_in_subj else 0
        sel_subcat = c_map2.selectbox("Select Sub Topic", subcats_in_subj, index=sc_idx_ai, key="admin_subcat_ai")
        st.session_state.admin_subcat = sel_subcat

        # Load pinned URL if exists
        source_mapping = st.session_state.settings.get("source_mapping", {})
        default_link = "https://notebooklm.google.com/notebook/aad77411-f703-4c7e-b806-ca6f61573dff"
        
        pinned_url = source_mapping.get(sel_subcat, default_link)
        col_url, col_pin = st.columns([3, 1])
        notebook_url = col_url.text_input("Paste Notebook LLM Source URL", value=pinned_url, placeholder="https://notebooklm.google.com/...", key="v4_url")
        
        if col_pin.button("📌 Pin Source", use_container_width=True):
            if "source_mapping" not in st.session_state.settings:
                st.session_state.settings["source_mapping"] = {}
            st.session_state.settings["source_mapping"][sel_subcat] = notebook_url
            save_db(st.session_state.settings, SETTINGS_FILE)
            st.success("Pinned!")
            time.sleep(0.5); st.rerun()

        with st.expander("🔓 How to allow other emails to open this link?"):
            st.markdown("""
            1. Open your **Notebook LM** source.
            2. Click the **'Share'** button (Top Right).
            3. Change 'Restricted' to **'Anyone with the link'**.
            4. Set role to **'Viewer'**.
            5. Copy that link and paste it above! 
            *Now anyone logged into ANY mail can open this research source.*
            """)

        if notebook_url.startswith("http"):
            st.markdown(f"🔗 **Universal Access Link:** [Global Research Link]({notebook_url})")

        # SMART-MATCH PULSE (Synchronized with student logic)
        db_qs = []
        for q in st.session_state.db:
            q_subj = q.get("subject", "")
            q_sc = q.get("subcategory", "")
            if q_subj == sel_subj:
                # Fuzzy match: "Brick" matches "Bricks" or "Bricks, Stones & Cement"
                if sel_subcat.lower() in q_sc.lower() or q_sc.lower() in sel_subcat.lower():
                    db_qs.append(q)

        q_count = len(db_qs)
        goal = 25
        progress_pct = min(100, int((q_count / goal) * 100))
        
        st.markdown(f"""
        <div style='background: white; border-radius:12px; padding:20px; border:1px solid #ddd; margin-bottom:20px; box-shadow: 0 4px 10px rgba(0,0,0,0.03);'>
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                <span style='font-size:16px; font-weight:700; color:#0B2F9F;'>📊 Live Topic Pulse: {sel_subcat}</span>
                <span style='font-size:14px; font-weight:700; color:{"#22C55E" if q_count >= goal else "#F97316"};'>
                    {q_count} / {goal} Questions Verified
                </span>
            </div>
            <div style='width: 100%; background-color: #eee; border-radius: 6px; height: 12px; margin-bottom:10px;'>
                <div style='width: {progress_pct}%; background-color: {"#22C55E" if q_count >= goal else "#0B2F9F"}; height: 100%; border-radius: 6px; transition: width 0.5s ease;'></div>
            </div>
            {"<div style='color:#22C55E; font-size:13px; font-weight:700;'>✅ Topic Complete! Data visible across all portals.</div>" if q_count >= goal else f"<div style='color:#666; font-size:13px;'>Add {goal - q_count} more to unlock for students.</div>"}
        </div>
        """, unsafe_allow_html=True)
        
        # PRUING TOOL (Requested by user: Need only exactly 25 questions)
        if q_count > 25:
            st.warning(f"⚠️ **Attention:** This topic has {q_count} questions (Limit is 25).")
            if st.button("🎯 Prune to Best 25 (Remove Excess)", key="prune_topic_btn"):
                # 1. Separate this topic from the rest
                other_qs = [q for q in st.session_state.db if not (q.get("subject") == sel_subj and (sel_subcat.lower() in q.get("subcategory", "").lower() or q.get("subcategory", "").lower() in sel_subcat.lower()))]
                
                # 2. Keep only the last 25 (most recent)
                keep_qs = db_qs[-25:] 
                
                # 3. Rebuild DB
                st.session_state.db = other_qs + keep_qs
                save_db(st.session_state.db, DB_FILE)
                
                # 4. Re-sync Physical Vault
                with st.spinner("📦 Updating Vault Folders..."):
                    # For Vault, we overwrite the folder archive for this topic
                    sync_to_physical_vault(keep_qs) 
                
                st.success("Successfully pruned topic to exactly 25 questions.")
                time.sleep(1); st.rerun()

        # Helper to fix stranded questions
        stranded = [q for q in st.session_state.db if q.get("subject") == sel_subj and q.get("subcategory") != sel_subcat and (sel_subcat.lower() in q.get("subcategory", "").lower() or q.get("subcategory", "").lower() in sel_subcat.lower())]
        if stranded:
            if st.button(f"🌀 Auto-fix {len(stranded)} naming mismatches for this Topic"):
                for q in stranded: q["subcategory"] = sel_subcat
                save_db(st.session_state.db, DB_FILE)
                st.success("Synchronized categories!")
                time.sleep(1); st.rerun()

        pasted_content = st.text_area(
            "Paste Generated Content from Notebook LLM", 
            height=200, 
            placeholder="Paste the raw text content generated from Notebook LLM here..."
        )

        has_key = bool(st.session_state.settings.get("gemini_api_key"))
        
        col_g1, col_g2 = st.columns(2)
        
        if col_g1.button("🎯 AI Generate", use_container_width=True, type="primary"):
            if not has_key:
                st.info("💡 **Key Needed**: Please set your Gemini Key in the 'Settings' tab to use AI Generation.")
            elif not pasted_content:
                st.error("Error: Content box is empty. Please paste Notebook LLM content.")
            else:
                
                saved_key = st.session_state.settings.get("gemini_api_key", "")
                with st.spinner("🎯 AI is analyzing and generating questions..."):
                    result = generate_from_text_content(
                        pasted_content, sel_subj, sel_subcat, num_questions=25, dynamic_api_key=saved_key
                    )
                    
                    if "success" in result:
                        batch = []
                        for idx, q in enumerate(result["questions"]):
                            q["id_temp"] = time.time() + idx
                            q["status"] = "PENDING"
                            batch.append(q)
                        st.session_state.v3_batch = batch
                        st.session_state.v3_source_url = notebook_url
                        st.success(f"AI generated {len(batch)} questions!")
                    else:
                        st.error(f"Generation Failed: {result['error']}")

        if col_g2.button("⚡ Quick Extract (Local)", use_container_width=True):
            if not pasted_content:
                st.error("Error: Please paste content first.")
            else:
                
                with st.spinner("⚡ Parsing pasted text locally..."):
                    result = local_smart_extract(pasted_content, sel_subj, sel_subcat)
                    if "success" in result and result.get("questions"):
                        batch = []
                        for idx, q in enumerate(result["questions"]):
                            q["id_temp"] = time.time() + idx
                            q["status"] = "PENDING"
                            batch.append(q)
                        st.session_state.v3_batch = batch
                        st.success(f"Successfully extracted {len(batch)} questions from text!")
                    else:
                        st.error("No questions found. Ensure you paste the full NotebookLLM output with 'Question Text:' and 'Correct Answer:' labels.")

        # --- ADMIN REVIEW MODE ---
        if "v3_batch" not in st.session_state:
            st.session_state.v3_batch = []

        st.markdown("---")
        st.markdown("### 📝 Review Mode & Question Management")
        
        col_b1, col_b2, col_b3 = st.columns([2, 1, 1])
        if col_b2.button("➕ Add Manual Question"):
            st.session_state.v3_batch.insert(0, {
                "id_temp": time.time(),
                "question": "New Concept Question",
                "options": {"a": "", "b": "", "c": "", "d": ""},
                "correct_answer": "a",
                "explanation": "",
                "type": "Theory-based MCQ",
                "subject": sel_subj,
                "subcategory": sel_subcat,
                "status": "APPROVED"
            })
            st.rerun()

        if col_b3.button("🗑️ Clear Review List", type="secondary"):
            st.session_state.v3_batch = []
            st.rerun()

        col_b1, col_b2, col_b3 = st.columns([1.5, 0.5, 0.5])
        
        with col_b1:
            pub_to_student = st.checkbox("🚀 Live Sync to Student Exam Portal", value=True, help="If checked, items will be marked 'Published' and visible on the student home page.")
        
        if col_b1.button("🚀 Approve & Save Everything to Admin Bank", use_container_width=True, type="primary"):
            # publish everything NOT rejected. 
            to_save = [q for q in st.session_state.v3_batch if q.get("status", "PENDING") != "REJECTED"]
            if not to_save:
                st.warning("No questions in the review list to publish.")
            else:
                for q in to_save:
                    q.pop("id_temp", None); q.pop("status", None)
                    q["subject"] = sel_subj
                    q["subcategory"] = sel_subcat
                    q["is_published"] = pub_to_student
                
                # EXACT Match Policy: Ensure we only touch the specific topic selected
                # 1. Get all other questions (everything NOT in this specific subject/topic)
                other_qs = [q for q in st.session_state.db if not (q.get("subject") == sel_subj and q.get("subcategory") == sel_subcat)]
                
                # 2. Get current topic questions (Exact match only)
                current_topic_qs = [q for q in st.session_state.db if q.get("subject") == sel_subj and q.get("subcategory") == sel_subcat]
                
                # 3. Combine: Existing first, then New ones at the end (Preserve Publication Order)
                combined = current_topic_qs + to_save
                
                # 4. Final Pruning: Keep only the LAST 25 (most recent verified content)
                final_topic_qs = combined[-25:]
                
                # 5. Update Master DB
                st.session_state.db = other_qs + final_topic_qs
                save_db(st.session_state.db, DB_FILE)
                
                # PHYSICAL FOLDER SYNC (Strict 1-25 Order)
                with st.spinner("📦 Syncing exactly 25 questions in order..."):
                    sync_to_physical_vault(final_topic_qs)
                
                st.success(f"✅ **Success!** Questions added to Admin Dashboard for '{sel_subcat}'.")
                if pub_to_student:
                    st.info("🟢 **Student Portal Updated:** These questions are now live in the student quiz pool.")
                else:
                    st.warning("🟡 **Draft Mode:** Questions saved to Admin Repository but hidden from students.")
                    
                st.session_state.v3_batch = []
                st.balloons()
                time.sleep(1.5); st.rerun()

        # Individual Question Cards
        if st.session_state.v3_batch:
            for idx, q in enumerate(st.session_state.v3_batch):
                q_id = q["id_temp"]
                
                q_status = q.get("status", "PENDING")
                status_color = "#F97316" # Orange for PENDING or missing
                if q_status == "APPROVED": status_color = "#22C55E"
                if q_status == "REJECTED": status_color = "#EF4444"
                
                with st.container():
                    img_src = get_base64_image(q.get("imageUrl"))
                    # 1. FIXED HTML PREVIEW (ZERO INDENTATION TO PREVENT CODE BLOCK RENDERING)
                    st.markdown(f"""
<div style='background-color:#FAF6EE; padding:25px; border-radius:12px; border-left:10px solid {status_color}; border-top:1px solid #ddd; border-right:1px solid #ddd; border-bottom:1px solid #ddd; font-family:"Inter", sans-serif; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom:20px;'>
<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;'>
<h2 style='color:#0B2F9F; margin:0;'>Question {idx+1}</h2>
<span style='background:{status_color}; color:white; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:700;'>{q_status}</span>
</div>
<p style='color:#0B2F9F; font-weight:700; margin-bottom:10px;'>[{q.get("subcategory", sel_subcat)} Advanced Check #{idx+1}]</p>
<p style='font-size:18px; font-weight:600; color:#1A1A2E; margin-bottom:20px;'>{q['question']}</p>
""" + (f'<img src="{img_src}" style="max-width:100%; border-radius:8px; margin-bottom:20px; border:2px solid #ddd;">' if img_src else "") + f"""
<div style='background: white; border: 2px solid #0B2F9F; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; font-weight: 600;'>
<span style='color:#0B2F9F; margin-right: 10px;'>A)</span> {q['options']['a']}
</div>
<div style='background: white; border: 2px solid #0B2F9F; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; font-weight: 600;'>
<span style='color:#0B2F9F; margin-right: 10px;'>B)</span> {q['options']['b']}
</div>
<div style='background: white; border: 2px solid #0B2F9F; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; font-weight: 600;'>
<span style='color:#0B2F9F; margin-right: 10px;'>C)</span> {q['options']['c']}
</div>
<div style='background: white; border: 2px solid #0B2F9F; border-radius: 8px; padding: 12px 14px; margin-bottom: 20px; font-weight: 600;'>
<span style='color:#0B2F9F; margin-right: 10px;'>D)</span> {q['options']['d']}
</div>
<div style='background:#E8F5E9; padding:15px; border-radius:8px; border-left:4px solid #2E7D32; font-size:14px; color: #1B5E20;'>
<div style='margin-bottom:8px;'><b>✅ Correct Answer:</b> {q['correct_answer'].upper()} | <b>Level:</b> {q.get('type', 'Theory')}</div>
<b>📖 Explanation:</b> {q['explanation']}
</div>
</div>
""", unsafe_allow_html=True)
                    
                    # 2. INTEGRATED EDIT FIELDS (Always Visible)
                    with st.expander("✏️ Edit Question Content", expanded=True):
                        new_txt = st.text_area("Question Text", value=q["question"], key=f"v3_txt_{q_id}", height=100)
                        
                        e_o1, e_o2 = st.columns(2)
                        oa = e_o1.text_input("Option A", value=q["options"]["a"], key=f"v3_oa_{q_id}")
                        ob = e_o2.text_input("Option B", value=q["options"]["b"], key=f"v3_ob_{q_id}")
                        oc = e_o1.text_input("Option C", value=q["options"]["c"], key=f"v3_oc_{q_id}")
                        od = e_o2.text_input("Option D", value=q["options"]["d"], key=f"v3_od_{q_id}")
                        
                        e_m1, e_m2, e_m3 = st.columns([1,1,2])
                        new_ans = e_m1.selectbox("Correct Ans", ["a", "b", "c", "d"], index=["a", "b", "c", "d"].index(q["correct_answer"]), key=f"v3_ans_{q_id}")
                        new_type = e_m2.selectbox("Question Type", ["Theory", "Numerical", "Assertion-Reason", "Match Following", "Diagram Based"], key=f"v3_type_{q_id}")
                        
                        # AI Review Image Upload
                        v3_img_val = q.get("imageUrl", "")
                        v3_up = e_m3.file_uploader("Upload Diagram", type=["jpg","jpeg","png"], key=f"v3_up_{q_id}")
                        if v3_up:
                            sp = os.path.join("assets", "question_images", v3_up.name)
                            if not os.path.exists(os.path.dirname(sp)): os.makedirs(os.path.dirname(sp))
                            with open(sp, "wb") as f: f.write(v3_up.getbuffer())
                            # Force update state immediately
                            st.session_state[f"v3_img_{q_id}"] = sp
                            v3_img_val = sp
                            st.toast(f"✅ Image {v3_up.name} Uploaded", icon="🖼️")
                            
                        new_img = e_m1.text_input("Final Image Path/URL", value=v3_img_val, key=f"v3_img_{q_id}")
                        if q.get('type') == 'Diagram Based' and not new_img:
                            st.error("⚠️ CRITICAL: Diagram Based question lacks an image. Please upload one.")
                        new_exp = e_m3.text_area("Detailed Explanation", value=q["explanation"], key=f"v3_exp_{q_id}", height=100)
                        
                        # Sync state live
                        st.session_state.v3_batch[idx]["question"] = new_txt
                        st.session_state.v3_batch[idx]["options"] = {"a": oa, "b": ob, "c": oc, "d": od}
                        st.session_state.v3_batch[idx]["correct_answer"] = new_ans
                        st.session_state.v3_batch[idx]["explanation"] = new_exp
                        st.session_state.v3_batch[idx]["type"] = new_type
                        st.session_state.v3_batch[idx]["imageUrl"] = new_img

                    # 3. ACTION BUTTONS (Quiz Styled)
                    c_ctrl1, c_ctrl2, c_ctrl3 = st.columns(3)
                    if c_ctrl1.button("✅ Save & Accept", key=f"acc_{q_id}", use_container_width=True):
                        st.session_state.v3_batch[idx]["status"] = "APPROVED"; st.rerun()
                    if c_ctrl2.button("❌ Reject / Clear", key=f"rej_{q_id}", use_container_width=True):
                        st.session_state.v3_batch[idx]["status"] = "REJECTED"; st.rerun()
                    if c_ctrl3.button("🗑️ Delete Question", key=f"del_{q_id}", use_container_width=True):
                        st.session_state.v3_batch.pop(idx); st.rerun()
                    
                    st.markdown("<br><hr style='border:1px solid #eee;'><br>", unsafe_allow_html=True)
        else:
            st.info("No questions in review list. Click 'Generate' or 'Add Manual' above to start.")

        # RECENTLY PUBLISHED LOG (Verified Master Records)
        if db_qs:
            with st.expander("🕒 Recently Published questions in this Topic", expanded=False):
                st.caption(f"Showing last 10 records for: {sel_subj} -> {sel_subcat}")
                recent_10 = db_qs[-10:][::-1]
                for rq in recent_10:
                    badge = "🖼️ [IMAGE AVAILABLE]" if rq.get("imageUrl") else "📄 [TEXT ONLY]"
                    st.markdown(f"**{badge}** {rq['question'][:80]}...")
                    if rq.get('imageUrl'):
                        isrc = get_base64_image(rq['imageUrl'])
                        if isrc: st.image(isrc, width=150)
                    st.caption(f"🎯 Destination: {rq.get('subcategory')} | Ans: {rq['correct_answer'].upper()} | Date: {rq.get('timestamp', 'Recently')}")
                    st.divider()

    with t2:
        col_t2_h, col_t2_ref = st.columns([3, 1])
        with col_t2_h: st.subheader("✏️ Edit Question Bank")
        if col_t2_ref.button("🔄 Force Refresh Database", key="ref_db_admin"):
            st.session_state.db = load_db(DB_FILE)
            st.success("Synchronized with disk!")
            time.sleep(0.5); st.rerun()
            
        s_idx_t2 = SUBJECTS.index(st.session_state.admin_subj) if st.session_state.admin_subj in SUBJECTS else 0
        edit_subj = st.selectbox("Select Subject to Manage", SUBJECTS, index=s_idx_t2, key="admin_subj_t2", label_visibility="collapsed")
        st.session_state.admin_subj = edit_subj
        
        if edit_subj:
            # Flexible filtering for subcategories
            subj_qs = [q for q in st.session_state.db if q.get("subject") == edit_subj]
            
            if not subj_qs:
                st.warning("No questions found for this subject.")
            else:
                # Use synced subcat key if possible, but for the editor we might want to see the RAW DB names
                # Actually, let's stick to the synced subcat for consistency
                db_subcats = sorted(list(set([q.get('subcategory', 'General') for q in subj_qs])))
                
                # Help the user find the right subcategory - using a unique key here to avoid conflict with syllabus-synced subcat 
                # because DB categories (e.g. "Bricks, Stones & Cement") might not exist in the syllabus-synced list.
                edit_subcat = st.selectbox("DB Subcategory found", ["-- All --"] + db_subcats, key="editor_db_subcat_search")
                
                # Get questions for this subject+subcategory
                filtered_qs = []
                filtered_indices = []
                for idx_db, q in enumerate(st.session_state.db):
                    if q.get("subject") == edit_subj:
                        q_sc = q.get("subcategory", "")
                        sc_match = (edit_subcat == "-- All --" or q_sc == edit_subcat)
                        if sc_match:
                            filtered_qs.append(q)
                            filtered_indices.append(idx_db)

                if len(filtered_qs) > 0:
                    st.write(f"**{len(filtered_qs)} Questions in this Subcategory** *(same as Quiz)*")
                    
                    col_num, col_prev = st.columns([1, 3])
                    user_q_num = col_num.number_input(
                        "Enter Question Number:", 
                        min_value=1, max_value=len(filtered_qs), value=1, step=1, key="edit_q_num"
                    )
                    edit_q_idx_rel = int(user_q_num) - 1
                    
                    # Preview and Edit form both use the same index — guaranteed sync
                    real_idx = filtered_indices[edit_q_idx_rel]
                    selected_q = st.session_state.db[real_idx]
                    
                    col_prev.info(f"**Preview Q{int(user_q_num)}:** {str(selected_q.get('question', ''))[:150]}...")
                    
                    st.markdown("---")
                    st.markdown("### Editing Selected Question")
                    
                    # ⚠️ KEY includes real_idx so widgets RESET when question changes
                    k = real_idx  # unique key per question
                    
                    # Show full question + options preview BEFORE the edit form
                    q_opts = selected_q.get('options', {})
                    img_src = get_base64_image(selected_q.get("imageUrl"))
                    
                    # ZERO INDENTATION for the HTML string to prevent markdown code-block rendering
                    preview_html = f"""
<div style='background:#EEF4FF; border-radius:10px; padding:20px; margin-bottom:20px; border-left:8px solid #1B3F72; border-right:1px solid #ddd; border-top:1px solid #ddd; border-bottom:1px solid #ddd;'>
<b style='color:#1B3F72; font-size:16px;'>📋 Card Preview (Database Format)</b><br/><br/>
<div style='font-size:18px; margin-bottom:15px;'>{html.escape(str(selected_q.get('question','')))}</div>
{(f'<img src="{img_src}" style="max-width:100%; height:auto; border-radius:8px; margin-bottom:15px; border:1px solid #ccc;"><br/>' if img_src else "")}
<div style='margin-bottom:8px;'><span style='color:#22C55E; font-weight:700;'>A)</span> {html.escape(str(q_opts.get('a','—')))}</div>
<div style='margin-bottom:8px;'><span style='color:#22C55E; font-weight:700;'>B)</span> {html.escape(str(q_opts.get('b','—')))}</div>
<div style='margin-bottom:8px;'><span style='color:#22C55E; font-weight:700;'>C)</span> {html.escape(str(q_opts.get('c','—')))}</div>
<div style='margin-bottom:15px;'><span style='color:#22C55E; font-weight:700;'>D)</span> {html.escape(str(q_opts.get('d','—')))}</div>
<div style='background:white; padding:10px; border-radius:5px; border:1px dashed #1B3F72;'>
✅ <b>Correct Answer:</b> <span style='color:#1B3F72; font-weight:700;'>{str(selected_q.get('correct_answer','')).upper()}</span>
</div>
</div>
"""
                    st.markdown(preview_html, unsafe_allow_html=True)
                    
                    new_q_text = st.text_area("Question Text", value=selected_q.get('question', ''), key=f"eq_text_{k}")
                    new_subcat = st.text_input("Subcategory", value=selected_q.get('subcategory', ''), key=f"eq_subcat_{k}")
                    
                    col_t, col_i = st.columns(2)
                    q_types_available = [
                        "Theory-based MCQ", "Numerical/Problem-based", "Assertion-Reason", 
                        "Match the Following", "Statement type (True/False)", "Diagram-based", "objective"
                    ]
                    curr_type = selected_q.get('type', 'objective')
                    if curr_type not in q_types_available:
                        q_types_available.append(curr_type)
                        
                    new_type = col_t.selectbox("Question Type", q_types_available, index=q_types_available.index(curr_type), key=f"eq_type_{k}")
                    
                    # Image Edit/Upload (Always Available)
                    col_img1, col_img2 = st.columns(2)
                    temp_img_url = selected_q.get('imageUrl', '')
                    
                    up_file = col_img1.file_uploader("Upload New Image", type=["jpg", "jpeg", "png"], key=f"up_{k}")
                    if up_file:
                        save_path = os.path.join("assets", "question_images", up_file.name)
                        if not os.path.exists(os.path.dirname(save_path)): os.makedirs(os.path.dirname(save_path))
                        with open(save_path, "wb") as f:
                            f.write(up_file.getbuffer())
                        temp_img_url = save_path
                        # Force update session state
                        st.session_state[f"eq_img_{k}"] = temp_img_url
                    
                    new_img_url = col_img2.text_input("Raw Image Path/URL", value=temp_img_url, key=f"eq_img_{k}")
                    
                    if new_img_url:
                        test_src = get_base64_image(new_img_url)
                        if test_src:
                            st.markdown("#### 🖼️ Image Live Sync Preview")
                            st.image(test_src, width=350, caption="Form Preview (Ready to Update)")
                        else:
                            st.error(f"⚠️ Diagram path invalid or file missing: {new_img_url}")
                    
                    c1_e, c2_e = st.columns(2)
                    opts = selected_q.get('options', {})
                    eo_a = c1_e.text_input("Option A", value=opts.get('a', ''), key=f"eo_a_{k}")
                    eo_b = c2_e.text_input("Option B", value=opts.get('b', ''), key=f"eo_b_{k}")
                    eo_c = c1_e.text_input("Option C", value=opts.get('c', ''), key=f"eo_c_{k}")
                    eo_d = c2_e.text_input("Option D", value=opts.get('d', ''), key=f"eo_d_{k}")
                    
                    ans_list = ["a", "b", "c", "d"]
                    curr_ans = selected_q.get('correct_answer', 'a')
                    if curr_ans not in ans_list: curr_ans = "a"
                        
                    new_corr = st.selectbox("Correct Option", ans_list, index=ans_list.index(curr_ans), key=f"eq_corr_{k}")
                    
                    col_u, col_d = st.columns(2)
                    if col_u.button("💾 Update Question"):
                        st.session_state.db[real_idx]['question'] = new_q_text
                        st.session_state.db[real_idx]['subcategory'] = new_subcat
                        st.session_state.db[real_idx]['type'] = new_type
                        # ALWAYS UPDATING IMAGE PATH (Allowing clearing by empty string)
                        st.session_state.db[real_idx]['imageUrl'] = new_img_url
                        st.session_state.db[real_idx]['options'] = {'a': eo_a, 'b': eo_b, 'c': eo_c, 'd': eo_d}
                        st.session_state.db[real_idx]['correct_answer'] = new_corr
                        save_db(st.session_state.db, DB_FILE)
                        st.success("✅ Question updated successfully!")
                        
                    if col_d.button("🗑️ Delete Question"):
                        st.session_state.db.pop(real_idx)
                        save_db(st.session_state.db, DB_FILE)
                        st.success("Question deleted!")
                        time.sleep(1)
                        st.rerun()

    with t3:
        st.subheader("📊 Student Quiz Statistics")
        results = load_db(RESULTS_FILE)
        if not isinstance(results, list): results = []
        
        if not results:
            st.info("No student results yet. Results appear here after students complete quizzes.")
        else:
            import pandas as pd
            df = pd.DataFrame(results)
            
            # Summary metrics
            total_attempts = len(df)
            unique_students = df['student_name'].nunique()
            avg_accuracy = df['accuracy'].mean()
            
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Total Quiz Attempts", total_attempts)
            mc2.metric("Unique Students", unique_students)
            mc3.metric("Avg Accuracy", f"{avg_accuracy:.1f}%")
            st.markdown("---")

            # --- Row 1: Heatmap ---
            st.subheader("🌐 Global Performance Heatmap")
            st.write("Average accuracy distribution across all subjects and topics.")
            # Prepare data for heatmap: average accuracy per (Subject, Subcategory)
            h_df = df.groupby(['subject', 'subcategory'])['accuracy'].mean().reset_index()
            # Pivot for imshow if preferred, or use density_heatmap
            import plotly.express as px
            fig_h = px.density_heatmap(h_df, x="subcategory", y="subject", z="accuracy", 
                                      color_continuous_scale=[[0, '#0B2F9F'], [1, '#F97316']], 
                                      labels={'accuracy': 'Avg Accuracy %'},
                                      height=450)
            fig_h.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_h, use_container_width=True)

            # --- Row 2: Engagement Trends ---
            st.subheader("📈 Quiz Engagement Trends")
            df['date_dt'] = pd.to_datetime(df['date'])
            engagement_df = df.groupby('date').size().reset_index(name='attempts')
            fig_e = px.line(engagement_df, x='date', y='attempts', markers=True,
                            title="Daily Quiz Attempt Frequency",
                            labels={'attempts': 'Number of Quizzes', 'date': 'Date'})
            fig_e.update_traces(line_color="#F97316", marker=dict(color="#0B2F9F", size=10))
            fig_e.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_e, use_container_width=True)

            st.markdown("---")
            
            # Filter by student
            students = ["All Students"] + sorted(df['student_name'].unique().tolist())
            sel_student = st.selectbox("Filter by Student", students, key="admin_student_filter")
            
            view_df = df if sel_student == "All Students" else df[df['student_name'] == sel_student]
            
            # Show table
            st.dataframe(
                view_df[['student_name','subject','subcategory','score','total','accuracy','rating','date','time']]
                .rename(columns={
                    'student_name': 'Student',
                    'subject': 'Subject',
                    'subcategory': 'Topic',
                    'score': 'Score',
                    'total': 'Total Q',
                    'accuracy': 'Accuracy %',
                    'rating': 'Rating',
                    'date': 'Date',
                    'time': 'Time'
                })
                .sort_values('Date', ascending=False)
                .reset_index(drop=True),
                use_container_width=True
            )
            
            st.markdown("---")
            st.subheader("🏆 Leaderboard (Top Students by Avg Accuracy)")
            leaderboard = df.groupby('student_name').agg(
                Attempts=('score','count'),
                Avg_Accuracy=('accuracy','mean'),
                Best_Score=('score','max')
            ).sort_values('Avg_Accuracy', ascending=False).round(1).reset_index()
            leaderboard.columns = ['Student','Attempts','Avg Accuracy %','Best Score']
            st.dataframe(leaderboard, use_container_width=True)
            
            if st.button("🗑️ Clear All Results", key="clear_results"):
                save_db([], RESULTS_FILE)
                st.success("All results cleared.")
                st.rerun()
    

    with t_student:
        st.subheader("🎓 Student Management")
        st.write("Create login credentials for students. Students can only log in using exactly matching details.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Single Student Creation**")
            new_s_name = st.text_input("Student Name")
            new_s_roll = st.text_input("Roll Number")
            new_s_email = st.text_input("Student Email")
            new_s_pwd = st.text_input("Assign Password")
            
            if st.button("➕ Create Single Student"):
                if new_s_name and new_s_roll and new_s_email and new_s_pwd:
                    students = load_db(STUDENTS_FILE)
                    if not isinstance(students, list): students = []
                    
                    if any(s.get("email") == new_s_email.strip() for s in students):
                        st.error("Email already exists in database!")
                    else:
                        students.append({
                            "name": new_s_name.strip(),
                            "roll_no": new_s_roll.strip(),
                            "email": new_s_email.strip(),
                            "password": new_s_pwd.strip()
                        })
                        save_db(students, STUDENTS_FILE)
                        st.success(f"Student {new_s_name} added successfully!")
                else:
                    st.error("Please fill all fields.")
        
        with c2:
            st.markdown("**Bulk Student Creation (CSV format)**")
            st.write("Format: `Name, RollNumber, Email, Password` (one per line)")
            bulk_data = st.text_area("Paste bulk student data here", height=200)
            
            if st.button("🚀 Process Bulk Registration"):
                if bulk_data.strip():
                    students = load_db(STUDENTS_FILE)
                    if not isinstance(students, list): students = []
                    
                    added_count = 0
                    errors = []
                    lines = bulk_data.strip().split('\\n')
                    for line in lines:
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) == 4:
                            n, r, e, p = parts
                            if not any(s.get("email") == e for s in students):
                                students.append({
                                    "name": n,
                                    "roll_no": r,
                                    "email": e,
                                    "password": p
                                })
                                added_count += 1
                            else:
                                errors.append(f"Email {e} already exists.")
                        elif line.strip():
                            errors.append(f"Invalid format: {line}")
                            
                    save_db(students, STUDENTS_FILE)
                    if added_count > 0: st.success(f"Successfully added {added_count} students!")
                    if errors:
                        for err in errors: st.warning(err)
                else:
                    st.error("Text area is empty.")
                    
        st.markdown("---")
        st.subheader("Registered Students Roster")
        students_list = load_db(STUDENTS_FILE)
        if not students_list:
            st.info("No students registered yet.")
        else:
            import pandas as pd
            sdf = pd.DataFrame(students_list)
            st.dataframe(sdf, use_container_width=True)
            
            del_email = st.selectbox("Select Student Email to Remove", sdf['email'].tolist())
            if st.button("🗑️ Delete Student"):
                students_list = [s for s in students_list if s.get("email") != del_email]
                save_db(students_list, STUDENTS_FILE)
                st.success("Student removed.")
                st.rerun()

    with t4:
        st.subheader("🏰 The Master Repository Vault")
        st.write("Browse your **Hard-Copy Archive** organized into separate sub-folders for every Subject and Topic.")
        
        vault_base = "MASTER_VAULT"
        
        col_v1, col_v2 = st.columns([1, 1])
        with col_v1:
            st.info(f"📍 **Vault Location:** `{os.path.abspath(vault_base)}`")
        with col_v2:
            if st.button("🔄 Full Vault Re-Sync (From Database)"):
                with st.spinner("Rebuilding physical folders..."):
                    sync_to_physical_vault(st.session_state.db)
                st.success("Physical folder structure updated!")
                time.sleep(1); st.rerun()

        st.divider()

        if not st.session_state.db:
            st.info("The Vault is currently locked. Publish questions to generate folders.")
        else:
            # Folder Explorer UI
            st.markdown("### �️ Folder Explorer")
            
            # Step 1: Subject Folder
            col_exp1, col_exp2 = st.columns([1, 2])
            
            with col_exp1:
                st.markdown("**1. Select Subject Folder**")
                sel_folder_subj = st.radio("Subjects", SUBJECTS, key="vault_subj_radio", label_visibility="collapsed")
            
            with col_exp2:
                # Official subtopics for this subject
                official_topics = SYLLABUS_ORDER.get(sel_folder_subj, [])
                
                # Filter DB questions for this subject
                subj_db_qs = [q for q in st.session_state.db if q.get("subject") == sel_folder_subj]
                
                st.markdown(f"**2. Select Topic Sub-Folder in '{sel_folder_subj}'**")
                
                # 1. SHOW OFFICIAL TOPICS FIRST (Strict alignment)
                for topic_folder in official_topics:
                    # Exact matching for folder view to ensure order visibility
                    t_qs = [q for q in subj_db_qs if q.get("subcategory") == topic_folder]
                    
                    status_icon = "📁" if len(t_qs) < 25 else "✅"
                    with st.expander(f"{status_icon} {topic_folder} ({len(t_qs)} Questions)", expanded=False):
                        if not t_qs:
                            st.info("No questions published for this subtopic yet.")
                            continue
                        
                        st.caption(f"Status: Official Syllabus Topic | Path: /{sel_folder_subj}/{topic_folder}/")
                        
                        # Dataframe view (Strict chronological order)
                        f_df = pd.DataFrame(t_qs)
                        f_df.index = range(1, len(f_df) + 1)
                        cols_to_show = ["question", "correct_answer", "type", "timestamp"]
                        existing_cols = [c for c in cols_to_show if c in f_df.columns]
                        
                        col_map = {"question": "Question Text", "correct_answer": "Ans", "type": "Type", "timestamp": "Archived Date"}
                        
                        show_edit = st.toggle(f"🛠️ Manage / Edit questions in {topic_folder}", key=f"toggle_{topic_folder}")
                        
                        show_table = st.toggle("📊 Switch to Table Overview (Compact)", value=False, key=f"tbl_{topic_folder}")
                        
                        if show_table:
                            st.dataframe(
                                f_df[existing_cols].rename(columns=col_map), 
                                use_container_width=True, 
                                height=500,
                                column_config={"Question Text": st.column_config.TextColumn("Question Text", width="large")}
                            )
                        elif not show_edit:
                            st.info(f"📚 {topic_folder} - Full Reading Mode")
                            for idx_repo, q_repo in enumerate(t_qs):
                                # 1. Escape symbols FIRST
                                disp_q = html.escape(q_repo['question'])
                                # 2. Then Format
                                if re.search(r'\s([1-4]{1}\.\s)', disp_q):
                                    disp_q = re.sub(r'\s([1-4]{1}\.\s)', r'<br/><br/><b>\1</b>', disp_q)
                                
                                with st.container(border=True):
                                    st.markdown(f"**Q{idx_repo+1}:** {disp_q}", unsafe_allow_html=True)
                                    if q_repo.get('imageUrl'):
                                        img_u = get_base64_image(q_repo['imageUrl'])
                                        if img_u: st.image(img_u, width=300)
                                    st.caption(f"🎯 Ans: {q_repo['correct_answer'].upper()} | Type: {q_repo.get('type')}")
                        else:
                            st.info("Management Mode: Use the buttons below to refine your folder content.")
                            for idx, q_data in enumerate(t_qs):
                                with st.container(border=True):
                                    st.markdown(f"**Q{idx+1}:** {q_data['question'][:150]}...")
                                    if q_data.get('imageUrl'):
                                        img_src = get_base64_image(q_data['imageUrl'])
                                        if img_src:
                                            st.image(img_src, width=max(100, 300))
                                        else:
                                            st.caption(f"⚠️ Diagram source not found: {q_data['imageUrl']}")
                                    st.caption(f"Correct Ans: {q_data['correct_answer'].upper()} | Type: {q_data.get('type')}")
                                    
                                    col_m1, col_m2 = st.columns([1, 5])
                                    if col_m1.button("🗑️ Delete", key=f"del_{topic_folder}_{idx}", type="secondary"):
                                        # Remove from master DB
                                        q_text_match = q_data['question']
                                        st.session_state.db = [q for q in st.session_state.db if not (q.get("question") == q_text_match and q.get("subcategory") == topic_folder)]
                                        save_db(st.session_state.db, DB_FILE)
                                        # RE-SYNC VAULT
                                        sync_to_physical_vault(st.session_state.db)
                                        st.success("Removed from Repository.")
                                        time.sleep(0.5); st.rerun()

                                    # Edit logic simplified for brevity - usually opens a modal or form
                                    with col_m2.expander("✏️ Quick Edit Content"):
                                        new_txt = st.text_area("Edit Question Text", value=q_data['question'], key=f"edt_txt_{topic_folder}_{idx}")
                                        new_ans = st.selectbox("Correct Ans", ["a", "b", "c", "d"], index=["a", "b", "c", "d"].index(q_data['correct_answer'].lower()), key=f"edt_ans_{topic_folder}_{idx}")
                                        
                                        # Image Edit
                                        curr_img = q_data.get('imageUrl', '')
                                        col_ui1, col_ui2 = st.columns(2)
                                        f_up = col_ui1.file_uploader("Replace Diagram", type=["jpg","jpeg","png"], key=f"fup_{topic_folder}_{idx}")
                                        if f_up:
                                            sp = os.path.join("assets", "question_images", f_up.name)
                                            if not os.path.exists(os.path.dirname(sp)): os.makedirs(os.path.dirname(sp))
                                            with open(sp, "wb") as f: f.write(f_up.getbuffer())
                                            curr_img = sp
                                            st.success("Uploaded!")
                                            
                                        new_img = col_ui2.text_input("Raw Image Path/URL", value=curr_img, key=f"edt_img_{topic_folder}_{idx}")
                                        if st.button("💾 Save Changes", key=f"sav_edt_{topic_folder}_{idx}"):
                                            # Update in DB
                                            for db_q in st.session_state.db:
                                                if db_q.get("question") == q_data['question'] and db_q.get("subcategory") == topic_folder:
                                                    db_q['question'] = new_txt
                                                    db_q['correct_answer'] = new_ans
                                                    db_q['imageUrl'] = new_img
                                            save_db(st.session_state.db, DB_FILE)
                                            sync_to_physical_vault(st.session_state.db)
                                            st.success("Updated!")
                                            time.sleep(0.5); st.rerun()
                        
                        st.divider()
                        if st.button(f"📥 Export {topic_folder} Backup", key=f"dl_{topic_folder}"):
                            json_str = json.dumps(t_qs, indent=4)
                            st.download_button(label=f"Download JSON", data=json_str, file_name=f"{topic_folder}.json", mime="application/json")

                # 2. SHOW EXTRA TOPICS (Any in DB but not in Official list)
                db_uncategorized_topics = sorted(list(set([
                    q.get("subcategory", "Uncategorized") for q in subj_db_qs 
                    if not any(off_t.lower() in q.get("subcategory", "").lower() or q.get("subcategory", "").lower() in off_t.lower() for off_t in official_topics)
                ])))
                
                if db_uncategorized_topics:
                    st.divider()
                    st.markdown("**📂 Extra / Legacy topics in Database (Non-Syllabus)**")
                    for extra_topic in db_uncategorized_topics:
                        e_qs = [q for q in subj_db_qs if q.get("subcategory") == extra_topic]
                        with st.expander(f"🩹 {extra_topic} ({len(e_qs)} Found in DB)", expanded=False):
                            st.dataframe(pd.DataFrame(e_qs)[["question", "correct_answer"]], use_container_width=True)
                            if st.button(f"🗑️ Delete All {len(e_qs)} Extra questions", key=f"del_extra_{extra_topic}"):
                                st.session_state.db = [q for q in st.session_state.db if not (q.get("subject") == sel_folder_subj and q.get("subcategory") == extra_topic)]
                                save_db(st.session_state.db, DB_FILE)
                                st.success("Cleared extra topic.")
                                time.sleep(0.5); st.rerun()

            st.markdown("---")
            with st.expander("🚨 Safety & Cleanup"):
                st.warning("Manual deletion of the `./MASTER_VAULT/` directory will not delete questions from the app, but you will lose the hard-copy backup.")
                if st.button("🚨 WIPE ALL DATA (DB + VAULT)"):
                    st.session_state.db = []
                    save_db([], DB_FILE)
                    if os.path.exists(vault_base): 
                        import shutil
                        shutil.rmtree(vault_base)
                    st.success("System wiped completely.")
                    st.rerun()

    with t5:
        st.subheader("⚙️ Global Admin Settings")
        
        c_s1, c_s2 = st.columns(2)
        with c_s1:
            st.markdown("### 🕒 Assessment Control")
            current_timer = st.session_state.settings.get("quiz_duration_minutes", 22.5)
            new_timer = st.number_input("Global Quiz Duration (Minutes)", min_value=1.0, value=float(current_timer), step=0.5)
            if st.button("Update Timer Settings"):
                st.session_state.settings["quiz_duration_minutes"] = new_timer
                save_db(st.session_state.settings, SETTINGS_FILE)
                st.success("Timer updated!")

        with c_s2:
            st.markdown("### 🔑 API Configuration")
            existing_key = st.session_state.settings.get("gemini_api_key", "")
            new_key = st.text_input("Master Gemini API Key", value=existing_key, type="password")
            if st.button("Update AI Key"):
                st.session_state.settings["gemini_api_key"] = new_key
                save_db(st.session_state.settings, SETTINGS_FILE)
                st.success("API Key updated!")
                
        st.markdown("---")
        st.subheader("🧹 Database Maintenance (System Repair)")
        st.write("If you can't see questions in the dashboard due to naming differences (e.g., 'Brick' vs 'Bricks'), use this tool.")
        
        if st.button("🔧 Standardize & Scrub Entire Database (Force 25 per Topic)"):
            migrated_count = 0
            pruned_total = 0
            
            # Syllabus flat list for matching
            all_syllabus_scs = []
            for sub_list in SYLLABUS_ORDER.values():
                all_syllabus_scs.extend(sub_list)
            
            # Phase 1: Standardize names
            for q in st.session_state.db:
                curr_sc = q.get("subcategory", "")
                for target_sc in all_syllabus_scs:
                    if target_sc.lower() in curr_sc.lower() or curr_sc.lower() in target_sc.lower():
                        if curr_sc != target_sc:
                            q["subcategory"] = target_sc
                            migrated_count += 1
                        break
            
            # Phase 2: Prune every single topic cluster to exactly 25
            refined_db = []
            # Group by Subject + Subcategory
            groups = {}
            for q in st.session_state.db:
                key = (q.get("subject"), q.get("subcategory"))
                if key not in groups: groups[key] = []
                groups[key].append(q)
            
            for key, qs in groups.items():
                if len(qs) > 25:
                    pruned_total += (len(qs) - 25)
                    refined_db.extend(qs[-25:]) # Keep last 25
                else:
                    refined_db.extend(qs)
            
            st.session_state.db = refined_db
            save_db(st.session_state.db, DB_FILE)
            
            # Sync Vault to reflect pruned state
            sync_to_physical_vault(st.session_state.db)
            
            st.success(f"Successfully migrated {migrated_count} items and pruned {pruned_total} excess questions!")
            st.info("All topics now have a hard-cap of 25 questions.")
            time.sleep(2); st.rerun()

def screen_analytics():
    st.title("📈 My Performance Analytics")
    user = st.session_state.get("login_user", "")
    st.write(f"Welcome to your personal dashboard, **{user}**.")
    
    results = load_db(RESULTS_FILE)
    if not isinstance(results, list): results = []
    
    # Filter for current user
    user_results = [r for r in results if r.get("student_name") == user]
    
    if not user_results:
        st.info("You haven't completed any quizzes yet. Start learning to see your analytics!")
        if st.button("⬅ Back to Home"): navigate("HOME")
        return
        
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    
    df = pd.DataFrame(user_results)
    
    # 0. Data Parsing for Charts
    def parse_time(t_str):
        try:
            parts = str(t_str).split('m')
            m = int(parts[0])
            s = int(parts[1].split('s')[0])
            return m * 60 + s
        except: return 0
    
    df['seconds'] = df['time_taken'].apply(parse_time)
    
    # 1. Top level metrics
    total_quizzes = len(df)
    avg_score = df['accuracy'].mean()
    best_score = df['accuracy'].max()
    
    # Calculate global syllabus completion (count unique cleared modules across all subjects)
    total_syllabus_modules = sum(len(v) for v in SYLLABUS_ORDER.values())
    
    # We need the max accuracy per module for gauge
    user_max_per_module = df.groupby(['subject', 'subcategory'])['accuracy'].max().reset_index()
    cleared_count = len(user_max_per_module[user_max_per_module['accuracy'] >= 90])
    syllabus_pct = (cleared_count / total_syllabus_modules * 100) if total_syllabus_modules > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Quizzes Done", total_quizzes)
    m2.metric("Avg Accuracy", f"{avg_score:.1f}%")
    m3.metric("Best Score", f"{best_score:.1f}%")
    m4.metric("Modules Cleared", f"{cleared_count}/{total_syllabus_modules}")
    
    st.markdown("---")
    
    # --- Advanced Row 1: Gauge & Subject Bar ---
    row1_c1, row1_c2 = st.columns([1, 1])
    with row1_c1:
        st.subheader("Syllabus Mastery")
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = syllabus_pct,
            title = {'text': "Total Syllabus Completion (%)", 'font': {'color': '#0B2F9F', 'size': 18}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#0B2F9F"},
                'bar': {'color': "#F97316"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "#0B2F9F",
                'steps': [
                    {'range': [0, 50], 'color': '#FFE0B2'},
                    {'range': [50, 90], 'color': '#BBDEFB'},
                    {'range': [90, 100], 'color': '#C8E6C9'}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90}}))
        fig_gauge.update_layout(height=280, margin=dict(l=30, r=30, t=50, b=20),
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_gauge, use_container_width=True)
        
    with row1_c2:
        st.subheader("Subject-wise Performance")
        subj_acc = df.groupby('subject')['accuracy'].mean().reset_index()
        fig1 = px.bar(subj_acc, x='subject', y='accuracy', 
                      color='accuracy', color_continuous_scale=[[0, '#0B2F9F'], [1, '#F97316']],
                      height=280)
        fig1.update_layout(margin=dict(l=10, r=10, t=30, b=10),
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          xaxis_title=None, yaxis_title="Accuracy (%)")
        st.plotly_chart(fig1, use_container_width=True)
        
    # --- Row 2: Trend & Matrix ---
    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        st.subheader("Improvement Trend")
        trend_df = df.copy()
        trend_df['attempt'] = range(1, len(trend_df) + 1)
        fig_trend = px.line(trend_df, x='attempt', y='accuracy', markers=True, 
                            labels={'attempt': 'Quiz #', 'accuracy': 'Score (%)'})
        fig_trend.update_traces(line_color="#0B2F9F", marker=dict(color="#F97316", size=8))
        fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with row2_c2:
        st.subheader("Speed vs. Quality Matrix")
        fig_scatter = px.scatter(df, x='seconds', y='accuracy', 
                                 size='total', color='accuracy',
                                 color_continuous_scale=[[0, '#0B2F9F'], [1, '#F97316']],
                                 hover_data=['subcategory', 'date'],
                                 labels={'seconds': 'Time (s)', 'accuracy': 'Accuracy (%)'})
        fig_scatter.add_vline(x=df['seconds'].mean(), line_dash="dash", line_color="#0B2F9F", annotation_text="Avg Time")
        fig_scatter.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    st.markdown("---")
    st.subheader("Subtopic Mastery (Weakest to Strongest)")
    
    topic_acc = df.groupby('subcategory').agg(
        Attempts=('accuracy', 'count'),
        Best_Score=('accuracy', 'max'),
        Avg_Score=('accuracy', 'mean')
    ).reset_index().sort_values('Avg_Score', ascending=True)
    
    st.dataframe(
        topic_acc.style.background_gradient(cmap='RdYlGn', subset=['Avg_Score', 'Best_Score']),
        use_container_width=True
    )
    
    st.markdown("---")
    st.subheader("🕒 Full Attempt History")
    st.dataframe(df[['date', 'time', 'subject', 'subcategory', 'score', 'total', 'accuracy', 'rating']].sort_values('date', ascending=False).reset_index(drop=True), use_container_width=True)

def screen_settings():
    st.title("⚙️ Settings & C³ Institute Profile")
    
    # --- GLOBAL AI CONFIGURATION ---
    st.subheader("🤖 Global AI Configuration")
    existing_key = st.session_state.settings.get("gemini_api_key", "")
    new_key = st.text_input("Gemini API Key (for Question Generation)", value=existing_key, type="password", help="Enter your Google AI Studio API key here. It will be saved permanently.")
    
    if st.button("💾 Save Settings"):
        st.session_state.settings["gemini_api_key"] = new_key
        save_db(st.session_state.settings, SETTINGS_FILE)
        st.success("Settings saved successfully!")
        time.sleep(1)
        st.rerun()

    st.markdown("---")
    st.write("**About C³ Institute App**")
    st.write("Version 2.0.0 - Full TNPSC AE Civil Syllabus loaded.")
    if st.button("Logout"): navigate("HOME")

# --- Routing ---
scr = st.session_state.current_screen
role = st.session_state.login_role

# Force login if not authenticated
if not role and scr != "LOGIN":
    screen_login()
elif scr == "LOGIN":
    screen_login()
elif scr == "HOME":
    screen_home()
elif scr == "SUBJECT_DETAIL":
    screen_subject_detail()
elif scr == "QUIZ":
    screen_quiz()
elif scr == "SUMMARY":
    screen_summary()
elif scr == "REVIEW":
    screen_review()
elif scr == "ADMIN":
    if role == "admin":
        screen_admin()
    else:
        st.error("🔒 Admin access only. Please login as Admin.")
elif scr == "ANALYTICS":
    screen_analytics()
elif scr == "SETTINGS":
    screen_settings()
