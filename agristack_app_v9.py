import streamlit as st
import hashlib
import pandas as pd
import numpy as np
import time
import re
from difflib import SequenceMatcher
import random
import base64
from pathlib import Path
import math
import pydeck as pdk
from datetime import datetime, timedelta

# ------------------------------
# MODULE 0: CONFIGURATION
# ------------------------------

# Set wide layout for VDV split-screen workbench
st.set_page_config(
    page_title="AgriStack J&K: Policy Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------
# UI THEME (CUSTOM)
# ------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;600;700&family=Space+Grotesk:wght@400;600&display=swap');
:root{
  --ink:#0b1b2b;
  --slate:#2b3a4a;
  --gold:#c08b2c;
  --teal:#0e6d5b;
  --sand:#f4efe6;
  --fog:#eef2f6;
  --accent:#b52a2a;
  --pine:#1d5c4a;
  --walnut:#6a4b2a;
  --saffron:#e6b04a;
}
body{
  background: #FDF7F8;
}
.stApp, .main, [data-testid="stAppViewContainer"]{
  background: transparent !important;
}
body, p, span, label, .stMarkdown, .stText, .stCaption, .stTextInput, .stSelectbox, .stRadio, .stCheckbox, .stNumberInput, .stTextArea{
  color: #333333 !important;
}
.stApp{
  background: transparent;
}
html, body, [class*="css"]  {font-family: "Space Grotesk", sans-serif;}
.app-hero{
  background: linear-gradient(135deg, #fbf5ea 0%, #f2f6f1 60%, #e7efe9 100%);
  border: 1px solid #e2e5ea;
  padding: 18px 22px;
  border-radius: 16px;
}
.hero-title{
  font-family: "Spectral", serif;
  font-size: 32px;
  font-weight: 700;
  color: var(--ink);
  margin: 0;
}
.hero-sub{
  font-family: "Spectral", serif;
  font-size: 18px;
  color: var(--slate);
  margin-top: 4px;
}
.badge-row{
  margin-top: 10px;
}
.badge{
  display: inline-block;
  background: #fff;
  border: 1px solid #e6e6e6;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  margin-right: 6px;
}
.section-title{
  font-family: "Spectral", serif;
  font-size: 22px;
  color: var(--ink);
  margin-bottom: 4px;
}
.callout{
  background: #fff;
  border-left: 4px solid var(--gold);
  padding: 10px 14px;
  border-radius: 8px;
}
.card{
  background: #fff;
  border: 1px solid #e8eaef;
  border-radius: 12px;
  padding: 10px 12px;
  box-shadow: 0 1px 8px rgba(7,16,29,0.05);
}
.subtle{
  color:#6b7785;
  font-size:12px;
}
.stTabs [data-baseweb="tab"]{
  font-size: 14px;
  padding: 10px 14px;
}
.stButton>button{
  border-radius: 10px;
  border: 1px solid #d7dbe2;
}
.banner-wrap{
  position: relative;
  width: 100vw;
  margin-left: calc(-50vw + 50%);
  margin-right: calc(-50vw + 50%);
  border-radius: 0;
  overflow: hidden;
  border-top: 1px solid #e2e5ea;
  border-bottom: 1px solid #e2e5ea;
  margin-bottom: 14px;
  height: 180px;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}
.banner-overlay{
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(10,20,30,0.25) 0%, rgba(10,20,30,0.05) 50%, rgba(10,20,30,0.18) 100%);
}
.logo-row{
  display: none;
}
.logo-badge{
  display: none;
}
.logo-badge img{
  height: 42px;
  width: auto;
  display: block;
}
.banner-title{
  position: absolute;
  left: 16px;
  bottom: 12px;
  color: #ffffff;
  font-family: "Spectral", serif;
  font-size: 22px;
  font-weight: 600;
  text-shadow: 0 2px 8px rgba(0,0,0,0.35);
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# MODULE 1: FORENSIC GOVERNANCE ENGINE
# ------------------------------

PROVISIONAL_LABEL = "Provisional – For Scheme Delivery Only – Not a Title Document"

def generate_strong_fid(name, village_code, device_id="TAB-09", parentage=""):
    """Offline-Resilient Farmer ID Generation (Section 2.1.1)"""
    lgd = str(village_code).strip().upper()
    raw_string = f"{str(name).strip().upper()}|{str(parentage).strip().upper()}|{device_id}"
    hash_part = hashlib.sha256(raw_string.encode()).hexdigest()[:6].upper()
    return f"JK-FID-{lgd}-{hash_part}"

def generate_pid(khasra_no, village_code):
    raw_string = f"{str(khasra_no).strip().upper()}|{village_code}"
    return f"PID-{hashlib.sha256(raw_string.encode()).hexdigest()[:12].upper()}"

def get_plot_center(khasra_no):
    """Deterministic pseudo-plot center for a Khasra number (demo only)."""
    base_lat, base_lon = 33.7782, 76.5762
    seed = int(hashlib.sha256(str(khasra_no).encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    lat = base_lat + rng.uniform(-0.01, 0.01)
    lon = base_lon + rng.uniform(-0.01, 0.01)
    return lat, lon

def haversine_meters(lat1, lon1, lat2, lon2):
    """Approximate distance between two GPS points in meters."""
    r = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def simulate_gis_integrity_check(khasra_no):
    """Simulates Geofence check (Section 4.2)"""
    if "2501" in str(khasra_no):
        return False, 33.7782, 75.0500, "OUT_OF_BOUNDS (52m deviation)"
    lat, lon = get_plot_center(khasra_no)
    jitter = random.uniform(-0.0003, 0.0003)
    return True, lat + jitter, lon - jitter, "WITHIN_GEOFENCE"

def parse_float(value):
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
        return float(value)
    except Exception:
        return None

def normalize_identity(name, parentage, lgd_code, device_id):
    n = str(name).lower()
    n = re.sub(r'[^a-z\\s]', '', n)
    p = str(parentage).lower()
    p = re.sub(r'[^a-z\\s]', '', p)
    lgd = str(lgd_code).strip().upper()
    dev = str(device_id).strip().upper()
    return f"{n}|{p}|{lgd}|{dev}"

def add_audit_entry(existing, prev_channel, new_channel, reason, vdv_id):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{ts} | {vdv_id} | {prev_channel} -> {new_channel} | {reason}"
    if existing:
        return f"{existing} | {entry}"
    return entry

def month_add(dt, months):
    year = dt.year + (dt.month - 1 + months) // 12
    month = (dt.month - 1 + months) % 12 + 1
    day = min(dt.day, [31,29 if year%4==0 and (year%100!=0 or year%400==0) else 28,31,30,31,30,31,31,30,31,30,31][month-1])
    return dt.replace(year=year, month=month, day=day)

def fuzzy_match_score(name1, name2):
    """Identity resolution with fuzzy matching (Section 3.1.A)"""
    if pd.isna(name1) or pd.isna(name2): return 0
    n1 = str(name1).lower().replace("sardar","").replace("shri","").replace("mr.","").strip()
    n2 = str(name2).lower().replace("sardar","").replace("shri","").replace("mr.","").strip()
    return round(SequenceMatcher(None, n1, n2).ratio()*100,1)

def check_custodian_status(remarks):
    """Statutory exclusions (Table 3.1)"""
    keywords = ['custodian','evacuee','muhajireen','state land','auqaf']
    for word in keywords:
        if word in str(remarks).lower(): return True, -0.25
    return False, 0.0

def check_land_nuance_strict(land_type):
    """Hard blocks for infrastructure, housing nuances (Fix Gap 7)"""
    lt = str(land_type).lower()
    if any(x in lt for x in ['sarak','road','nallah','river','darya','forest']):
        return "BLOCKED_INFRA", -0.40, True
    if 'gair mumkin' in lt and ('makan' in lt or 'abadi' in lt):
        return "HOUSING", -0.10, False
    return "AGRI", 0.0, False

def derive_mutation_status(remarks):
    """Infers mutation status from remarks text"""
    rem = str(remarks).lower()
    if "pending" in rem: return "Pending"
    if re.search(r'\d+', rem): return "Active"
    return "Active"

def check_mutation_logic(mutation_status, remarks):
    """Inheritance amnesty & grey channel routing (Section 3.2)"""
    mut = str(mutation_status).lower()
    rem = str(remarks).lower()
    if mut in ['pending','no'] and 'varasat' in rem: return "GREY_CANDIDATE",0.0
    elif mut in ['pending','no']: return "BROKEN_CHAIN",-0.20
    return "ACTIVE",0.0

def execute_verification_protocol(df):
    """Master governance protocol: generates FID, computes trust score, assigns channels"""
    df = df.copy()
    df['AgriStack_FID'] = df.apply(
        lambda row: generate_strong_fid(
            row.get('Owner_Name','Unknown'),
            row.get('LGD_Code', row.get('Village_Code', "VIL001")),
            row.get('VDV_Device_ID', "TAB-09"),
            row.get('Parentage_Name','')
        ),
        axis=1
    )
    df['Plot_ID'] = df.apply(
        lambda row: generate_pid(row.get('Khasra_No','000'), row.get('LGD_Code', row.get('Village_Code', "VIL001"))),
        axis=1
    )
    df['Entity_Key'] = df.apply(
        lambda row: normalize_identity(
            row.get('Owner_Name',''),
            row.get('Parentage_Name',''),
            row.get('LGD_Code', row.get('Village_Code','')),
            row.get('VDV_Device_ID','')
        ),
        axis=1
    )
    df['Provisional_Label'] = PROVISIONAL_LABEL

    results, map_points = [], []
    for _, row in df.iterrows():
        base_score = 1.0
        logic_trace = []
        hard_block_trigger = False
        reasons = []

        # GIS check (uses VDV GPS if available)
        khasra = str(row.get('Khasra_No','000'))
        vdv_lat = parse_float(row.get('VDV_Lat', None))
        vdv_lon = parse_float(row.get('VDV_Lon', None))
        if vdv_lat is not None and vdv_lon is not None:
            center_lat, center_lon = get_plot_center(khasra)
            distance_m = haversine_meters(vdv_lat, vdv_lon, center_lat, center_lon)
            gis_pass = distance_m <= 50
            gis_msg = f"{'WITHIN' if gis_pass else 'OUT_OF_BOUNDS'}_GEOFENCE ({int(distance_m)}m deviation)"
            lat, lon = vdv_lat, vdv_lon
        else:
            gis_pass, lat, lon, gis_msg = simulate_gis_integrity_check(khasra)
        row['GIS_Status'] = gis_msg
        map_points.append({'lat': lat, 'lon': lon, 'status': 'PASS' if gis_pass else 'FAIL'})
        if not gis_pass:
            base_score -= 0.50
            logic_trace.append("GIS Integrity Fail (-0.50)")
            hard_block_trigger = True

        # Custodian check
        is_custodian, cust_penalty = check_custodian_status(row.get('Remarks_Kaifiyat',''))
        if is_custodian:
            base_score += cust_penalty
            logic_trace.append("Custodian Land (-0.25)")
            reasons.append("CUSTODIAN")

        # Land nuance
        land_cat, land_penalty, is_hard_block = check_land_nuance_strict(row.get('Land_Type',''))
        if is_hard_block:
            hard_block_trigger = True
            logic_trace.append(f"State Asset Block: {land_cat}")
        base_score += land_penalty

        # VDV validation
        verified_name = row.get('VDV_Verified_Name', row.get('Owner_Name','Unknown'))
        if pd.isna(verified_name) or str(verified_name).strip() == "":
            base_score -= 0.20
            logic_trace.append("VDV Validation Missing (-0.20)")

        # Identity resolution
        id_score = fuzzy_match_score(row.get('Owner_Name',''), verified_name)
        if id_score < 50:
            base_score -= 0.50
            logic_trace.append(f"Identity Mismatch {id_score}% (-0.50)")
            hard_block_trigger = True

        # VDV rotation safeguard
        vdv_domicile = str(row.get('VDV_Domicile_Village','')).strip()
        village_code = str(row.get('Village_Code','')).strip()
        vdv_rotation_fail = vdv_domicile != "" and village_code != "" and vdv_domicile == village_code
        if vdv_rotation_fail:
            hard_block_trigger = True
            logic_trace.append("VDV Rotation Fail")
            reasons.append("VDV_ROTATION_FAIL")

        # Proxy verification
        proxy_flag = str(row.get('Proxy_Verification','')).strip().lower() in ['yes','true','1']

        # Grey channel logic for Varasat
        mutation_status = derive_mutation_status(row.get('Remarks_Kaifiyat',''))
        mut_state, mut_penalty = check_mutation_logic(mutation_status, row.get('Remarks_Kaifiyat',''))
        base_score += mut_penalty
        if mut_state == "GREY_CANDIDATE":
            reasons.append("VARASAT_GREY")

        # Final scoring & routing
        final_score = max(round(base_score, 2), 0.0)
        if hard_block_trigger:
            channel = "RED"; action = "Blocked: Critical Failure"; final_score = min(final_score, 0.40)
        elif "VARASAT_GREY" in reasons:
            channel = "GREY"; action = "Deemed Verified (Varasat Amnesty)"
        elif is_custodian:
            channel = "AMBER"; action = "CRC Path (Custodian)"
        elif final_score >= 0.80:
            channel = "GREEN"; action = "Auto-Approve"
        elif final_score >= 0.50:
            channel = "AMBER"; action = "Provisional Review"
        else:
            channel = "RED"; action = "Score Too Low"

        if proxy_flag and channel in ["GREEN","GREY"]:
            channel = "AMBER"; action = "Proxy Verification (Reverify)"
            reasons.append("PROXY_VERIFICATION")

        # Amnesty and re-verification
        created_ts = row.get('Record_Created','')
        if created_ts:
            try:
                created_dt = datetime.strptime(created_ts, "%Y-%m-%d")
            except Exception:
                created_dt = datetime.now()
        else:
            created_dt = datetime.now()
        amnesty_expiry = ""
        reverify_by = ""
        if channel == "GREY":
            amnesty_expiry = month_add(created_dt, 24).strftime("%Y-%m-%d")
            if datetime.now() > month_add(created_dt, 24):
                channel = "AMBER"
                action = "Grey Amnesty Expired"
                reasons.append("AMNESTY_EXPIRED")
        if proxy_flag:
            reverify_by = month_add(created_dt, 12).strftime("%Y-%m-%d")

        # Scheme flags and CRC
        row['CRC_Issued'] = True if is_custodian else False
        row['Credit_Path'] = "CRC_RESTRICTED" if is_custodian else "FULL"
        row['KCC_Eligible'] = True if channel in ["GREEN","GREY"] and not is_custodian else False
        row['PM_KISAN_Eligible'] = True if channel in ["GREEN","GREY","AMBER"] else False
        row['PMFBY_Eligible'] = True if channel in ["GREEN","GREY","AMBER"] else False

        # Workflow queues
        if channel == "AMBER":
            row['Workflow_Queue'] = "BLOCK_TECH_UNIT"
        elif channel == "GREY":
            row['Workflow_Queue'] = "MUTATION_FOLLOWUP"
        elif channel == "RED":
            row['Workflow_Queue'] = "AUDIT_QUEUE"
        else:
            row['Workflow_Queue'] = "AUTO_CLEARED"

        # Audit log and transitions
        prev_channel = row.get('Prev_Channel','NEW')
        vdv_id = row.get('VDV_Device_ID','VDV-UNK')
        row['Audit_Log'] = add_audit_entry(row.get('Audit_Log',''), prev_channel, channel, action, vdv_id)

        # Safeguards
        seed = int(hashlib.sha256(str(row['AgriStack_FID']).encode()).hexdigest()[:8], 16)
        row['Super_Check_Selected'] = True if (seed % 100) < 5 else False
        row['VDV_Rotation_Flag'] = True if vdv_rotation_fail else False

        # Offline sync
        row['Sync_Status'] = row.get('Sync_Status','QUEUED_OFFLINE')
        row['Amnesty_Expiry'] = amnesty_expiry
        row['Reverify_By'] = reverify_by

        row['Trust_Score'] = final_score
        row['Governance_Channel'] = channel
        row['Action_Taken'] = action
        row['Audit_Trace'] = "; ".join(logic_trace)
        row['Validation_Status'] = channel
        row['Confidence_Score'] = final_score
        eligible = []
        if row['KCC_Eligible']:
            eligible.append("KCC")
        if row['PM_KISAN_Eligible']:
            eligible.append("PM-KISAN")
        if row['PMFBY_Eligible']:
            eligible.append("PMFBY")
        row['Welfare_Eligibility_Flag'] = ",".join(eligible)

        results.append(row)

    return pd.DataFrame(results), pd.DataFrame(map_points)

# ============================================================
# MODULE 2: ROBUST DATA LOADING & OCR SIMULATION
# ============================================================

USER_COLUMNS = [
    'Khevat_No', 'Khata_No', 'Owner_Name', 'Cultivator_Name', 
    'Khasra_No', 'Land_Type', 'Area_Kanal', 'Area_Marla', 'Remarks_Kaifiyat',
    'VDV_Verified_Name', 'VDV_Device_ID', 'VDV_Collector_Name',
    'VDV_Lat', 'VDV_Lon', 'VDV_Timestamp', 'Village_Code',
    'LGD_Code', 'District', 'Tehsil', 'Parentage_Name',
    'Proxy_Verification', 'Absentee_Reason', 'VDV_Domicile_Village',
    'Season', 'Crop_Sown', 'Record_Created', 'Prev_Channel', 'Audit_Log',
    'Sync_Status', 'Aadhaar_Verified', 'Aadhaar_Masked',
    'Revenue_Demand_Mutation', 'Role',
    'Farmer_Photo_Name', 'Farmer_Photo_Size_KB',
    'Plot_Photo_Name', 'Plot_Photo_Size_KB'
]

def load_data_robust(uploaded_file):
    """Robust CSV loader handling extra header rows"""
    try:
        df = pd.read_csv(uploaded_file)
        header_found = any("Khevat" in str(c) for c in df.columns)
        if header_found:
            for col in USER_COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, header=2)
        for col in USER_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    except:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, header=2)
        for col in USER_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df

def run_ocr_pipeline(uploaded_file):
    """Simulated OCR extraction for demo purposes"""
    time.sleep(2.5)
    mock_data = [
        {"Khevat_No":"101","Khata_No":"15","Owner_Name":"Gyan Chand pisar Dheru",
         "Cultivator_Name":"Khudkasht","Khasra_No":"401","Land_Type":"Nahri",
         "Remarks_Kaifiyat":"Tabadilah 1057","VDV_Verified_Name":"Gyan Chand pisar Dheru"},
        {"Khevat_No":"102","Khata_No":"16","Owner_Name":"Late Ghulam Rasool",
         "Cultivator_Name":"Heir A","Khasra_No":"405","Land_Type":"Agri",
         "Remarks_Kaifiyat":"VarasatPending","VDV_Verified_Name":"Ghulam Rasool"},
        {"Khevat_No":"105","Khata_No":"20","Owner_Name":"State Govt PWD",
         "Cultivator_Name":"Maqboza Dept","Khasra_No":"500","Land_Type":"Gair Mumkin Srk",
         "Remarks_Kaifiyat":"Road Infra","VDV_Verified_Name":"State Govt PWD"},
        {"Khevat_No":"110","Khata_No":"25","Owner_Name":"Custodian Evacuee Property",
         "Cultivator_Name":"Refugee Alloc","Khasra_No":"601","Land_Type":"Agri",
         "Remarks_Kaifiyat":"Custodian Land","VDV_Verified_Name":"Custodian Evacuee Property"},
        {"Khevat_No":"112","Khata_No":"28","Owner_Name":"Viijay Kmar pisar Sunar",
         "Cultivator_Name":"Maqboza Khud","Khasra_No":"605","Land_Type":"Agri",
         "Remarks_Kaifiyat":"Baya nama 334","VDV_Verified_Name":"Vijay Kumar pisar Sunar"},
        {"Khevat_No":"115","Khata_No":"30","Owner_Name":"State Irrigation Dept",
         "Cultivator_Name":"Sarkar","Khasra_No":"700","Land_Type":"Gair Mumkin Nallah",
         "Remarks_Kaifiyat":"Canal","VDV_Verified_Name":"State Irrigation Dept"},
        {"Khevat_No":"120","Khata_No":"35","Owner_Name":"Late Akbar Ali",
         "Cultivator_Name":"Sons of Akbar","Khasra_No":"801","Land_Type":"Agri",
         "Remarks_Kaifiyat":"Varasat Pnding","VDV_Verified_Name":"Akbar Ali"},
        {"Khevat_No":"125","Khata_No":"40","Owner_Name":"Sardar Karnail Singh",
         "Cultivator_Name":"Khudkasht","Khasra_No":"905","Land_Type":"Agri",
         "Remarks_Kaifiyat":"Clean","VDV_Verified_Name":"Karnail Singh"},
        {"Khevat_No":"130","Khata_No":"45","Owner_Name":"Pawan Kumar",
         "Cultivator_Name":"Khudkasht","Khasra_No":"1001","Land_Type":"Agri",
         "Remarks_Kaifiyat":"Mutation 505","VDV_Verified_Name":"Pawan Kumar"},
        {"Khevat_No":"135","Khata_No":"50","Owner_Name":"Harbans Lal",
         "Cultivator_Name":"Khudkasht","Khasra_No":"1100","Land_Type":"Gair Mumkin Makan",
         "Remarks_Kaifiyat":"Abadi Deh","VDV_Verified_Name":"Harbans Lal"},
        {"Khevat_No":"140","Khata_No":"55","Owner_Name":"Village Common Land",
         "Cultivator_Name":"Encroacher","Khasra_No":"2501","Land_Type":"Agri",
         "Remarks_Kaifiyat":"Active","VDV_Verified_Name":"Village Common Land"}
    ]
    df_result = pd.DataFrame(mock_data)
    for col in USER_COLUMNS:
        if col not in df_result.columns:
            df_result[col] = ""
    return df_result, "Success: Extracted {} records".format(len(df_result))

# ============================================================
# MODULE 3: STREAMLIT DASHBOARD
# ============================================================

def _img_b64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""

_BASE_DIR = Path(__file__).resolve().parent
_banner_b64 = _img_b64(_BASE_DIR / "jk_banner.png")
_govt_b64 = _img_b64(_BASE_DIR / "jk_govt.png")
_agri_b64 = _img_b64(_BASE_DIR / "jk_agri.png")

st.markdown(f"""
<div class="banner-wrap" style="background-image:url('data:image/png;base64,{_banner_b64}');">
  <div class="banner-overlay"></div>
  <div class="banner-title">AgriStack J&amp;K: Integrated Policy Implementation System</div>
</div>
<div class="app-hero">
  <div class="hero-sub">Possession‑Anchored, Welfare‑Enabled Digital Public Infrastructure</div>
  <div class="badge-row">
    <span class="badge">Prototype v1.2</span>
    <span class="badge">Policy Hackathon</span>
    <span class="badge">Streamlit + Python</span>
  </div>
</div>
""", unsafe_allow_html=True)
st.markdown(f"<div class='callout'><b>{PROVISIONAL_LABEL}</b></div>", unsafe_allow_html=True)

with st.sidebar:
    st.subheader("System Controls")
    offline_mode = st.checkbox("Offline Mode (Queue Sync)", value=True)
    st.caption("Offline mode queues sync events for low-connectivity regions.")

tab1, tab0, tab2, tab3, tab4 = st.tabs([
    "Phase 1: Digitization Workbench",
    "VDV Mobile Collection",
    "Phase 2: Governance Engine",
    "Registries & Queues",
    "Panchayat Validation"
])

# -----------------------
# TAB 0: VDV MOBILE DATA COLLECTION
# -----------------------
with tab0:
    st.markdown("<div class='section-title'>VDV Mobile Data Collection</div>", unsafe_allow_html=True)
    st.markdown("Use this on a mobile device to collect Aadhaar auth, farmer registration, and plot data.")
    st.markdown("<div class='callout'>Sequence: Aadhaar Authentication → Farmer Registration → Plot Registration</div>", unsafe_allow_html=True)

    if 'vdv_farmers' not in st.session_state:
        st.session_state['vdv_farmers'] = []
    if 'vdv_plots' not in st.session_state:
        st.session_state['vdv_plots'] = []
    if 'vdv_lat' not in st.session_state:
        st.session_state['vdv_lat'] = None
    if 'vdv_lon' not in st.session_state:
        st.session_state['vdv_lon'] = None
    if 'area_kanal_auto' not in st.session_state:
        st.session_state['area_kanal_auto'] = ""
    if 'area_marla_auto' not in st.session_state:
        st.session_state['area_marla_auto'] = ""
    if 'aadhaar_verified' not in st.session_state:
        st.session_state['aadhaar_verified'] = False
    if 'aadhaar_number' not in st.session_state:
        st.session_state['aadhaar_number'] = ""

    prefill_row = None
    if 'vdv_work_data' in st.session_state and len(st.session_state['vdv_work_data']) > 0:
        df_prefill = st.session_state['vdv_work_data'].copy()
        for col in USER_COLUMNS:
            if col not in df_prefill.columns:
                df_prefill[col] = ""
        df_prefill['_label'] = df_prefill.apply(lambda r: f"{r.get('Owner_Name','')} | {r.get('Khasra_No','')}", axis=1)
        selection = st.selectbox("Select record for prefill", df_prefill['_label'].tolist())
        prefill_row = df_prefill[df_prefill['_label'] == selection].iloc[0].to_dict()

    t_aadhaar, t_farmer, t_plot = st.tabs(["Aadhaar Authentication", "Farmer Registration", "Plot Registration"])

    with t_aadhaar:
        with st.form("aadhaar_form"):
            a_number = st.text_input("Aadhaar Number", value=st.session_state['aadhaar_number'])
            a_consent = st.checkbox("Consent to Aadhaar verification")
            a_otp = st.text_input("OTP (dummy: 123456)")
            verify = st.form_submit_button("Verify Aadhaar")
        if verify:
            if a_consent and a_otp.strip() == "123456" and len(a_number.strip()) >= 12:
                st.session_state['aadhaar_verified'] = True
                st.session_state['aadhaar_number'] = a_number.strip()
                st.success("Aadhaar verified.")
            else:
                st.session_state['aadhaar_verified'] = False
                st.error("Aadhaar verification failed.")

    with t_farmer:
        c1, c2, c3 = st.columns(3)
        with c1:
            vdv_device_id = st.text_input("VDV Device ID", value="TAB-09")
            vdv_collector = st.text_input("VDV Collector Name", value=st.session_state.get('vdv_collector_default', ''))
            vdv_domicile = st.text_input("VDV Domicile Village Code", value=st.session_state.get('vdv_domicile_default', ''))
        with c2:
            village_code = st.text_input("Village Code", value=prefill_row.get('Village_Code','VIL001') if prefill_row else "VIL001")
            lgd_code = st.text_input("LGD Code", value=prefill_row.get('LGD_Code','LGD-0001') if prefill_row else "LGD-0001")
        with c3:
            district = st.text_input("District", value=prefill_row.get('District','Srinagar') if prefill_row else "Srinagar")
            tehsil = st.text_input("Tehsil", value=prefill_row.get('Tehsil','Srinagar') if prefill_row else "Srinagar")

        c4, c5, c6 = st.columns(3)
        with c4:
            owner_name = st.text_input("Owner Name", value=prefill_row.get('Owner_Name','') if prefill_row else "")
            parentage_name = st.text_input("Parentage Name", value=prefill_row.get('Parentage_Name','') if prefill_row else "")
        with c5:
            cultivator_name = st.text_input("Cultivator Name", value=prefill_row.get('Cultivator_Name','') if prefill_row else "")
            vdv_verified_name = st.text_input("VDV Verified Name", value=owner_name)
        with c6:
            khevat_no = st.text_input("Khevat No", value=prefill_row.get('Khevat_No','') if prefill_row else "")
            khata_no = st.text_input("Khata No", value=prefill_row.get('Khata_No','') if prefill_row else "")

        c7, c8 = st.columns(2)
        with c7:
            role = st.selectbox("Role", ["Cultivator", "Tenant", "Sharecropper", "Owner-Cultivator"])
        with c8:
            revenue_demand = st.text_input("Revenue Demand / Mutation", value=prefill_row.get('Revenue_Demand_Mutation','') if prefill_row else "")

        proxy_verification = st.selectbox("Proxy Verification", ["No", "Yes"])
        absentee_reason = st.text_input("Absentee Reason")
        farmer_photo = st.file_uploader("Capture Farmer Photo (Geo-tagged)", type=["jpg", "jpeg", "png"])

        add_farmer = st.button("Register Farmer")
        if add_farmer:
            required_fields = {
                "VDV Collector Name": vdv_collector,
                "VDV Domicile Village Code": vdv_domicile,
                "District": district,
                "Tehsil": tehsil,
                "Owner Name": owner_name,
                "Parentage Name": parentage_name,
                "Khevat No": khevat_no,
                "Khata No": khata_no,
                "Cultivator Name": cultivator_name,
                "VDV Verified Name": vdv_verified_name,
                "Revenue Demand / Mutation": revenue_demand
            }
            missing = [k for k, v in required_fields.items() if str(v).strip() == ""]
            if not st.session_state['aadhaar_verified']:
                st.error("Aadhaar verification is required.")
                missing.append("Aadhaar Verification")
            if missing:
                st.error(f"Missing required fields: {', '.join(missing)}")
            else:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                aadhaar_masked = st.session_state['aadhaar_number'][-4:].rjust(12, "X") if st.session_state['aadhaar_number'] else ""
                farmer_id = generate_strong_fid(owner_name, lgd_code, vdv_device_id, parentage_name)
                farmer_record = {
                    "AgriStack_FID": farmer_id,
                    "Owner_Name": owner_name,
                    "Parentage_Name": parentage_name,
                    "Cultivator_Name": cultivator_name,
                    "VDV_Verified_Name": vdv_verified_name,
                    "VDV_Device_ID": vdv_device_id,
                    "VDV_Collector_Name": vdv_collector,
                    "VDV_Domicile_Village": vdv_domicile,
                    "Village_Code": village_code,
                    "LGD_Code": lgd_code,
                    "District": district,
                    "Tehsil": tehsil,
                    "Khevat_No": khevat_no,
                    "Khata_No": khata_no,
                    "Aadhaar_Verified": st.session_state['aadhaar_verified'],
                    "Aadhaar_Masked": aadhaar_masked,
                    "Proxy_Verification": proxy_verification,
                    "Absentee_Reason": absentee_reason,
                    "Revenue_Demand_Mutation": revenue_demand,
                    "Role": role,
                    "Farmer_Photo_Name": farmer_photo.name if farmer_photo else "NA",
                    "Farmer_Photo_Size_KB": int(farmer_photo.size/1024) if farmer_photo else "NA",
                    "Record_Created": timestamp.split(" ")[0],
                    "Sync_Status": "QUEUED_OFFLINE" if offline_mode else "SYNCED"
                }
                st.session_state['vdv_farmers'].append(farmer_record)
                st.session_state['last_farmer_id'] = farmer_id
                st.session_state['vdv_collector_default'] = vdv_collector
                st.session_state['vdv_domicile_default'] = vdv_domicile
                st.success("Farmer registered.")

    with t_plot:
        farmer_ids = [f['AgriStack_FID'] for f in st.session_state['vdv_farmers']]
        selected_farmer = st.selectbox("Select Farmer F-ID", farmer_ids) if farmer_ids else ""
        c7, c8, c9 = st.columns(3)
        with c7:
            khasra_no = st.text_input("Khasra No", value=prefill_row.get('Khasra_No','') if prefill_row else "")
            land_type = st.text_input("Land Type", value=prefill_row.get('Land_Type','') if prefill_row else "")
        with c8:
            area_kanal = st.text_input("Area (Kanal)", value=st.session_state['area_kanal_auto'] or (prefill_row.get('Area_Kanal','') if prefill_row else ""))
            area_marla = st.text_input("Area (Marla)", value=st.session_state['area_marla_auto'] or (prefill_row.get('Area_Marla','') if prefill_row else ""))
        with c9:
            season = st.text_input("Season", value="Rabi 2025")
            crop_sown = st.text_input("Crop Sown")
            remarks = st.text_input("Remarks / Kaifiyat", value=prefill_row.get('Remarks_Kaifiyat','') if prefill_row else "")

        capture_gps = st.button("Capture GPS (Simulated)")
        if capture_gps:
            if khasra_no.strip() != "":
                sim_lat, sim_lon = get_plot_center(khasra_no)
            else:
                sim_lat, sim_lon = 33.7782, 76.5762
            st.session_state['vdv_lat'] = round(sim_lat + random.uniform(-0.0003, 0.0003), 6)
            st.session_state['vdv_lon'] = round(sim_lon + random.uniform(-0.0003, 0.0003), 6)
            rand_area = random.uniform(1.5, 12.0)
            kanal = int(rand_area)
            marla = int((rand_area - kanal) * 20)
            st.session_state['area_kanal_auto'] = str(kanal)
            st.session_state['area_marla_auto'] = str(marla)

        vdv_lat = st.number_input("VDV Latitude", value=st.session_state['vdv_lat'] or 0.0, format="%.6f")
        vdv_lon = st.number_input("VDV Longitude", value=st.session_state['vdv_lon'] or 0.0, format="%.6f")
        vdv_photo = st.file_uploader("Capture Plot Photo (Geo-tagged)", type=["jpg", "jpeg", "png"])

        add_plot = st.button("Add Plot")
        if add_plot:
            required_plot = {
                "Farmer F-ID": selected_farmer,
                "Khasra No": khasra_no,
                "Land Type": land_type,
                "Area (Kanal)": area_kanal,
                "Area (Marla)": area_marla,
                "Remarks / Kaifiyat": remarks,
                "Season": season,
                "Crop Sown": crop_sown,
                "VDV Latitude": vdv_lat,
                "VDV Longitude": vdv_lon
            }
            missing_plot = [k for k, v in required_plot.items() if str(v).strip() == "" or str(v) == "0.0"]
            if missing_plot:
                st.error(f"Missing required fields: {', '.join(missing_plot)}")
            else:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                photo_name = vdv_photo.name if vdv_photo else ""
                photo_size_kb = int(vdv_photo.size/1024) if vdv_photo else ""
                plot_id = generate_pid(khasra_no, prefill_row.get('LGD_Code','LGD-0001') if prefill_row else "LGD-0001")
                plot_record = {
                    "AgriStack_FID": selected_farmer,
                    "Plot_ID": plot_id,
                    "Khasra_No": khasra_no,
                    "Land_Type": land_type,
                    "Area_Kanal": area_kanal,
                    "Area_Marla": area_marla,
                    "Remarks_Kaifiyat": remarks,
                    "Season": season,
                    "Crop_Sown": crop_sown,
                    "VDV_Lat": vdv_lat,
                    "VDV_Lon": vdv_lon,
                    "VDV_Timestamp": timestamp,
                    "Plot_Photo_Name": photo_name,
                    "Plot_Photo_Size_KB": photo_size_kb
                }
                st.session_state['vdv_plots'].append(plot_record)
                st.success("Plot added.")

    if len(st.session_state['vdv_farmers']) > 0 or len(st.session_state['vdv_plots']) > 0:
        st.subheader("Collected Records")
        df_farmers = pd.DataFrame(st.session_state['vdv_farmers'])
        df_plots = pd.DataFrame(st.session_state['vdv_plots'])
        st.markdown("Farmers")
        st.dataframe(df_farmers, use_container_width=True)
        st.markdown("Plots")
        st.dataframe(df_plots, use_container_width=True)

        if len(df_farmers) > 0 and len(df_plots) > 0:
            df_mobile = df_plots.merge(df_farmers, on='AgriStack_FID', how='left')
        elif len(df_farmers) > 0:
            df_mobile = df_farmers.copy()
        else:
            df_mobile = df_plots.copy()

        for col in USER_COLUMNS:
            if col not in df_mobile.columns:
                df_mobile[col] = "NA"
        df_mobile = df_mobile.fillna("NA").replace("", "NA")

        st.download_button(
            "Download Mobile Collection CSV",
            df_mobile.to_csv(index=False).encode('utf-8'),
            "VDV_Mobile_Collection.csv",
            "text/csv"
        )
        if st.button("Clear Mobile Collection"):
            st.session_state['vdv_farmers'] = []
            st.session_state['vdv_plots'] = []
            st.session_state['aadhaar_verified'] = False
            st.session_state['aadhaar_number'] = ""
            st.success("Cleared.")

# -----------------------
# TAB 1: DIGITIZATION
# -----------------------
with tab1:
    st.markdown("<div class='section-title'>Phase 1: Human-in-the-Loop Digitization</div>", unsafe_allow_html=True)
    st.markdown("Upload a scanned Jamabandi PDF (Shikasta Urdu) to verify the AI's extraction.")
    st.markdown("<div class='callout'>Output from this phase is the corrected OCR dataset used for VDV field verification.</div>", unsafe_allow_html=True)

    # CHANGE 1: Accept PDF files
    uploaded_raw = st.file_uploader(
        "Upload Scanned Jamabandi PDF",
        type=['pdf'],
        key="raw_up_unique"
    )

    # 1. Load Data & Initialize Session
    if uploaded_raw:
        # Run OCR simulation
        df_ocr, status = run_ocr_pipeline(uploaded_raw)
        
        # Normalize columns
        for col in USER_COLUMNS:
            if col not in df_ocr.columns:
                df_ocr[col] = ""

        # Store data in session
        st.session_state['ocr_data'] = df_ocr
        st.session_state['ocr_status'] = status
        
        # Initialize WORKING copy
        if 'vdv_work_data' not in st.session_state:
            st.session_state['vdv_work_data'] = df_ocr.copy()

    # 2. Display Split Screen
    if uploaded_raw and 'ocr_data' in st.session_state:
        st.success(f"AI Extraction Status: {st.session_state['ocr_status']}")

        col_left, col_right = st.columns([1, 1], gap="large")

        # LEFT SCREEN: PDF Viewer (Embedded)
        with col_left:
            st.subheader("Source Document (PDF)")
            st.info("Reference: Original Shikasta Urdu Script")
            
            # --- PDF EMBEDDING LOGIC ---
            # 1. Read file as bytes
            uploaded_raw.seek(0)
            base64_pdf = base64.b64encode(uploaded_raw.read()).decode('utf-8')
            
            # 2. Embed PDF in HTML iframe
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
            
            # 3. Render in Streamlit
            st.markdown(pdf_display, unsafe_allow_html=True)
            # ---------------------------

        # RIGHT SCREEN: Editable Data
        with col_right:
            st.subheader("Digitization Workbench")
            st.warning("Action: Verify against the PDF on the left")
            
            st.session_state['vdv_work_data'] = st.data_editor(
                st.session_state['vdv_work_data'],
                num_rows="dynamic",
                key="ocr_editor_right",
                use_container_width=True,
                height=600
            )

        # 3. Download Button
        st.divider()
        st.download_button(
            "Download Verified CSV (Phase 1 Output)",
            st.session_state['vdv_work_data'].to_csv(index=False).encode('utf-8'),
            "Transliterated_Verified_Data.csv",
            key="download_csv",
            mime="text/csv",
            type="primary"
        )# -----------------------
# TAB 2: GOVERNANCE
# -----------------------
with tab2:
    uploaded_verified = st.file_uploader("Upload Transliterated CSV", type=['csv'], key="ver_upload_tab2")
    if uploaded_verified:
        df_input = load_data_robust(uploaded_verified)
        st.success(f"Successfully loaded {len(df_input)} records.")
        with st.expander("Preview Data"):
            st.dataframe(df_input)

        if st.button("Execute Governance Protocol", key="governance_btn"):
            # Assume execute_verification_protocol is implemented
            df_final, map_data = execute_verification_protocol(df_input)

            # Registries
            df_ranked = df_final.sort_values(by=['Trust_Score'], ascending=False)
            farmer_registry = df_ranked.groupby('AgriStack_FID', as_index=False).first()
            plot_registry = df_ranked.groupby('Plot_ID', as_index=False).first()
            crop_registry = df_final[['AgriStack_FID','Plot_ID','Season','Crop_Sown','Village_Code','LGD_Code']].copy()

            # Dedupe and conflicts
            entity_counts = df_final.groupby('Entity_Key').size().reset_index(name='Entity_Count')
            df_final = df_final.merge(entity_counts, on='Entity_Key', how='left')
            df_final['Cross_District_Dedupe_Flag'] = df_final.groupby('Entity_Key')['District'].transform('nunique') > 1
            df_final['Conflict_Flag'] = df_final['Entity_Count'] > 1

            # GIS overlap detection
            plot_counts = df_final.groupby('Plot_ID').size().reset_index(name='Plot_Count')
            df_final = df_final.merge(plot_counts, on='Plot_ID', how='left')
            df_final['GIS_Overlap_Flag'] = df_final['Plot_Count'] > 1

            # Queue snapshots
            amber_queue = df_final[df_final['Workflow_Queue'] == 'BLOCK_TECH_UNIT']
            grey_queue = df_final[df_final['Workflow_Queue'] == 'MUTATION_FOLLOWUP']
            red_queue = df_final[df_final['Workflow_Queue'] == 'AUDIT_QUEUE']
            gis_queue = df_final[df_final['GIS_Overlap_Flag'] == True]

            df_display = df_final.fillna("NA").replace("", "NA")
            st.session_state['df_final'] = df_display
            st.session_state['map_data'] = map_data
            st.session_state['farmer_registry'] = farmer_registry.fillna("NA").replace("", "NA")
            st.session_state['plot_registry'] = plot_registry.fillna("NA").replace("", "NA")
            st.session_state['crop_registry'] = crop_registry.fillna("NA").replace("", "NA")
            st.session_state['amber_queue'] = amber_queue.fillna("NA").replace("", "NA")
            st.session_state['grey_queue'] = grey_queue.fillna("NA").replace("", "NA")
            st.session_state['red_queue'] = red_queue.fillna("NA").replace("", "NA")
            st.session_state['gis_queue'] = gis_queue.fillna("NA").replace("", "NA")

            st.subheader("GIS Plot Verification")
            map_df = map_data.copy()
            map_df['color'] = map_df['status'].apply(lambda s: [0, 180, 0, 140] if s == 'PASS' else [200, 0, 0, 160])
            if len(map_df) > 0:
                view_state = pdk.ViewState(
                    latitude=map_df['lat'].mean(),
                    longitude=map_df['lon'].mean(),
                    zoom=10
                )
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=map_df,
                    get_position='[lon, lat]',
                    get_fill_color='color',
                    get_radius=60,
                    pickable=True
                )
                st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{status}"}))
            else:
                st.info("No GIS points available.")

            st.subheader("Governance Audit Results")
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"<div class='card'><div class='subtle'>Green</div><div style='font-size:26px;font-weight:700'>{len(df_final[df_final['Governance_Channel']=='GREEN'])}</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='card'><div class='subtle'>Grey</div><div style='font-size:26px;font-weight:700'>{len(df_final[df_final['Governance_Channel']=='GREY'])}</div></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='card'><div class='subtle'>Amber</div><div style='font-size:26px;font-weight:700'>{len(df_final[df_final['Governance_Channel']=='AMBER'])}</div></div>", unsafe_allow_html=True)
            c4.markdown(f"<div class='card'><div class='subtle'>Red</div><div style='font-size:26px;font-weight:700'>{len(df_final[df_final['Governance_Channel']=='RED'])}</div></div>", unsafe_allow_html=True)

            # --- Color-coded final table
            def color_coding(row):
                val = row['Governance_Channel']
                if val=='GREEN': return ['background-color: #d4edda']*len(row)
                elif val=='GREY': return ['background-color: #e2e3e5']*len(row)
                elif val=='AMBER': return ['background-color: #fff3cd']*len(row)
                else: return ['background-color: #f8d7da']*len(row)

            disp_cols = [
                'AgriStack_FID', 'Plot_ID', 'Owner_Name', 'Land_Type', 'GIS_Status',
                'Trust_Score', 'Governance_Channel', 'Action_Taken', 'CRC_Issued',
                'KCC_Eligible', 'PM_KISAN_Eligible', 'PMFBY_Eligible', 'Workflow_Queue',
                'Amnesty_Expiry', 'Reverify_By', 'Super_Check_Selected', 'Provisional_Label'
            ]
            final_cols = [c for c in disp_cols if c in df_final.columns]
            df_display = df_final.fillna("NA").replace("", "NA")
            st.dataframe(df_display[final_cols].style.apply(color_coding, axis=1))
            st.download_button(
                "Export Final Registry",
                df_display.to_csv(index=False).encode('utf-8'),
                "AgriStack_Final_Registry.csv",
                "text/csv"
            )

