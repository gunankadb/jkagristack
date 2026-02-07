# AgriStack J&K: Integrated Policy Implementation System
### *Possession-Anchored, Welfare-Enabled Digital Public Infrastructure (DPI)*

![Status](https://img.shields.io/badge/Status-Prototype_v1.0-blue) ![Context](https://img.shields.io/badge/Event-Harvard_Policy_Hackathon-maroon) ![Tech](https://img.shields.io/badge/Built_With-Streamlit_|_Python-green)

## 1. Executive Summary
This software serves as the **Digital Public Infrastructure (DPI)** for the *AgriStack J&K Policy Framework*. It automates the verification of legacy land records (*Jamabandis*), transitioning them from static paper documents to a dynamic, credit-ready digital registry.

By decoupling "Service Eligibility" from "Legal Title Finality," this system allows immediate welfare delivery to active cultivators while long-term legal disputes are resolved in the background.

### ⚠️ Project Scope & Limitations
> **"This prototype focuses on the 'Land Governance & Registration' layer of AgriStack (cleaning the RoR, generating FIDs, and validating statutory compliance). It simulates the GIS Integrity Check and OCR ingestion to demonstrate the governance logic flow."**

---

## 2. Key Functional Modules

The application is divided into two distinct operational phases:

### Phase 0: VDV Mobile Data Collection
* **Problem:** Field data is often captured on paper and later retyped, creating delays and errors.
* **Solution:** A mobile-friendly flow with Aadhaar verification, farmer registration, and plot capture in real time.
* **Tech:** Streamlit form-based capture with GPS simulation, auto-area calculation on geo capture, and CSV export.

### Phase 1: Human-in-the-Loop Digitization Workbench
* **Problem:** Legacy records are in *Shikasta* (cursive) Urdu and often illegible.
* **Solution:** A split-screen interface where **AI-Simulated OCR** extracts raw data, and a Village Data Volunteer (VDV) verifies/edits the entries against the original PDF scan.
* **Tech:** Utilizes a **Simulated OCR Pipeline** to mimic the post-processing of Bhashini AI outputs.

### Phase 2: Governance & GIS Engine
This is the algorithmic core that processes the digitized data:
1.  **Forensic Audit Logic:** Implements the **Risk Verification Matrix** to assign Trust Scores (0.0–1.0).
2.  **GIS Plot Integrity:** Simulates a real-time geofence check. It validates if the VDV's physical location matches the plot's official coordinates (blocking 'Ghost Surveys').
3.  **Governance Channels:**
    * 🟢 **Green:** Verified, eligible for full KCC (Kisan Credit Card).
    * ⚪ **Grey:** Inheritance (*Varasat*) cases deemed verified with a 24-month amnesty.
    * 🟡 **Amber:** Provisional; welfare allowed (CRC) but subject to review.
    * 🔴 **Red:** Blocked due to identity failure, encroachment (*Sarak/Nallah*), or GIS mismatch.

### Phase 3: Registries & Governance Queues
* **Farmer Registry (F-ID):** Provisional identities tied to LGD + Device ID.
* **Plot Registry (P-ID):** Deterministic plot IDs derived from Khasra + LGD.
* **Crop Sown Registry:** Seasonal link between F-ID and P-ID.
* **Queues:** Amber → Block Technical Unit, Grey → Mutation Follow-up, Red → Audit.

### Phase 4: Panchayat Validation
* **Public Verification Wall:** Community validation view.
* **Grievance Intake:** Panchayat-level escalation and tracking.

---

## 3. Policy Alignment Matrix

| Code Feature | Policy Principle Implemented |
| :--- | :--- |
| **Offline-Resilient Hashing** | **Sec 2.1.1:** Deterministic ID generation (`Name` + `Village` + `DeviceID`) ensuring uniqueness without connectivity. |
| **Fuzzy Matching** | **Sec 3.1.A:** Handles spelling variations between Urdu and English IDs. |
| **GIS Module** | **Sec 4.2:** Plot Integrity; Ensures VDV physically visited the field. |
| **Grey Channel** | **Sec 3.2:** Amnesty for *Varasat* (Inheritance) pending mutations. |
| **Amber Channel** | **Table 3.1:** Financial inclusion for *Custodian/Evacuee* land occupants. |

---

## 4. Installation & Setup

### Prerequisites
* Python 3.9+

### Step 1: Install Dependencies
```bash
pip install streamlit pandas numpy

```

### Step 2: Launch the Application

```bash
streamlit run agristack_app_v9.py

```

The application will open in your browser at `http://localhost:8501`.

---

## 5. How to Run the Demo (Walkthrough)

0. **Phase 1 (Digitization):**
* Go to the **"Phase 1"** tab.
* Upload the sample `Jamabandi_Sample.pdf` (provided in repo).
* The system simulates the OCR extraction. As a VDV, verify the data against the PDF viewer.
* Click **"Download Verified CSV"**.

1. **VDV Mobile Collection:**
* Go to the **"VDV Mobile Collection"** tab.
* Verify Aadhaar (dummy), register the farmer, then add plot data.
* Farmer Registration auto-prefills from the corrected OCR dataset where available.
* Plot capture uses GPS to auto-fill area and collects geo-tagged photos.
* Download the **VDV_Mobile_Collection.csv** output and use it in Phase 2.

2. **Phase 2 (Governance):**
* Go to the **"Phase 2"** tab.
* Upload the CSV you just downloaded.
* Click **"Execute Governance Protocol"**.


3. **The Result:**
* View the **Governance Channels** (Green/Grey/Amber/Red).
* Interact with the **GIS Map Widget** (Observe the "Red Flag" on Khasra 2501 for Geofence failure).
* Review the **Audit Trace** logs for blocked farmers.
* Explore **Registries & Queues** and the **Panchayat Validation** module.



---

## 6. Disclaimer

This is a policy demonstration prototype created for the **Harvard Kennedy School Policy Hackathon**. It simulates governance logic and system architecture for welfare-linked agricultural digitization. It does **not** create or modify official land ownership records and must not be used for legal title determination.
