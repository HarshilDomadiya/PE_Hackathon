# Content Repurposing Chain — Setup & Run Guide
**Team 24 | Problem 22 | Marwadi University Hackathon**

---

## 📋 Prerequisites on Your Computer

1. **Node.js** (v18 or higher) — [Download Node.js](https://nodejs.org/)
2. **Python** (v3.9, 3.10, 3.11, or 3.12) — [Download Python](https://www.python.org/)

---

## 🚀 Quick 2-Minute Setup Instructions

### Step 1: Open Terminal / Command Prompt in Project Folder
Open your terminal (PowerShell, Command Prompt, or Terminal) and navigate into this folder:
```bash
cd content_repurposing_chain
```

### Step 2: Install Node.js Dependencies
Run the following command to install Express, Cors, and Multer:
```bash
npm install
```

### Step 3: Install Python AI & PDF OCR Dependencies
Run the following command to install the Python PDF extraction & OCR libraries:
```bash
pip install PyMuPDF easyocr pypdf python-docx
```

### Step 4: Launch the Web Application
Start the Node.js Express server:
```bash
node server.js
```

### Step 5: Open in Web Browser
Open your browser and navigate to:
👉 **`http://localhost:3000`**

---

## ✨ Features Available Out-of-the-Box

1. **5-Stage Repurposing Pipeline**:
   - Article ➔ Summary ➔ B2B LinkedIn Post ➔ X/Twitter Thread ➔ Source Facts ➔ Fact Audit
2. **PDF & OCR Upload Support**:
   - Works for plain text, `.docx`, `.txt`, `.md`, standard PDFs, and scanned/image PDFs (`R1.pdf`).
3. **Fact-Drift Audit & Formula Breakdown**:
   - Displays real-time 0–100% Fact Fidelity Score and `Supported / Total Claims × 100` formula.
4. **10 Labelled Benchmark Test Cases**:
   - Click the **Benchmark & Test Suite** tab in the top navigation bar and click **Run Full 10-Case Benchmark Evaluation**.
5. **Security Guardrails**:
   - Intercepts prompt injection attacks (*"ignore previous instructions"*) with a red Security Refusal notification.

---
*Created by Team 24 | Problem 22*