# -----------------------
# TAB 3: REGISTRIES & QUEUES
# -----------------------
with tab3:
    st.markdown("<div class='section-title'>Registries & Governance Queues</div>", unsafe_allow_html=True)
    if 'df_final' not in st.session_state:
        st.info("Run Phase 2 to populate registries and queues.")
    else:
        st.subheader("Farmer Registry (F-ID)")
        st.dataframe(st.session_state['farmer_registry'], use_container_width=True)

        st.subheader("Plot Registry (P-ID)")
        st.dataframe(st.session_state['plot_registry'], use_container_width=True)

        st.subheader("Crop Sown Registry (Seasonal Link)")
        st.dataframe(st.session_state['crop_registry'], use_container_width=True)

        st.subheader("Dedupe and Cross-District Flags")
        dedupe_view = st.session_state['df_final'][['AgriStack_FID','Owner_Name','Entity_Key','Entity_Count','Conflict_Flag','Cross_District_Dedupe_Flag','District','Tehsil','Village_Code']]
        st.dataframe(dedupe_view, use_container_width=True)

        st.subheader("Governance Queues")
        st.markdown("Amber → Block Technical Unit")
        st.dataframe(st.session_state['amber_queue'], use_container_width=True)
        st.markdown("Grey → Mutation Follow-up")
        st.dataframe(st.session_state['grey_queue'], use_container_width=True)
        st.markdown("Red → Audit Queue")
        st.dataframe(st.session_state['red_queue'], use_container_width=True)

        st.subheader("GIS Analyst Review Queue")
        st.dataframe(st.session_state['gis_queue'], use_container_width=True)

