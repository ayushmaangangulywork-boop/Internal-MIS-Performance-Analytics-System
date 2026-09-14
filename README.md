

## Jewellery Design MIS & Performance Analytics System

A Python-based internal MIS and performance analytics system developed to automate recurring jewellery design reporting, KPI analysis, performance tracking, and management reporting.

---

## Overview

MAWSIM GOLD converts operational jewellery-design data into structured MIS, performance analytics, management insights, and reporting outputs.

The system covers:

- Monthly MIS reporting
- Weekly MIS reporting
- Designer performance analysis
- Target vs. achievement analysis
- Project and product analysis
- Workload and contribution analysis
- Management insights and recommendations
- Executive summaries
- Individual performance reports
- Excel and PDF reporting

---

## Business Problem

Recurring MIS reporting required repeated data preparation, KPI calculations, performance analysis, and report generation.

Management also needed visibility beyond basic totals, including:

- Target achievement
- Designer performance
- Performance gaps
- Project contribution
- Product contribution
- Workload distribution
- Areas requiring management attention

The objective was to make reporting more consistent, repeatable, and decision-oriented.

---

## Solution

I developed and implemented a modular Python/Pandas MIS system that follows:

```text
Operational Data
      ↓
Data Processing
      ↓
KPI & Performance Analysis
      ↓
Business Insights
      ↓
Management Reports
```

The analytics logic is separated from the reporting modules so that the same business calculations can be reused across different reports.

--

## Key Analytics

### Performance
- Target vs. achievement
- Designer performance
- Team-level performance
- Below-target identification
- Contribution analysis

### Operational Analysis
- Project contribution
- Product contribution
- Collection analysis
- Location analysis
- Work-type analysis
- Workload distribution
- Pareto/concentration analysis

### Management Intelligence
- Automated performance observations
- Priority-based insights
- Action-required identification
- Management recommendations

---

## Reports & Outputs

Running the main application generates the available MIS and reporting outputs.

The repository also contains sample generated outputs for exploration.

Typical outputs include:

- Monthly MIS
- Weekly MIS
- CAD executive report
- Manual department executive report
- Individual designer reports
- Excel MIS outputs
- Management summaries
- Analytical charts and insights

---

## Project Structure

```text
Internal-MIS-Performance-Analytics-System/
│
├── main.py
├── analytics.py
├── dashboard.py
├── data_reader.py
├── excel_export.py
├── executive_report.py
├── individual_reports.py
├── insight_blocks.py
├── pdf_styles.py
├── reports.py
├── scorecards.py
├── time_intelligence.py
├── weekly_report.py
│
├── CAD REPORT JULY 2026.xlsx
├── MIS_CAD_OUTPUT.pdf
├── Individual_CAD_Aditya_Sengupta_SAMPLE.pdf
│
├── requirements.txt
└── README.md

---

## Technical Architecture

The system is organized into separate modules for:

**Data → Analytics → Insights → Reporting**

This allows individual components to be maintained and reused without putting the entire reporting workflow into one script.

The weekly MIS also uses the existing analytics engine after filtering the relevant weekly data, while keeping the monthly reporting logic independent.

---

## Technology Stack

- Python
- Pandas
- NumPy
- Excel
- OpenPyXL
- XlsxWriter
- ReportLab
- Matplotlib
- Git / GitHub

---

## How to Run

### 1. Clone the repository

```bash
git clone <repository-url>
cd MAWSIM-GOLD
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

**Windows**

```bash
venv\Scripts\activate
```

**macOS / Linux**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the system

```bash
python main.py
```

The application processes the available input data and generates the configured MIS/reporting outputs.

---

## My Contribution

I developed and implemented this system as part of my professional operations role.

My contribution included:

- Identifying recurring MIS and reporting requirements
- Designing the reporting workflow
- Structuring operational data for analysis
- Developing Python/Pandas analytics
- Implementing KPI and performance calculations
- Automating recurring report generation
- Developing management insights
- Building Excel/PDF reporting outputs
- Improving the reporting process based on operational requirements

---

## Business Value

The system was developed to:

- Reduce repetitive manual reporting work
- Standardize recurring calculations
- Improve performance visibility
- Identify performance gaps more quickly
- Reduce manual analytical effort
- Provide management with actionable information

---

### Reports & Outputs

The system generates both management-level and individual performance reports.

- **Total / Executive MIS Report** — consolidated management report covering overall KPIs, performance analysis, workload, productivity, targets vs achievement, and key management insights.
<img width="922" height="650" alt="image" src="https://github.com/user-attachments/assets/8e40a8e9-3ebd-4f50-8e7a-550cf141c62d" />



- **Sample Individual Designer Report** — individual performance report providing a detailed view of a designer's productivity, workload, performance metrics, and related insights.
<img width="925" height="660" alt="image" src="https://github.com/user-attachments/assets/7843a4c8-47a0-48d0-a0db-cd3566eb7b2a" />


Sample PDF reports are included in the repository files so reviewers can directly explore the generated outputs.

> The repository includes representative sample reports generated by the system.

## Explore the Project

For a deeper understanding, explore:

- `analytics.py` — analytical and KPI logic
- `reports.py` — MIS reporting
- `executive_report.py` — executive summaries
- `weekly_report.py` — weekly MIS
- `individual_reports.py` — individual performance reporting
- `insight_blocks.py` — management insights
- `excel_export.py` — Excel output generation
- `OUTPUT/` — generated report examples

---

## Project Context

MAWSIM GOLD was developed and implemented as an internal business solution to address actual operational reporting and performance-analysis requirements.

The repository contains the cleared version intended for portfolio and technical demonstration.

---

## Skills Demonstrated

**Operations Analysis · MIS Reporting · Business Analytics · KPI Design · Performance Analysis · Process Improvement · Python/Pandas · Reporting Automation · Management Reporting · Data Analysis**
```
