# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Grade 12 exam planner that generates PDF day planners with color-coded subjects and highlighted exam periods. It creates a comprehensive planner covering both trial exams (September) and final exams (October-November 2025) for South African Grade 12 students.

## Core Architecture

- **Single-file application**: All functionality is contained in `exam_planner.py`
- **Data structures**: Two main exam dictionaries (`trial_exams` and `final_exams`) containing datetime objects for precise scheduling
- **PDF generation**: Uses ReportLab library to create structured PDF output with tables and styling
- **Color coding**: Each subject has a dedicated color defined in `subject_colors` dictionary

## Key Components

### Exam Data Structure
- Exams are organized by subject, then by individual papers
- Each exam entry contains: paper name, start datetime, end datetime
- Supports 7 subjects: Life Orientation, English Home Language, Afrikaans First Additional Language, Mathematics, Life Sciences, Information Technology, Physical Science

### PDF Generation Functions
- `create_exam_summary_page()`: Generates overview tables for both trial and final exams
- `create_daily_planner_pages()`: Creates 2-day-per-page hourly planners (7 AM - 12 AM)
- `get_exam_for_datetime()`: Helper function to check for exams at specific times
- `generate_pdf()`: Main orchestrator function

## Development Commands

### Using uv (recommended)
```bash
# Install dependencies
uv sync

# Run the application
uv run exam-planner

# Run with Python directly
uv run python exam_planner.py

# Format code
uv run black exam_planner.py

# Lint code
uv run ruff exam_planner.py

# Run tests
uv run pytest
```

### Using pip (alternative)
```bash
# Install dependencies
pip install reportlab

# Run directly
python exam_planner.py
```

## Testing
- Test framework: pytest
- Test files should be placed in `tests/` directory
- Run tests with: `uv run pytest`

## Code Style
- Black formatter with line length 88
- Ruff linter configured for Python 3.13
- Target Python version: 3.13+

## Output
The application generates `Grade12_Exam_Day_Planner_2025.pdf` containing:
1. Summary page with complete exam overview tables
2. Daily planner pages from August 26, 2025 to November 30, 2025
3. Color-coded exam blocks matching subject colors
4. Weekend highlighting for easy identification