# -----------------------
# TAB 4: PANCHAYAT VALIDATION
# -----------------------
with tab4:
    st.markdown("<div class='section-title'>Panchayat Validation</div>", unsafe_allow_html=True)
    if 'df_final' not in st.session_state:
        st.info("Run Phase 2 to open the public verification wall.")
    else:
        st.subheader("Public Verification Wall")
        wall_cols = ['AgriStack_FID','Owner_Name','Village_Code','Khasra_No','Governance_Channel','Trust_Score','Provisional_Label']
        wall_cols = [c for c in wall_cols if c in st.session_state['df_final'].columns]
        st.dataframe(st.session_state['df_final'][wall_cols], use_container_width=True)

        if 'grievances' not in st.session_state:
            st.session_state['grievances'] = []

        st.subheader("Grievance Intake")
        with st.form("grievance_form"):
            g_fid = st.text_input("AgriStack F-ID")
            g_name = st.text_input("Complainant Name")
            g_contact = st.text_input("Contact")
            g_reason = st.text_area("Grievance Details")
            g_priority = st.selectbox("Priority", ["Low","Medium","High"])
            submit_grievance = st.form_submit_button("Submit Grievance")
        if submit_grievance:
            st.session_state['grievances'].append({
                "AgriStack_FID": g_fid,
                "Name": g_name,
                "Contact": g_contact,
                "Priority": g_priority,
                "Details": g_reason,
                "Status": "PANCHAYAT_REVIEW",
                "Submitted": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.success("Grievance submitted.")

        if len(st.session_state['grievances']) > 0:
            st.subheader("Grievance Queue")
            st.dataframe(pd.DataFrame(st.session_state['grievances']), use_container_width=True)
