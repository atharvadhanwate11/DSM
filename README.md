# 🎓 PICT Sem 4 — Student ESE Risk Predictor

A data-driven web application built specifically for **PICT (Pune Institute of Computer Technology) Semester 4 IT students** that predicts which students are at risk of failing their End Semester Examinations (ESE) — **before the exams happen**.

---

## 📌 Problem Statement

Many educational institutions lack data-driven methods to identify at-risk students early. By the time a student fails, it's already too late for meaningful intervention. This project uses **mid-semester data (CIE marks, ISE marks, and attendance)** to predict ESE failure risk, giving teachers the opportunity to intervene **before** the exams.

---

## 🏫 Built For

> **PICT Autonomous — Semester IV (Information Technology)**
> Subject scheme as per PICT 2024-25 curriculum

| Subject | Code | Type |
|---|---|---|
| Advanced Data Structures & Applications (ADSA) | 3403105 | Theory |
| Database & Information Systems (DIS) | 3403106 | Theory |
| Discrete & Statistical Mathematics (DSM) | 3403107 | Theory |
| MDM-2 | 04051X2 | Theory |
| Open Elective II (OE-II) | 04063XX | Theory |
| IP Strategies & Economics (IPSE) | 3409302 | Theory |

---

## 🚀 Features

- 📂 **CSV Upload** — Upload mid-semester student data in one click
- 🔮 **ML Prediction** — Gradient Boosting model predicts Safe vs At Risk for each student
- 💡 **Key Patterns** — Auto-generated insights like attendance trends, backlog impact, weakest subjects
- 📊 **Visual Graphs** — Attendance vs fail rate, backlogs vs fail rate charts
- 🚨 **At-Risk Table** — Highlighted list of students needing immediate attention
- 🕓 **Upload History** — All past uploads stored in database with full detail view
- 🗄️ **SQLite Database** — Persists all predictions and patterns across sessions

---

## 🧠 How It Works

```
Teacher uploads CSV with mid-sem data
            ↓
App calculates avg attendance, midsem scores, risk flags
            ↓
Gradient Boosting model predicts: Safe / At Risk
            ↓
Dashboard shows patterns, graphs, at-risk students
            ↓
Teacher can intervene BEFORE ESE exams
```

The model is trained on historical student data where:
- **Input** → CIE marks, ISE marks, attendance (mid-semester, available before ESE)
- **Output** → Safe (passed all ESE) / At Risk (failed one or more ESE)

---

## 📁 Project Structure

```
DSM Project/
│
├── data/
│   └── sem4_students.csv        ← training data
│
├── templates/
│   └── index.html               ← web frontend
│
├── main.py                      ← data cleaning, EDA, model training
├── app.py                       ← Flask web backend
├── model.pkl                    ← saved trained model (auto-generated)
├── label_encoder.pkl            ← saved label encoder (auto-generated)
├── database.db                  ← SQLite database (auto-generated)
└── requirements.txt
```

---

## 📊 CSV Format

Your CSV must have these columns:

```
student_id, name, roll_no,
ADSA_CIE, ADSA_ISE, ADSA_ESE, ADSA_attendance,
DIS_CIE,  DIS_ISE,  DIS_ESE,  DIS_attendance,
DSM_CIE,  DSM_ISE,  DSM_ESE,  DSM_attendance,
MDM2_CIE, MDM2_ISE, MDM2_ESE, MDM2_attendance,
OE2_ESE, IPSE_ESE,
backlogs, performance_label
```

> **Note:** For prediction on new students, `performance_label` can be left blank or filled with a placeholder. The model only uses CIE, ISE, attendance, and backlogs as input.

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/pict-sem4-risk-predictor.git
cd pict-sem4-risk-predictor
```

### 2. Install dependencies
```bash
pip install flask pandas numpy scikit-learn matplotlib seaborn
```

### 3. Add your data
Place your `sem4_students.csv` inside the `data/` folder.

### 4. Train the model
```bash
python main.py
```
Wait for:
```
Model saved successfully!
Labels: ['At Risk' 'Safe']
```

### 5. Run the web app
```bash
python app.py
```

### 6. Open in browser
```
http://127.0.0.1:5000
```

---

## 🖥️ Usage

1. Open the app in your browser
2. Click **"Choose CSV File"** and upload your mid-semester student data
3. The dashboard will show:
   - How many students are **Safe** vs **At Risk**
   - Subject-wise mid-sem averages
   - Key patterns found in the data
   - Attendance and backlog graphs
   - Full student table with predictions
4. Click **"Upload History"** to view all previous uploads

---

## 📈 Model Details

| Property | Value |
|---|---|
| Algorithm | Gradient Boosting Classifier |
| Library | scikit-learn |
| Features | CIE, ISE, attendance per subject + derived features |
| Target | Safe / At Risk (binary) |
| Train/Test Split | 80% / 20% |
| Accuracy | ~88% on test data |

**Features used for prediction:**
- CIE and ISE marks for ADSA, DIS, DSM, MDM2
- Combined mid-sem score (CIE + ISE) per subject
- Subject-wise attendance
- Average attendance across all theory subjects
- Low attendance flag (< 75%)
- Low CIE flag (< 50% in CIE)
- Number of backlogs from previous semesters

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Web Framework | Flask |
| ML Library | scikit-learn |
| Data Processing | Pandas, NumPy |
| Visualization | Matplotlib, Seaborn |
| Frontend | HTML, CSS, JavaScript |
| Charts | Chart.js |
| Database | SQLite |

---

## 👥 Team

> Made with ❤️ by SY IT — Section 9, PICT Pune
> Academic Year: 2025-26
> Subject: Discrete & Statistical Mathematics (DSM) Project

---

## 📄 License

This project is for academic purposes only.
