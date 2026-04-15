import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

df = pd.read_csv('data/sem4_students.csv')

# ---- DATA CLEANING ----
print("Missing values:")
print(df.isnull().sum())
print("\nDuplicate rows:", df.duplicated().sum())
print("\nMarks out of range check:")
print("ADSA_CIE > 20 :", (df['ADSA_CIE'] > 20).sum())
print("ADSA_ISE > 20 :", (df['ADSA_ISE'] > 20).sum())
print("ADSA_ESE > 60 :", (df['ADSA_ESE'] > 60).sum())
print("Attendance <0 or >100:", ((df['ADSA_attendance'] < 0) | (df['ADSA_attendance'] > 100)).sum())

# ---- FEATURE ENGINEERING ----
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

print("\nLabel distribution:")
print(df['performance_label'].value_counts())

# ---- EDA ----
plt.figure(figsize=(8,5))
sns.countplot(data=df, x='performance_label', hue='performance_label',
              palette={'Safe':'#22c55e','At Risk':'#ef4444'}, legend=False)
plt.title('Safe vs At Risk Distribution')
plt.tight_layout()
plt.savefig('graph1_label_distribution.png')
plt.close()

plt.figure(figsize=(8,5))
sns.boxplot(data=df, x='performance_label', y='avg_attendance', hue='performance_label',
            palette={'Safe':'#22c55e','At Risk':'#ef4444'}, legend=False)
plt.title('Attendance vs Label')
plt.tight_layout()
plt.savefig('graph2_attendance_vs_label.png')
plt.close()

plt.figure(figsize=(8,5))
sns.boxplot(data=df, x='performance_label', y='ADSA_midsem', hue='performance_label',
            palette={'Safe':'#22c55e','At Risk':'#ef4444'}, legend=False)
plt.title('ADSA Mid-Sem Score vs Label')
plt.tight_layout()
plt.savefig('graph3_adsa_midsem_vs_label.png')
plt.close()

plt.figure(figsize=(8,5))
sns.boxplot(data=df, x='backlogs', y='avg_attendance', hue='performance_label',
            palette={'Safe':'#22c55e','At Risk':'#ef4444'})
plt.title('Backlogs vs Attendance by Label')
plt.tight_layout()
plt.savefig('graph4_backlogs_attendance.png')
plt.close()

plt.figure(figsize=(14,10))
numeric_cols = df.select_dtypes(include='number').drop(columns=['roll_no'])
sns.heatmap(numeric_cols.corr(), annot=True, fmt='.1f', cmap='coolwarm')
plt.title('Correlation Heatmap')
plt.tight_layout()
plt.savefig('graph5_heatmap.png')
plt.close()

print("EDA graphs saved!")

# ---- ML MODEL ----
features = [
    'ADSA_CIE',  'DIS_CIE',  'DSM_CIE',  'MDM2_CIE',
    'ADSA_ISE',  'DIS_ISE',  'DSM_ISE',  'MDM2_ISE',
    'ADSA_midsem', 'DIS_midsem', 'DSM_midsem', 'MDM2_midsem',
    'ADSA_attendance', 'DIS_attendance', 'DSM_attendance', 'MDM2_attendance',
    'avg_attendance', 'low_attendance_flag',
    'ADSA_cie_low', 'DIS_cie_low', 'DSM_cie_low', 'MDM2_cie_low',
    'backlogs'
]

X = df[features]
y = df['performance_label']

le = LabelEncoder()
y_encoded = le.fit_transform(y)
print("\nLabel mapping:", dict(zip(le.classes_, le.transform(le.classes_))))

X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)

print(f"Training samples : {len(X_train)}")
print(f"Testing  samples : {len(X_test)}")

model = GradientBoostingClassifier(n_estimators=200, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

print("\nAccuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred,
      labels=list(range(len(le.classes_))),
      target_names=le.classes_, zero_division=0))

plt.figure(figsize=(6,5))
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=le.classes_, yticklabels=le.classes_)
plt.title('Confusion Matrix')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.tight_layout()
plt.savefig('graph6_confusion_matrix.png')
plt.close()

plt.figure(figsize=(10,8))
importance = pd.Series(model.feature_importances_, index=features)
importance.sort_values().plot(kind='barh', color='steelblue')
plt.title('Feature Importance')
plt.xlabel('Importance Score')
plt.tight_layout()
plt.savefig('graph7_feature_importance.png')
plt.close()

# ---- SAVE MODEL ----
with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)
with open('label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)

print("\nModel saved successfully!")
print("Labels:", le.classes_)