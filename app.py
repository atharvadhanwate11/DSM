import os
import pickle
import pandas as pd
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'teacher_secret_key_123' # In production, use os.urandom(24)

model = pickle.load(open('model.pkl', 'rb'))
le    = pickle.load(open('label_encoder.pkl', 'rb'))

# Faculty Credentials (Hardcoded for simplicity)
FACULTY_USER = "teacher"
FACULTY_PASS = "admin123"


# ---- DATABASE ----
def init_db():
    conn = sqlite3.connect('database.db')
    c    = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS uploads (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        filename        TEXT,
        upload_date     TEXT,
        total_students  INTEGER,
        safe_count      INTEGER,
        at_risk_count   INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        upload_id             INTEGER,
        name                  TEXT,
        avg_attendance        REAL,
        backlogs              INTEGER,
        adsa_midsem           INTEGER,
        dis_midsem            INTEGER,
        dsm_midsem            INTEGER,
        mdm2_midsem           INTEGER,
        predicted_performance TEXT,
        FOREIGN KEY (upload_id) REFERENCES uploads(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS patterns (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        upload_id   INTEGER,
        pattern     TEXT,
        FOREIGN KEY (upload_id) REFERENCES uploads(id))''')
    conn.commit()
    conn.close()

init_db()


# ---- HELPERS ----
def process_csv(df):
    # Enforce the requirement: No pre-existing labels allowed for prediction
    if 'performance_label' in df.columns:
        raise ValueError("The uploaded CSV contains a 'performance_label' column. Please upload a file without labels to perform a fresh prediction.")

    df['avg_attendance']      = (df['ADSA_attendance'] + df['DIS_attendance'] +
                                  df['DSM_attendance']  + df['MDM2_attendance']) / 4
    df['low_attendance_flag'] = (df['avg_attendance'] < 75).astype(int)
    df['ADSA_cie_low']        = (df['ADSA_CIE'] < 10).astype(int)
    df['DIS_cie_low']         = (df['DIS_CIE']  < 10).astype(int)
    df['DSM_cie_low']         = (df['DSM_CIE']  < 10).astype(int)
    df['MDM2_cie_low']        = (df['MDM2_CIE'] < 10).astype(int)
    df['ADSA_midsem']         = df['ADSA_CIE'] + df['ADSA_ISE']
    df['DIS_midsem']          = df['DIS_CIE']  + df['DIS_ISE']
    df['DSM_midsem']          = df['DSM_CIE']  + df['DSM_ISE']
    df['MDM2_midsem']         = df['MDM2_CIE'] + df['MDM2_ISE']

    features = [
        'ADSA_CIE',  'DIS_CIE',  'DSM_CIE',  'MDM2_CIE',
        'ADSA_ISE',  'DIS_ISE',  'DSM_ISE',  'MDM2_ISE',
        'ADSA_midsem', 'DIS_midsem', 'DSM_midsem', 'MDM2_midsem',
        'ADSA_attendance', 'DIS_attendance', 'DSM_attendance', 'MDM2_attendance',
        'avg_attendance', 'low_attendance_flag',
        'ADSA_cie_low', 'DIS_cie_low', 'DSM_cie_low', 'MDM2_cie_low',
        'backlogs'
    ]
    df['predicted_performance'] = le.inverse_transform(model.predict(df[features]))
    return df


def generate_patterns(df):
    patterns = []
    total   = len(df)
    at_risk = df[df['predicted_performance'] == 'At Risk']

    patterns.append(f"🚨 {len(at_risk)} out of {total} students ({len(at_risk)/total*100:.0f}%) are predicted to fail one or more ESE exams.")

    low_att = df[df['avg_attendance'] < 75]
    if len(low_att) > 0:
        rate = (low_att['predicted_performance'] == 'At Risk').sum() / len(low_att) * 100
        patterns.append(f"📉 {len(low_att)} students have attendance below 75% — {rate:.0f}% of them are At Risk.")

    good_att = df[df['avg_attendance'] >= 85]
    if len(good_att) > 0:
        rate = (good_att['predicted_performance'] == 'Safe').sum() / len(good_att) * 100
        patterns.append(f"✅ Students with 85%+ attendance have a {rate:.0f}% chance of being Safe.")

    with_bl = df[df['backlogs'] > 0]
    if len(with_bl) > 0:
        rate = (with_bl['predicted_performance'] == 'At Risk').sum() / len(with_bl) * 100
        patterns.append(f"📚 {len(with_bl)} students have previous backlogs — {rate:.0f}% of them are At Risk.")

    subj_avgs = {
        'ADSA': df['ADSA_midsem'].mean(),
        'DIS':  df['DIS_midsem'].mean(),
        'DSM':  df['DSM_midsem'].mean(),
        'MDM2': df['MDM2_midsem'].mean()
    }
    worst = min(subj_avgs, key=subj_avgs.get)
    patterns.append(f"📊 Weakest subject by mid-sem avg: {worst} ({subj_avgs[worst]:.1f}/40) — needs most attention.")

    low_cie = df[(df['ADSA_CIE'] < 10) | (df['DIS_CIE'] < 10) |
                 (df['DSM_CIE']  < 10) | (df['MDM2_CIE'] < 10)]
    if len(low_cie) > 0:
        patterns.append(f"⚠️ {len(low_cie)} students scored below 50% in at least one CIE — early warning sign.")

    return patterns


def save_to_db(filename, df, patterns):
    summary   = df['predicted_performance'].value_counts().to_dict()
    conn      = sqlite3.connect('database.db')
    c         = conn.cursor()
    c.execute('''INSERT INTO uploads (filename, upload_date, total_students, safe_count, at_risk_count)
                 VALUES (?, ?, ?, ?, ?)''', (
        filename,
        datetime.now().strftime('%d %b %Y, %I:%M %p'),
        len(df),
        summary.get('Safe', 0),
        summary.get('At Risk', 0)
    ))
    upload_id = c.lastrowid
    for _, row in df.iterrows():
        c.execute('''INSERT INTO students
            (upload_id, name, avg_attendance, backlogs,
             adsa_midsem, dis_midsem, dsm_midsem, mdm2_midsem, predicted_performance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            upload_id, row['name'], round(row['avg_attendance'], 1),
            int(row['backlogs']), int(row['ADSA_midsem']), int(row['DIS_midsem']),
            int(row['DSM_midsem']), int(row['MDM2_midsem']), row['predicted_performance']
        ))
    for p in patterns:
        c.execute('INSERT INTO patterns (upload_id, pattern) VALUES (?, ?)', (upload_id, p))
    conn.commit()
    conn.close()
    return upload_id


# ---- ROUTES ----
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        if data.get('username') == FACULTY_USER and data.get('password') == FACULTY_PASS:
            session['logged_in'] = True
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Invalid credentials'})
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        file = request.files['csv_file']
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Please upload a CSV file.'})

        df        = pd.read_csv(file)
        df        = process_csv(df)
        patterns  = generate_patterns(df)
        upload_id = save_to_db(file.filename, df, patterns)
        summary   = df['predicted_performance'].value_counts().to_dict()

        cols      = ['name', 'avg_attendance', 'backlogs',
                     'ADSA_midsem', 'DIS_midsem', 'DSM_midsem',
                     'MDM2_midsem', 'predicted_performance']

        students  = df[cols].copy()
        students['avg_attendance'] = students['avg_attendance'].round(1)

        at_risk   = students[students['predicted_performance'] == 'At Risk'].copy()

        bins   = [0, 50, 60, 75, 85, 100]
        labels = ['0-50','51-60','61-75','76-85','86-100']
        df['att_bucket'] = pd.cut(df['avg_attendance'], bins=bins, labels=labels)
        att_graph = df.groupby('att_bucket', observed=True)['predicted_performance'].apply(
            lambda x: (x == 'At Risk').sum() / len(x) * 100).round(1).to_dict()
        att_graph = {str(k): v for k, v in att_graph.items()}

        backlog_graph = df.groupby('backlogs')['predicted_performance'].apply(
            lambda x: (x == 'At Risk').sum() / len(x) * 100).round(1).to_dict()
        backlog_graph = {str(k): v for k, v in backlog_graph.items()}

        subject_avgs = {
            'ADSA': round(df['ADSA_midsem'].mean(), 1),
            'DIS':  round(df['DIS_midsem'].mean(), 1),
            'DSM':  round(df['DSM_midsem'].mean(), 1),
            'MDM2': round(df['MDM2_midsem'].mean(), 1)
        }

        return jsonify({
            'upload_id':     upload_id,
            'students':      students.to_dict(orient='records'),
            'at_risk':       at_risk.to_dict(orient='records'),
            'summary':       summary,
            'patterns':      patterns,
            'att_graph':     att_graph,
            'backlog_graph': backlog_graph,
            'subject_avgs':  subject_avgs,
            'total':         len(df)
        })
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/history')
def history():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    conn = sqlite3.connect('database.db')
    c    = conn.cursor()
    c.execute('SELECT * FROM uploads ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return jsonify({'uploads': [
        {'id': r[0], 'filename': r[1], 'date': r[2],
         'total': r[3], 'safe_count': r[4], 'at_risk_count': r[5]}
        for r in rows]})


