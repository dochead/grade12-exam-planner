# Grade 12 Exam Planner

A Python script to generate PDF day planners for Grade 12 exam schedules with color-coded subjects and highlighted exam periods.

## Features

- **Comprehensive Exam Coverage**: Supports both trial exams (September) and final exams (October-November)
- **Color-Coded Subjects**: Each subject has its own color for easy identification
- **Summary Page**: Overview of all exams in organized tables
- **Daily Planner**: Two days per page format with hourly time slots (7 AM - 12 AM)
- **Exam Highlighting**: Exam blocks are highlighted in subject-specific colors
- **Weekend Highlighting**: Weekends are highlighted for easy identification

## Supported Subjects

- Life Orientation (L.O.)
- English Home Language
- Afrikaans First Additional Language
- Mathematics
- Life Sciences
- Information Technology
- Physical Science

## Installation

### Using uv (recommended)

```bash
uv sync
```

### Using pip

```bash
pip install reportlab
```

## Usage

### With uv

```bash
uv run exam-planner
```

### Direct Python execution

```bash
python exam_planner.py
```

## Output

The script generates a PDF file named `Grade12_Exam_Day_Planner_2025.pdf` containing:

1. **Summary Page**: Complete overview of all exams with dates and times
2. **Daily Planner Pages**: Detailed day-by-day schedule from August 26, 2025, to November 30, 2025

## Exam Schedule Overview

### Trial Exams (September 2025)
- 15 exams across 7 subjects
- Runs throughout September 2025

### Final Exams (October-November 2025)
- 16 exams across 7 subjects
- National Senior Certificate examinations

## Requirements

- Python 3.13+
- reportlab library

## License

MIT License