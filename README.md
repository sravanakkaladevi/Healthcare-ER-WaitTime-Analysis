# Healthcare ER Wait Time Analytics Dashboard

## Project Overview
This project analyzes Emergency Room (ER) patient data to understand wait times, admissions, department workload, and patient demographics. The main analysis is presented in Power BI, and the repository also includes Python scripts for visual reporting and basic model evaluation.

## Tools Used
- Power BI
- Excel / CSV data source
- Python
- Data Visualization
- Exploratory Data Analysis

## Key Metrics
- Total Patients: 9,216
- Average Wait Time: 35.26 minutes
- Maximum Wait Time: 60 minutes
- Admission Rate: 50.04%
- Highest Referred Department: General Practice

## Dashboard Insights
- General Practice is the busiest referred department, while many visits also arrive with no referral.
- Patient distribution across genders is broadly balanced.
- Adult and Young Adult groups represent the largest share of ER visits.
- Admissions are almost evenly split between admitted and non-admitted patients.
- Wait times are concentrated around the mid-range, with an average just over 35 minutes.

## Dashboard Preview
![ER Dashboard](Images/Dashboard.png)

## Python Visual Report
This project includes a lightweight Python visual generator that recreates the main Power BI dashboard visuals from the ER dataset.

Run:
```powershell
python scripts\generate_visuals.py
```

Generated visuals:
- `visuals/index.html`
- `visuals/er_patient_visits_trend_line.svg`
- `visuals/patients_by_department_bar.svg`
- `visuals/patients_by_gender_donut.svg`
- `visuals/patient_age_distribution_bar.svg`

## Accuracy Testing
You can also run the Python evaluation script to measure model performance on admission prediction and wait-time prediction.

Run:
```powershell
python scripts\evaluate_accuracy.py
```

## Project Files
- Dataset: `Dataset/Hospital ER_Data.csv`
- Power BI dashboard: `PowerBI_Dashboard/ER_WaitTime_Dashboard.pbix`
- Visual report generator: `scripts/generate_visuals.py`
- Accuracy evaluator: `scripts/evaluate_accuracy.py`