@app.route('/history/<int:upload_id>')
def history_detail(upload_id):
    conn = sqlite3.connect('database.db')
    c    = conn.cursor()
    c.execute('SELECT * FROM uploads WHERE id = ?', (upload_id,))
    u = c.fetchone()
    c.execute('SELECT * FROM students WHERE upload_id = ?', (upload_id,))
    students = c.fetchall()
    c.execute('SELECT pattern FROM patterns WHERE upload_id = ?', (upload_id,))
    patterns = [p[0] for p in c.fetchall()]
    conn.close()

    students_list = [{'name': s[2], 'avg_attendance': s[3], 'backlogs': s[4],
                      'ADSA_midsem': s[5], 'DIS_midsem': s[6],
                      'DSM_midsem': s[7], 'MDM2_midsem': s[8],
                      'predicted_performance': s[9]} for s in students]

    return jsonify({
        'upload':   {'id': u[0], 'filename': u[1], 'date': u[2],
                     'total': u[3], 'safe_count': u[4], 'at_risk_count': u[5]},
        'students': students_list,
        'at_risk':  [s for s in students_list if s['predicted_performance'] == 'At Risk'],
        'patterns': patterns
    })


@app.route('/history/delete/<int:upload_id>', methods=['DELETE'])
def delete_record(upload_id):
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('DELETE FROM students WHERE upload_id = ?', (upload_id,))
        c.execute('DELETE FROM patterns WHERE upload_id = ?', (upload_id,))
        c.execute('DELETE FROM uploads WHERE id = ?', (upload_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/history/delete_all', methods=['DELETE'])
def delete_all():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('DELETE FROM students')
        c.execute('DELETE FROM patterns')
        c.execute('DELETE FROM uploads')
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True)