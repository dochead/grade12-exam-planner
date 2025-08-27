#!/usr/bin/env python3
"""
Grade 12 Exam Day Planner Generator
Creates a PDF planner with exam schedules highlighted
"""

from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import json
import click

def load_exam_data(filename="custom_data.json"):
    """Load exam timetable data from JSON file and return it in current format"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            exam_timetable = json.load(f)
        return exam_timetable
    except FileNotFoundError:
        click.echo(f"Error: JSON file '{filename}' not found.", err=True)
        click.echo("Please ensure the exam data JSON file exists.", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON in '{filename}': {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error loading '{filename}': {e}", err=True)
        raise click.Abort()

# Custom colors
dark_grey = colors.Color(0.3, 0.3, 0.3)  # Dark grey for text
muted_grey = colors.Color(0.9, 0.9, 0.9)  # Muted grey for weekends


def build_runtime_structures(exam_timetable):
    """Build in-memory structures from current JSON for rendering (colors, abbreviations, emojis, and parsed datetimes)."""
    trial_exams = {}
    final_exams = {}
    subject_colors = {}
    subject_abbreviations = {}
    subject_emojis = {}

    for subject_name, subject_data in exam_timetable.get("subjects", {}).items():
        # Subject attributes
        color_triplet = subject_data.get("color", [1, 1, 1])
        subject_colors[subject_name] = colors.Color(*color_triplet)
        subject_abbreviations[subject_name] = subject_data.get("abbreviation", subject_name)
        subject_emojis[subject_name] = subject_data.get("emoji", "")

        # Exams: parse ISO datetimes to datetime objects expected by renderer
        trial_exams[subject_name] = []
        for exam in subject_data.get("exam_types", {}).get("trial", {}).get("exams", []):
            trial_exams[subject_name].append({
                "paper": exam.get("paper", ""),
                "start": datetime.fromisoformat(exam["start_datetime"]),
                "end": datetime.fromisoformat(exam["end_datetime"]),
            })

        final_exams[subject_name] = []
        for exam in subject_data.get("exam_types", {}).get("final", {}).get("exams", []):
            final_exams[subject_name].append({
                "paper": exam.get("paper", ""),
                "start": datetime.fromisoformat(exam["start_datetime"]),
                "end": datetime.fromisoformat(exam["end_datetime"]),
            })

    return trial_exams, final_exams, subject_colors, subject_abbreviations, subject_emojis

# Register both text and emoji fonts
def register_fonts():
    """Register Public Sans for text and Noto Color Emoji for emojis"""
    fonts = {'text_font': 'Helvetica', 'emoji_font': 'Helvetica'}
    
    try:
        # Try to find and register PublicSans-VariableFont_wght.ttf
        public_sans_paths = [
            './PublicSans-SemiBold.ttf',  # Current directory
            '/System/Library/Fonts/PublicSans-SemiBold.ttf',
            '/Library/Fonts/PublicSans-SemiBold.ttf',
            os.path.expanduser('~/Downloads/PublicSans-SemiBold.ttf'),
        ]
        
        for path in public_sans_paths:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont('PublicSansFont', path))
                    fonts['text_font'] = 'PublicSansFont'
                    print(f"Registered text font: {path}")
                    break
                except Exception as e:
                    print(f"Failed to register Public Sans at {path}: {e}")
                    continue
        
        # Try to find and register NotoColorEmoji-Regular.ttf
        noto_emoji_paths = [
            './NotoEmoji-Regular.ttf',  # Current directory
            '/System/Library/Fonts/NotoEmoji-Regular.ttf',
            '/Library/Fonts/NotoEmoji-Regular.ttf',
            os.path.expanduser('~/Downloads/NotoEmoji-Regular.ttf'),
        ]
        
        for path in noto_emoji_paths:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont('NotoEmojiFont', path))
                    fonts['emoji_font'] = 'NotoEmojiFont'
                    print(f"Registered emoji font: {path}")
                    break
                except Exception as e:
                    print(f"Failed to register Noto Color Emoji at {path}: {e}")
                    continue
        
        return fonts
        
    except Exception as e:
        print(f"Font registration failed: {e}")
        return fonts

# Register both fonts
FONTS = register_fonts()
TEXT_FONT = FONTS['text_font']
EMOJI_FONT = FONTS['emoji_font']


def _format_duration(delta: timedelta) -> str:
    total_minutes = int(delta.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "0m"


def create_exam_paragraph(subject, exam, subject_emojis, subject_abbreviations):
    """Create a paragraph with emoji and text using different fonts, including time window and duration"""
    emoji = subject_emojis[subject]
    subject_abbrev = subject_abbreviations[subject]
    paper = exam['paper']
    start = exam['start']
    end = exam['end']
    duration = end - start
    time_str = f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')} ({_format_duration(duration)})"

    # Create paragraph with mixed fonts - emoji font for emoji, bold text font for text
    content = (
        f'<font name="{EMOJI_FONT}">{emoji}</font> '
        f'<font name="{TEXT_FONT}"><b>{subject_abbrev}<br/>{paper}</b><br/>'
        f'{time_str}</font>'
    )

    # Create paragraph style
    style = ParagraphStyle(
        'ExamStyle',
        fontSize=9,  # Increased from 7 to 9
        textColor=dark_grey,
        alignment=TA_CENTER,
        leading=10  # Increased leading proportionally
    )

    return Paragraph(content, style)

def create_exam_summary_page(doc_elements, exam_timetable, legacy_data):
    """Create the first page with exam summary tables side by side"""
    trial_exams, final_exams, subject_colors, subject_abbreviations, subject_emojis = legacy_data
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER
    )

    # Title from metadata
    title = Paragraph(exam_timetable['metadata']['title'], title_style)
    doc_elements.append(title)
    doc_elements.append(Spacer(1, 12))

    # Sort all exams by date
    trial_exam_list = []
    for subject, exams in trial_exams.items():
        for exam in exams:
            trial_exam_list.append((subject, exam))
    trial_exam_list.sort(key=lambda x: x[1]['start'])

    final_exam_list = []
    for subject, exams in final_exams.items():
        for exam in exams:
            final_exam_list.append((subject, exam))
    final_exam_list.sort(key=lambda x: x[1]['start'])

    # Create trial exams table
    trial_data = [['Subject', 'Paper', 'Date', 'Time']]
    trial_row = 1
    trial_subject_rows = {}
    for subject, exam in trial_exam_list:
        date_str = exam['start'].strftime('%a, %b %d')
        time_str = f"{exam['start'].strftime('%H:%M')}-{exam['end'].strftime('%H:%M')}"
        trial_data.append([subject_abbreviations[subject], exam['paper'], date_str, time_str])
        if subject not in trial_subject_rows:
            trial_subject_rows[subject] = []
        trial_subject_rows[subject].append(trial_row)
        trial_row += 1

    # Create final exams table
    final_data = [['Subject', 'Paper', 'Date', 'Time']]
    final_row = 1
    final_subject_rows = {}
    for subject, exam in final_exam_list:
        date_str = exam['start'].strftime('%a, %b %d')
        time_str = f"{exam['start'].strftime('%H:%M')}-{exam['end'].strftime('%H:%M')}"
        final_data.append([subject_abbreviations[subject], exam['paper'], date_str, time_str])
        if subject not in final_subject_rows:
            final_subject_rows[subject] = []
        final_subject_rows[subject].append(final_row)
        final_row += 1

    # Table dimensions for landscape layout - 5mm (~0.2 inch) spacing between tables
    available_width = 10.2 * inch
    spacing = 0.2 * inch  # About 5mm spacing
    table_width = (available_width - spacing) / 2
    
    # Custom column widths: balanced for all content
    subject_col_width = table_width * 0.4   # 40% for subject column
    paper_col_width = table_width * 0.25    # 25% for paper column
    date_col_width = table_width * 0.2      # 20% for date column  
    time_col_width = table_width * 0.15     # 15% for time column

    col_widths = [subject_col_width, paper_col_width, date_col_width, time_col_width]
    trial_table = Table(trial_data, colWidths=col_widths)
    final_table = Table(final_data, colWidths=col_widths)

    # Common table style with smaller font and dark grey text
    table_style_base = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, 1), (-1, -1), dark_grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), TEXT_FONT),  # Use text font for summary content
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, dark_grey)
    ]

    # Apply styling and subject colors to trial table
    trial_table_style = table_style_base.copy()
    for subject, rows in trial_subject_rows.items():
        for row in rows:
            trial_table_style.append(('BACKGROUND', (0, row), (0, row), subject_colors[subject]))

    # Apply styling and subject colors to final table
    final_table_style = table_style_base.copy()
    for subject, rows in final_subject_rows.items():
        for row in rows:
            final_table_style.append(('BACKGROUND', (0, row), (0, row), subject_colors[subject]))

    trial_table.setStyle(TableStyle(trial_table_style))
    final_table.setStyle(TableStyle(final_table_style))

    # Create side-by-side layout with titles using top-level exam display names
    trial_title = Paragraph(f"<b>{exam_timetable['exams']['trial']['display_name']}</b>", styles['Heading3'])
    final_title = Paragraph(f"<b>{exam_timetable['exams']['final']['display_name']}</b>", styles['Heading3'])

    # Create a table to hold both tables side by side
    side_by_side_data = [
        [trial_title, final_title],
        [trial_table, final_table]
    ]

    side_by_side_table = Table(side_by_side_data, colWidths=[table_width, table_width], hAlign='CENTER')
    side_by_side_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('RIGHTPADDING', (0, 0), (0, -1), 0.1*inch),  # 5mm spacing
        ('LEFTPADDING', (1, 0), (1, -1), 0.1*inch),   # 5mm spacing
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
    ]))

    doc_elements.append(side_by_side_table)
    doc_elements.append(PageBreak())

def get_exam_for_datetime(dt, trial_exams, final_exams):
    """Check if there's an exam at the given datetime"""
    # Check trial exams first
    for subject, exams in trial_exams.items():
        for exam in exams:
            if exam['start'].date() == dt.date() and exam['start'].hour <= dt.hour < exam['end'].hour:
                return subject, exam
    
    # Then check final exams
    for subject, exams in final_exams.items():
        for exam in exams:
            if exam['start'].date() == dt.date() and exam['start'].hour <= dt.hour < exam['end'].hour:
                return subject, exam
                
    return None, None

def create_daily_planner_pages(doc_elements, exam_timetable, legacy_data):
    """Create daily planner pages with 4 days per page"""
    trial_exams, final_exams, subject_colors, subject_abbreviations, subject_emojis = legacy_data
    start_date = datetime.fromisoformat(exam_timetable['metadata']['planner_start_date'])
    end_date = datetime.fromisoformat(exam_timetable['metadata']['planner_end_date'])
    current_date = start_date

    styles = getSampleStyleSheet()

    while current_date <= end_date:
        # Create a page with up to 4 days
        days = []
        for i in range(4):
            if current_date + timedelta(days=i) <= end_date:
                days.append(current_date + timedelta(days=i))
            else:
                break

        # Page title
        if len(days) == 4:
            page_title = f"{days[0].strftime('%A, %b %d')} - {days[3].strftime('%A, %b %d, %Y')}"
        else:
            page_title = f"{days[0].strftime('%A, %b %d')} - {days[-1].strftime('%A, %b %d, %Y')}"

        title_para = Paragraph(f"<b>{page_title}</b>", styles['Heading1'])
        doc_elements.append(title_para)
        doc_elements.append(Spacer(1, 12))

        # Create table data for all days
        headers = ['Time'] + [day.strftime('%a, %b %d') for day in days]
        table_data = [headers]

        # Precompute mapping of day index -> list of (subject, exam)
        day_exams = {i: [] for i in range(len(days))}
        for subj, exams in trial_exams.items():
            for ex in exams:
                for i, d in enumerate(days):
                    if ex['start'].date() == d.date():
                        day_exams[i].append((subj, ex))
        for subj, exams in final_exams.items():
            for ex in exams:
                for i, d in enumerate(days):
                    if ex['start'].date() == d.date():
                        day_exams[i].append((subj, ex))
        # sort exams per day by start time
        for i in day_exams:
            day_exams[i].sort(key=lambda se: se[1]['start'])

        for hour in range(7, 24):  # 7 AM to 11 PM
            if hour == 12:
                time_str = "12:00 PM"
            elif hour > 12:
                time_str = f"{hour-12}:00 PM"
            else:
                time_str = f"{hour}:00 AM"

            # Initialize row with time label and placeholders
            row_data = [time_str] + ["" for _ in days]
            table_data.append(row_data)

        # Now populate cells and create spans for qualified items
        first_hour = 7
        def needs_merge(ex):
            start, end = ex['start'], ex['end']
            duration = end - start
            crosses_hour = start.hour != end.hour
            over_hour = duration >= timedelta(hours=1)
            # merge if > 1 hour or crosses hour boundary
            return over_hour or crosses_hour

        table_style_spans = []
        table_style_backgrounds = []

        for day_idx, se_list in day_exams.items():
            col = 1 + day_idx
            for subject, exam in se_list:
                start = exam['start']
                end = exam['end']
                # compute start/end row indices within table_data (account for header row)
                start_row = 1 + (start.hour - first_hour)
                start_row = max(1, start_row)
                end_row = 1 + (end.hour - first_hour)
                # If exam ends exactly on an hour and doesn't cross into the next hour, we still want merge only if duration >=1h
                # Ensure end_row at least start_row
                if end_row < start_row:
                    end_row = start_row

                # Place content only in the start row
                if 1 <= start_row < len(table_data):
                    table_data[start_row][col] = create_exam_paragraph(subject, exam, subject_emojis, subject_abbreviations)

                # Decide if we should span across rows
                if needs_merge(exam):
                    # If the exam crosses into the next hour with minutes, include the end hour row as part of span
                    if start.hour != end.hour and (end.minute > 0 or start.minute > 0 or (end - start) >= timedelta(hours=1)):
                        # include the end hour row as a visual block
                        pass  # end_row already points to the end hour row
                    # Apply SPAN from start_row to end_row (clamp within table bounds)
                    span_end = max(start_row, min(end_row, len(table_data) - 1))
                    table_style_spans.append(('SPAN', (col, start_row), (col, span_end)))
                    # Background over the spanned area
                    table_style_backgrounds.append(('BACKGROUND', (col, start_row), (col, span_end), subject_colors[subject]))
                else:
                    # Not merged: just color the single cell
                    table_style_backgrounds.append(('BACKGROUND', (col, start_row), (col, start_row), subject_colors[subject]))

        # Create the table with dynamic column widths for landscape orientation
        # Available width in landscape A4 is about 10.2 inches (11.7 - 1.5 for margins)
        available_width = 10.2 * inch
        time_col_width = 0.8 * inch
        day_col_width = (available_width - time_col_width) / len(days)

        col_widths = [time_col_width] + [day_col_width] * len(days)
        day_table = Table(table_data, colWidths=col_widths)

        # Base table style - no font settings for content since we use Paragraph objects
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # Increased header font size from 7 to 9
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('GRID', (0, 0), (-1, -1), 1, dark_grey),
        ]

        # Highlight weekends (time blocks only, not headers)
        for idx, day in enumerate(days):
            if day.weekday() >= 5:  # Saturday or Sunday
                table_style.append(('BACKGROUND', (idx + 1, 1), (idx + 1, -1), muted_grey))

        # Apply computed spans and backgrounds for exams
        for span in table_style_spans:
            table_style.append(span)
        for bg in table_style_backgrounds:
            table_style.append(bg)

        day_table.setStyle(TableStyle(table_style))
        doc_elements.append(day_table)

        # Move to next set of days
        current_date += timedelta(days=4)

        # Add page break if not the last page
        if current_date <= end_date:
            doc_elements.append(PageBreak())

# ===================== Study Plan (with ADHD-aware constraints) =====================
from collections import defaultdict

# Multipliers
LEVELS_THEORY = {"none": 0.0, "low": 1.0, "medium": 2.0, "high": 3.0}
LEVELS_PRACTICE = {"none": 0.0, "low": 1.0, "medium": 1.5, "high": 2.0}
LEVELS_EFFORT = {"none": 1.0, "low": 1.0, "medium": 1.2, "high": 1.5}

DEFAULT_SESSION_MIN = 45  # ADHD-friendly shorter minimum session (minutes)
DEFAULT_SESSION_MAX = 75  # keep under 90 by default
DEFAULT_BREAK_MINUTES = 15

HARD_START_HOUR = 9   # do not schedule before 09:00
HARD_END_HOUR = 23    # do not schedule after 23:00


def _parse_time_str(hhmm: str):
    hh, mm = map(int, hhmm.split(":"))
    return hh, mm


def _get_config(exam_timetable):
    meta = exam_timetable.get("metadata", {})
    # Defaults
    cfg = {
        "daily_start": (9, 0),
        "daily_end": (21, 30),
        "per_day_max_hours": 10.0,  # legacy; will fall back to study_time_per_day if provided
        "study_time_per_day": None,
        "adhd_frontload": True,
        "weekend_extra_hours": 2.0,    # add hours to capacity on Sat/Sun
        "free_day_extra_hours": 2.0,   # add hours if no exam/tuition that day
        "tuition_blocks": [],          # list of {start_datetime, end_datetime}
        "break_minutes": DEFAULT_BREAK_MINUTES,
        "per_subject_daily_cap_hours": 3.0,
        # Day-before priority sessions
        "day_before_sessions_default": 2,
        "day_before_sessions_high_effort": 4,
    }
    # Optional overrides in JSON
    if "daily_start_time" in meta:
        cfg["daily_start"] = _parse_time_str(meta["daily_start_time"])
    if "daily_end_time" in meta:
        cfg["daily_end"] = _parse_time_str(meta["daily_end_time"])
    if "study_time_per_day" in meta:
        cfg["study_time_per_day"] = float(meta["study_time_per_day"]) 
    if "per_day_max_hours" in meta:
        cfg["per_day_max_hours"] = float(meta["per_day_max_hours"]) 
    if "adhd_frontload" in meta:
        cfg["adhd_frontload"] = bool(meta["adhd_frontload"]) 
    if "weekend_extra_hours" in meta:
        cfg["weekend_extra_hours"] = float(meta["weekend_extra_hours"]) 
    if "free_day_extra_hours" in meta:
        cfg["free_day_extra_hours"] = float(meta["free_day_extra_hours"]) 
    if "tuition_classes" in meta:
        # array of {start_datetime, end_datetime}
        for t in meta.get("tuition_classes", []):
            try:
                cfg["tuition_blocks"].append((datetime.fromisoformat(t["start_datetime"]), datetime.fromisoformat(t["end_datetime"])) )
            except Exception:
                pass
    if "break_minutes" in meta:
        cfg["break_minutes"] = int(meta["break_minutes"]) 
    if "per_subject_daily_cap_hours" in meta:
        cfg["per_subject_daily_cap_hours"] = float(meta["per_subject_daily_cap_hours"]) 

    # Clamp to hard bounds 09:00–23:00
    s_h, s_m = cfg["daily_start"]
    e_h, e_m = cfg["daily_end"]
    s_h = max(s_h, HARD_START_HOUR)
    e_h = min(e_h, HARD_END_HOUR)
    cfg["daily_start"] = (s_h, s_m if s_h > HARD_START_HOUR else 0)
    cfg["daily_end"] = (e_h, e_m if e_h < HARD_END_HOUR else 0)
    return cfg


def exam_duration_hours(exam):
    return (exam["end"] - exam["start"]).total_seconds() / 3600.0


def extend_exams_with_levels(trial_exams, final_exams, exam_timetable):
    # Reparse from source to fetch new fields
    src_subjects = exam_timetable.get("subjects", {})
    def enrich(group_dict, group_key):
        for subject, exams in group_dict.items():
            # find source exams list
            src_exams = src_subjects.get(subject, {}).get("exam_types", {}).get(group_key, {}).get("exams", [])
            # naive matching by paper and start ISO
            for ex in exams:
                for s in src_exams:
                    if s.get("paper") == ex["paper"] and datetime.fromisoformat(s["start_datetime"]) == ex["start"]:
                        ex["effort_level"] = s.get("effort_level", "medium")
                        ex["theory_level"] = s.get("theory_level", "medium")
                        ex["practice_level"] = s.get("practice_level", "medium")
                        ex["past_papers_required"] = int(s.get("past_papers_required", 0))
                        # Optional hours override for preparation workload (excludes past papers)
                        if "hours" in s:
                            try:
                                ex["hours"] = float(s["hours"])
                            except Exception:
                                pass
                        break
    enrich(trial_exams, "trial")
    enrich(final_exams, "final")


def build_tasks_for_exam(subject, exam):
    L = exam_duration_hours(exam)
    effort = LEVELS_EFFORT.get(exam.get("effort_level", "medium"), 1.2)
    theory_mult = LEVELS_THEORY.get(exam.get("theory_level", "medium"), 2.0)
    practice_mult = LEVELS_PRACTICE.get(exam.get("practice_level", "medium"), 1.5)

    def _round_up_to_45min(hours_val: float) -> float:
        # Round up to nearest 45-minute multiple
        total_minutes = int(round(hours_val * 60))
        # Avoid rounding down; always ceil to 45-min blocks
        blocks = (total_minutes + 44) // 45
        return (blocks * 45) / 60.0

    tasks = []

    # Past papers first to frontload at least one before other study blocks
    N = int(exam.get("past_papers_required", 0))
    mandatory_pp = True
    if N == 0:
        # If explicitly set to 0 on this exam, disable mandatory past paper
        mandatory_pp = "past_papers_required" not in exam
        if mandatory_pp:
            N = 1
    if N > 0:
        # Non-written must be at least 2h
        tasks.append({
            "subject": subject,
            "paper": exam["paper"],
            "type": "Past Paper 1 (non-written)",
            "hours": 2.0,
            "mandatory": True
        })
        for i in range(2, N + 1):
            # Timed past papers must be exactly 3h
            tasks.append({
                "subject": subject,
                "paper": exam["paper"],
                "type": f"Past Paper {i} (timed)",
                "hours": 3.0,
                "mandatory": False
            })

    # Preparation workload: support hours override that excludes past papers.
    override_hours = exam.get("hours")
    if override_hours is not None:
        try:
            prep_hours = max(0.0, float(override_hours))
            prep_hours = _round_up_to_45min(prep_hours)
        except Exception:
            prep_hours = None
    else:
        prep_hours = None

    if prep_hours is not None and prep_hours > 0:
        tasks.append({
            "subject": subject,
            "paper": exam["paper"],
            "type": "Preparation",
            "hours": prep_hours,
            "mandatory": False
        })
    else:
        # Fall back to computed theory/practice workload if no override provided
        th = L * theory_mult * effort
        if th > 0:
            tasks.append({"subject": subject, "paper": exam["paper"], "type": "Theory Study", "hours": th, "mandatory": False})
        ph = L * practice_mult * effort
        if ph > 0:
            tasks.append({"subject": subject, "paper": exam["paper"], "type": "Practice", "hours": ph, "mandatory": False})

    return tasks


def list_blocks_by_date(trial_exams, final_exams, tuition_blocks, planner_start, planner_end):
    blocks = defaultdict(list)
    def add_block(start, end):
        blocks[start.date()].append((start, end))
    # Exams and mandatory post-exam downtime (2h) count as occupied
    downtime = timedelta(hours=2)
    all_dates = set()
    for by_subject in (trial_exams, final_exams):
        for _, exams in by_subject.items():
            for ex in exams:
                add_block(ex["start"], ex["end"])
                all_dates.add(ex["start"].date())
                # Add 2h after-exam downtime block
                post_start = ex["end"]
                post_end = ex["end"] + downtime
                add_block(post_start, post_end)
                all_dates.add(post_start.date())
    # Tuition classes plus 30m before and 1.5h after
    pre = timedelta(minutes=30)
    post = timedelta(minutes=90)
    for (ts, te) in tuition_blocks:
        add_block(ts, te)
        add_block(ts - pre, ts)   # buffer before class
        add_block(te, te + post)  # buffer after class
        all_dates.add(ts.date()); all_dates.add(te.date())
    
    # Force-insert a supper break 18:30–20:00 for every date in the planner range
    current_date = planner_start.date()
    end_date = planner_end.date() if isinstance(planner_end, datetime) else planner_end
    while current_date <= end_date:
        day_dt = datetime.combine(current_date, datetime.min.time())
        supper_start = day_dt.replace(hour=18, minute=30, second=0, microsecond=0)
        supper_end = supper_start + timedelta(minutes=90)
        add_block(supper_start, supper_end)
        current_date += timedelta(days=1)
    
    return blocks


def _day_bounds(day_dt, cfg):
    sh, sm = cfg["daily_start"]
    eh, em = cfg["daily_end"]
    # Hard clamp to 09:00–23:00
    sh = max(sh, HARD_START_HOUR)
    eh = min(eh, HARD_END_HOUR)
    s = day_dt.replace(hour=sh, minute=sm, second=0, microsecond=0)
    e = day_dt.replace(hour=eh, minute=em, second=0, microsecond=0)
    return s, e


def _free_segments(day_dt, occupied_blocks, start_pref, end_pref):
    # Start with preferred window within day bounds, then subtract occupied
    segments = [(start_pref, end_pref)]
    for (bs, be) in sorted(occupied_blocks):
        new_segments = []
        for (fs, fe) in segments:
            if be <= fs or bs >= fe:
                new_segments.append((fs, fe))
            else:
                if bs > fs:
                    new_segments.append((fs, bs))
                if be < fe:
                    new_segments.append((be, fe))
        segments = new_segments
    # Remove tiny crumbs under DEFAULT_SESSION_MIN
    pruned = []
    for (fs, fe) in segments:
        if (fe - fs).total_seconds() >= DEFAULT_SESSION_MIN * 60:
            pruned.append((fs, fe))
    return pruned


def _sum_block_minutes(blocks):
    return sum(int((be - bs).total_seconds() // 60) for (bs, be) in blocks)


def _allocate_single_block(minutes_needed, free_segments, frontload=True):
    """Pick a single contiguous slot of minutes_needed from free_segments.
    Returns a list with one (start, end) tuple or empty list if none fits.
    """
    if minutes_needed <= 0:
        return []
    segs = sorted(free_segments, key=lambda ab: ab[0]) if frontload else sorted(free_segments, key=lambda ab: ab[0], reverse=True)
    for (s, e) in segs:
        seg_mins = int((e - s).total_seconds() // 60)
        if seg_mins >= minutes_needed:
            return [(s, s + timedelta(minutes=minutes_needed))]
    return []


def _allocate_sessions(hours_needed, free_segments, per_subject_remaining_mins, day_remaining_mins, break_minutes, frontload=True, ignore_caps=False):
    minutes_needed = int(round(hours_needed * 60))
    sessions = []
    # Order segments: frontload earlier in the day if requested
    segs = sorted(free_segments, key=lambda ab: ab[0]) if frontload else sorted(free_segments, key=lambda ab: ab[0], reverse=True)
    last_end = None
    for (s, e) in segs:
        cursor = s
        while cursor < e and minutes_needed > 0 and per_subject_remaining_mins > 0 and day_remaining_mins > 0:
            seg_mins = int((e - cursor).total_seconds() // 60)
            if seg_mins <= 0:
                break
            session_len = min(DEFAULT_SESSION_MAX, seg_mins, per_subject_remaining_mins, day_remaining_mins, minutes_needed)
            # Ensure minimum unless tail remainder
            if session_len < DEFAULT_SESSION_MIN and minutes_needed > DEFAULT_SESSION_MIN:
                break
            # Insert break if contiguous with previous
            if last_end and cursor <= last_end:
                cursor = last_end + timedelta(minutes=break_minutes)
                if cursor >= e:
                    break
                seg_mins = int((e - cursor).total_seconds() // 60)
                if seg_mins < DEFAULT_SESSION_MIN:
                    break
            session_end = cursor + timedelta(minutes=session_len)
            sessions.append((cursor, session_end))
            last_end = session_end
            cursor = session_end + timedelta(minutes=break_minutes)  # enforce break after each session within the same segment
            minutes_needed -= session_len
            per_subject_remaining_mins -= session_len
            day_remaining_mins -= session_len
        if minutes_needed <= 0:
            break
    remaining_hours = minutes_needed / 60.0
    return sessions, remaining_hours, per_subject_remaining_mins, day_remaining_mins


def schedule_study_for_exam(subject, exam, tasks, planner_start, blocks_by_date, cfg, session_count_by_day):
    scheduled = []
    today = datetime.now().date()
    # We schedule until exam start day/time; do not place after exam start/end
    last_day = exam["start"].date()

    # Day-before priority reservation (non-negotiable):
    # Determine target number of sessions for D-1 (and fallback to D-2 if needed)
    required_sessions = cfg["day_before_sessions_high_effort"] if str(exam.get("effort_level", "")).lower() == "high" else cfg["day_before_sessions_default"]
    # Build a list of non–past-paper study tasks (prep/theory/practice) to draw from for these sessions
    priority_pool = []
    for t in tasks:
        if not (isinstance(t.get("type"), str) and "Past Paper" in t["type"]):
            priority_pool.append(t)
    # Helper to reserve sessions on a specific date
    def _reserve_priority_on(day_date, remaining_sessions):
        if remaining_sessions <= 0:
            return 0
        day_dt = datetime.combine(day_date, datetime.min.time())
        day_start, day_end = _day_bounds(day_dt, cfg)
        # If it is the exam day, cap to exam start and skip if morning exam
        if day_date == last_day:
            if exam["start"].hour < 12:
                return 0
            day_end = min(day_end, exam["start"])  # never intrude exam window
        occupied = list(blocks_by_date.get(day_date, []))
        free = _free_segments(day_dt, occupied, day_start, day_end)
        sessions_made = 0
        # Use standard session sizing for ADHD (45–75m)
        per_subj = 10**9  # ignore caps per requirement
        day_cap = 10**9
        # Iterate through the priority tasks in round-robin fashion to carve sessions
        i = 0
        while free and remaining_sessions > 0 and priority_pool and i < len(priority_pool):
            task = priority_pool[i]
            # allocate one session chunk only (DEFAULT_SESSION_MAX) to count as a session
            alloc_hours = min(task["hours"], DEFAULT_SESSION_MAX / 60.0)
            sess, rem, _, _ = _allocate_sessions(alloc_hours, free, per_subj, day_cap, cfg["break_minutes"], frontload=True, ignore_caps=True)
            if sess:
                # take only the first produced session to count as 1 reserved session
                ss, ee = sess[0]
                scheduled.append({"subject": subject, "paper": exam["paper"], "type": task["type"], "start": ss, "end": ee})
                # mark occupied and recompute free
                blocks_by_date.setdefault(day_date, []).append((ss, ee))
                occupied.append((ss, ee))
                free = _free_segments(day_dt, occupied, day_start, day_end)
                # reduce task hours
                task["hours"] = max(0.0, task["hours"] - (ee - ss).total_seconds() / 3600.0)
                remaining_sessions -= 1
                sessions_made += 1
                # if task depleted, remove from pool
                if task["hours"] <= 1e-6:
                    priority_pool.pop(i)
                    i = 0
                    continue
            i += 1
            if i >= len(priority_pool):
                # restart loop to try remaining pool again in case free segments changed
                i = 0
                # If we couldn’t place any more, break to avoid infinite loop
                if sessions_made == 0:
                    break
                sessions_made = 0
        return remaining_sessions
    # Reserve on D-1, then D-2 if needed
    day_before = last_day - timedelta(days=1)
    remaining = required_sessions
    remaining -= _reserve_priority_on(day_before, remaining) if day_before >= today and day_before >= planner_start.date() else 0
    if remaining > 0:
        two_before = last_day - timedelta(days=2)
        remaining -= _reserve_priority_on(two_before, remaining) if two_before >= today and two_before >= planner_start.date() else 0

    # Prepare backward and forward iteration with frontload preference
    day_cursor = max(planner_start.date(), today)
    # Loop through days from planner_start to last_day inclusive
    d = day_cursor
    while d <= last_day and tasks:
        day_dt = datetime.combine(d, datetime.min.time())
        day_start, day_end = _day_bounds(day_dt, cfg)
        # On exam day, cap end to exam start and forbid morning study before a morning exam
        if d == last_day:
            # If exam starts before 12:00, do not schedule any sessions on this day at all
            if exam["start"].hour < 12:
                free = []
                occupied = blocks_by_date.get(d, [])
                # skip scheduling by setting day_end before day_start
                day_end = day_start
            else:
                day_end = min(day_end, exam["start"])  # do not run into exam time
        occupied = list(blocks_by_date.get(d, []))
        # Insert daily supper break 18:30–20:00 as non-counting occupied block
        # Note: Supper is already added in list_blocks_by_date, but ensure it's present
        supper_start = day_dt.replace(hour=18, minute=30, second=0, microsecond=0)
        supper_end = supper_start + timedelta(minutes=90)
        # Only add if intersects day window and not already in occupied
        if supper_end > day_start and supper_start < day_end:
            ss = max(supper_start, day_start)
            se = min(supper_end, day_end)
            if se > ss:
                # Check if already present in occupied blocks
                supper_already_present = False
                for (obs, obe) in occupied:
                    if _overlaps(ss, se, obs, obe):
                        supper_already_present = True
                        break
                if not supper_already_present:
                    occupied.append((ss, se))
        free = _free_segments(day_dt, occupied, day_start, day_end)

        # Compute available daily capacity: study_time_per_day (or per_day_max) minus counting blocks only
        # Count only exams, tuition, and their buffers - NOT supper break
        counting_minutes = 0
        for (bs, be) in occupied:
            # Check if this is a supper break (18:30-20:00) - exclude from counting
            if bs.hour == 18 and bs.minute == 30 and (be - bs) == timedelta(minutes=90):
                continue  # Skip supper break
            counting_minutes += int((be - bs).total_seconds() // 60)
        
        base_cap_hours = cfg["study_time_per_day"] if cfg["study_time_per_day"] is not None else cfg["per_day_max_hours"]
        day_cap_minutes = int(base_cap_hours * 60) - counting_minutes
        # Weekend extra
        if d.weekday() >= 5:
            day_cap_minutes += int(cfg["weekend_extra_hours"] * 60)
        # Free day (minimal counting blocks) extra
        if counting_minutes <= 30:  # Allow for tiny blocks
            day_cap_minutes += int(cfg["free_day_extra_hours"] * 60)
        day_cap_minutes = max(0, day_cap_minutes)

        per_subject_remaining = int(cfg["per_subject_daily_cap_hours"] * 60)
        # Track per-day placed session count to trigger 2h break after every 4 sessions
        day_session_count = int(session_count_by_day.get(d, 0))
        i = 0
        while i < len(tasks) and free:
            task = tasks[i]
            is_past_paper = isinstance(task.get("type"), str) and "Past Paper" in task["type"]
            must_ignore_caps = bool(task.get("mandatory", False))
            # Determine effective caps for this task
            eff_per_subj = per_subject_remaining if not must_ignore_caps else 10**9
            eff_day_cap = day_cap_minutes if not must_ignore_caps else 10**9
            # If not mandatory and no capacity remains, stop trying today
            if not must_ignore_caps and (eff_per_subj <= 0 or eff_day_cap <= 0):
                break

            used_minutes = 0
            sessions = []
            rem_hours = task["hours"]

            if is_past_paper:
                # Single contiguous block: 2h or 3h exactly
                minutes_needed = int(round(task["hours"] * 60))
                # For non-mandatory, require that caps can fit the whole block
                if must_ignore_caps or (eff_per_subj >= minutes_needed and eff_day_cap >= minutes_needed):
                    sessions = _allocate_single_block(minutes_needed, free, frontload=cfg["adhd_frontload"])
                    if sessions:
                        rem_hours = 0.0
            else:
                # Regular tasks: split into sessions with breaks
                sessions, rem_hours, new_per_subj, new_day_cap = _allocate_sessions(
                    task["hours"], free, eff_per_subj, eff_day_cap, cfg["break_minutes"], frontload=cfg["adhd_frontload"], ignore_caps=must_ignore_caps
                )

            # Update capacities and free segments if we placed anything
            for (ss, ee) in sessions:
                dur = int((ee - ss).total_seconds() // 60)
                used_minutes += dur
                scheduled.append({"subject": subject, "paper": exam["paper"], "type": task["type"], "start": ss, "end": ee})
                # Update occupied with session itself and recompute free segments immediately
                occupied.append((ss, ee))
                day_session_count += 1
                
                # Insert mandatory 15-minute break after every study session (counts toward day cap)
                short_break_start = ee
                short_break_end = ee + timedelta(minutes=cfg["break_minutes"])
                if short_break_start < day_end:
                    # Clamp break to day bounds
                    bs = max(short_break_start, day_start)
                    be = min(short_break_end, day_end)
                    if be > bs:
                        occupied.append((bs, be))
                        # Add explicit break item (counts toward daily study time)
                        scheduled.append({
                            "subject": subject,
                            "paper": exam["paper"],
                            "type": "Break: 15m",
                            "start": bs,
                            "end": be,
                        })
                        # 15-minute between-session breaks count towards daily study time
                        used_minutes += int((be - bs).total_seconds() // 60)
                
                # If this was a Past Paper, enforce mandatory post-paper downtime which also counts to the cap:
                # - non-written: 45 minutes after
                # - timed (written): 90 minutes after
                if is_past_paper:
                    # Determine break length from type
                    t = str(task.get("type", ""))
                    extra_break = 45 if "non-written" in t else 90
                    # Place break after the 15m inter-session break if it exists
                    break_start = short_break_end if short_break_end > short_break_start else ee
                    break_end = break_start + timedelta(minutes=extra_break)
                    # Clamp the break to day bounds
                    if break_start < day_end:
                        bs = max(break_start, day_start)
                        be = min(break_end, day_end)
                        if be > bs:
                            occupied.append((bs, be))
                            # Add explicit post-past-paper break item (counts toward daily study time)
                            label = f"Break: Post Past Paper ({extra_break}m)"
                            scheduled.append({
                                "subject": subject,
                                "paper": exam["paper"],
                                "type": label,
                                "start": bs,
                                "end": be,
                            })
                            extra_used = int((be - bs).total_seconds() // 60)
                            used_minutes += extra_used
                
                # Insert a mandatory 2-hour break after every 4 sessions (does NOT count toward day cap)
                if day_session_count % 4 == 0:
                    # Find the end point of the last break we added
                    last_end = ee
                    if short_break_end > short_break_start:
                        last_end = short_break_end
                    if is_past_paper:
                        # Account for post-past-paper break
                        t = str(task.get("type", ""))
                        extra_break = 45 if "non-written" in t else 90
                        last_end = last_end + timedelta(minutes=extra_break)
                    
                    long_break_start = last_end
                    long_break_end = long_break_start + timedelta(hours=2)
                    if long_break_start < day_end:
                        lbs = max(long_break_start, day_start)
                        lbe = min(long_break_end, day_end)
                        if lbe > lbs:
                            occupied.append((lbs, lbe))
                            # Add explicit 2h recovery break item (non-counting)
                            scheduled.append({
                                "subject": subject,
                                "paper": exam["paper"],
                                "type": "Break: 2h recovery",
                                "start": lbs,
                                "end": lbe,
                            })
                            # Note: 2h recovery breaks do NOT count toward daily capacity
                
                # Recompute free segments after adding all breaks to avoid overlaps
                free = _free_segments(day_dt, occupied, day_start, day_end)

            if sessions:
                if not is_past_paper:
                    # allocator already computed new caps for regular tasks, but we need to add counting break minutes
                    if not must_ignore_caps:
                        per_subject_remaining = new_per_subj
                        day_cap_minutes = new_day_cap
                    else:
                        # Only count session time and counting breaks (15m + post-past-paper), not 2h recovery
                        counting_used = dur  # session time
                        # Add 15m break if it was added
                        if short_break_end > short_break_start:
                            counting_used += int((min(short_break_end, day_end) - max(short_break_start, day_start)).total_seconds() // 60)
                        per_subject_remaining = max(0, per_subject_remaining - counting_used)
                        day_cap_minutes = max(0, day_cap_minutes - counting_used)
                else:
                    # Past papers: apply cap deductions including post-paper downtime (but not 2h recovery)
                    counting_used = used_minutes  # This already includes session + 15m break + post-past-paper downtime
                    if not must_ignore_caps:
                        per_subject_remaining = max(0, per_subject_remaining - counting_used)
                        day_cap_minutes = max(0, day_cap_minutes - counting_used)
                    else:
                        # mandatory may drive caps below zero conceptually; clamp to 0
                        per_subject_remaining = max(0, per_subject_remaining - counting_used)
                        day_cap_minutes = max(0, day_cap_minutes - counting_used)
                task["hours"] = rem_hours

            # Advance to next task or keep same if partially remaining
            if task["hours"] <= 1e-6:
                tasks.pop(i)
            else:
                i += 1
        # Persist updated session count for this day across subjects
        session_count_by_day[d] = day_session_count
        d += timedelta(days=1)

    return scheduled


def build_study_plan(exam_timetable, legacy_data):
    trial_exams, final_exams, subject_colors, subject_abbreviations, subject_emojis = legacy_data
    cfg = _get_config(exam_timetable)

    # Enrich existing exam dicts with levels & past papers
    extend_exams_with_levels(trial_exams, final_exams, exam_timetable)

    planner_start = datetime.fromisoformat(exam_timetable["metadata"]["planner_start_date"])    
    planner_end = datetime.fromisoformat(exam_timetable["metadata"]["planner_end_date"])    
    blocks_by_date = list_blocks_by_date(trial_exams, final_exams, cfg["tuition_blocks"], planner_start, planner_end)

    plan = []
    # Maintain per-day session count across all subjects
    session_count_by_day = defaultdict(int)
    # Iterate exams in chronological order to schedule per exam
    all_exams = []
    for subject, exams in trial_exams.items():
        for ex in exams:
            all_exams.append((subject, ex))
    for subject, exams in final_exams.items():
        for ex in exams:
            all_exams.append((subject, ex))
    all_exams.sort(key=lambda se: se[1]["start"]) 

    for subject, exam in all_exams:
        tasks = build_tasks_for_exam(subject, exam)
        if not tasks:
            continue
        scheduled = schedule_study_for_exam(subject, exam, [t.copy() for t in tasks], planner_start, blocks_by_date, cfg, session_count_by_day)
        # Add scheduled sessions and breaks both to the plan and to occupied blocks so later scheduling avoids overlap
        for s in scheduled:
            plan.append(s)
            d = s["start"].date()
            blocks_by_date.setdefault(d, []).append((s["start"], s["end"]))
            # If this item is a study session (not a break or exam), count it toward the per-day session counter
            if not str(s.get("type", "")).startswith("Break") and s.get("type") != "EXAM":
                session_count_by_day[d] += 1

    # Add supper breaks to the plan so verification can see them
    planner_end = datetime.fromisoformat(exam_timetable["metadata"]["planner_end_date"])
    current_date = planner_start.date()
    end_date = planner_end.date()
    while current_date <= end_date:
        # Check if this day has any scheduled activities
        day_has_activities = False
        for item in plan:
            if item["start"].date() == current_date:
                day_has_activities = True
                break
        
        if day_has_activities:
            day_dt = datetime.combine(current_date, datetime.min.time())
            supper_s = day_dt.replace(hour=18, minute=30, second=0, microsecond=0)
            supper_e = supper_s + timedelta(minutes=90)
            plan.append({
                "subject": "—",
                "paper": "—",
                "type": "Break: Supper",
                "start": supper_s,
                "end": supper_e,
            })
        current_date += timedelta(days=1)
    
    plan.sort(key=lambda x: x["start"])
    return plan


def _overlaps(a_start, a_end, b_start, b_end):
    return (a_start < b_end) and (b_start < a_end)


def verify_study_plan(plan, trial_exams, final_exams, cfg):
    warnings = []
    # Build a map: date -> sorted list of study items (exclude EXAM rows; they are added only in rendering)
    by_date = defaultdict(list)
    for it in plan:
        by_date[it["start"].date()].append(it)
    for d in by_date:
        by_date[d].sort(key=lambda x: x["start"])
    # For each day, verify:
    # 1) 15-minute break after each study session (except when a bigger enforced break starts immediately)
    # 2) 2-hour break exists somewhere after every 4th session
    # 3) Supper break intersects 18:30–20:00
    # 4) Post-past-paper downtime (45/90 min) follows past paper sessions
    for day, items in sorted(by_date.items()):
        # Gather occupied blocks produced by plan for that day
        blocks = [(x["start"], x["end"]) for x in items]
        # Helpers
        def has_block_between(start, end, min_minutes):
            for (bs, be) in blocks:
                if _overlaps(bs, be, start, end):
                    # overlap length
                    ovl = max(0, int((min(be, end) - max(bs, start)).total_seconds() // 60))
                    if ovl >= min_minutes:
                        return True
            return False
        # Daily bounds and supper
        day_dt = datetime.combine(day, datetime.min.time())
        day_start, day_end = _day_bounds(day_dt, cfg)
        supper_s = day_dt.replace(hour=18, minute=30, second=0, microsecond=0)
        supper_e = supper_s + timedelta(minutes=90)
        supper_s = max(supper_s, day_start)
        supper_e = min(supper_e, day_end)
        if supper_e > supper_s:
            # Check if we have a supper break in the plan items (not just blocks)
            has_supper = False
            for it in items:
                if "Break: Supper" in str(it.get("type", "")):
                    has_supper = True
                    break
            if not has_supper:
                warnings.append(f"{day.isoformat()}: Missing supper break around 18:30–20:00")
        # Session-based checks - count only actual study sessions, not breaks or exams
        session_count = 0
        for idx, it in enumerate(items):
            # Only count actual study sessions (not breaks, not exams)
            if not str(it.get("type", "")).startswith("Break") and it.get("type") != "EXAM":
                session_count += 1
            cur_end = it["end"]
            
            # 15-minute break check - only for actual study sessions
            if not str(it.get("type", "")).startswith("Break") and it.get("type") != "EXAM":
                if idx < len(items) - 1:
                    next_start = items[idx+1]["start"]
                    # there should be an occupied block covering at least the configured break in [cur_end, next_start)
                    gap = (next_start - cur_end).total_seconds() / 60
                    if gap >= cfg["break_minutes"]:
                        # ensure we actually blocked it with a break block
                        if not has_block_between(cur_end, next_start, cfg["break_minutes"]):
                            warnings.append(f"{day.isoformat()}: Missing 15m inter-session break after {it['subject']} – {it['paper']}")
            
            # 2-hour after every 4 sessions - only count actual study sessions
            if not str(it.get("type", "")).startswith("Break") and it.get("type") != "EXAM" and session_count % 4 == 0:
                # look for any occupied block starting at or after cur_end that is at least 120m within the same day bounds
                long_s = cur_end
                long_e = min(day_end, cur_end + timedelta(hours=2))
                # Accept if there is >=90m overlap (allow slight truncation by bounds)
                if (long_e - long_s) >= timedelta(minutes=60):
                    if not has_block_between(long_s, long_e, 90):
                        warnings.append(f"{day.isoformat()}: Missing 2h recovery break after 4 sessions (after {it['subject']} – {it['paper']})")
            
            # Post-past-paper downtime
            t = str(it.get("type", ""))
            if "Past Paper" in t:
                need = 45 if "non-written" in t else 90
                pp_s = cur_end
                pp_e = min(day_end, cur_end + timedelta(minutes=need))
                if (pp_e - pp_s) >= timedelta(minutes=need // 2):
                    if not has_block_between(pp_s, pp_e, need // 2):
                        # if at least half the required downtime isn't blocked, warn
                        warnings.append(f"{day.isoformat()}: Missing post-past-paper downtime ({need}m) after {it['subject']} – {it['paper']}")
    return warnings


def create_study_plan_pages(doc_elements, exam_timetable, legacy_data):
    styles = getSampleStyleSheet()
    title_para = Paragraph("<b>Proposed Study Plan</b>", styles['Heading1'])
    doc_elements.append(title_para)
    doc_elements.append(Spacer(1, 12))

    trial_exams, final_exams, subject_colors, subject_abbreviations, subject_emojis = legacy_data
    plan = build_study_plan(exam_timetable, legacy_data)

    # Sanity check: verify required breaks exist and emit warnings
    cfg = _get_config(exam_timetable)
    warnings = verify_study_plan(plan, trial_exams, final_exams, cfg)
    if warnings:
        click.echo("Study Plan Sanity Check: some required breaks are missing:", err=True)
        for w in warnings:
            click.echo(f" - {w}", err=True)
        # Also render a warnings panel
        warn_title = Paragraph("<b>Sanity Check Warnings</b>", styles['Heading3'])
        doc_elements.append(warn_title)
        for w in warnings:
            doc_elements.append(Paragraph(w, styles['Normal']))
        doc_elements.append(Spacer(1, 12))

    # Build list of exam items to include in the schedule view (and highlight)
    exam_items = []
    for subject, exams in trial_exams.items():
        for ex in exams:
            exam_items.append({
                "subject": subject,
                "paper": ex["paper"],
                "type": "EXAM",
                "start": ex["start"],
                "end": ex["end"],
            })
    for subject, exams in final_exams.items():
        for ex in exams:
            exam_items.append({
                "subject": subject,
                "paper": ex["paper"],
                "type": "EXAM",
                "start": ex["start"],
                "end": ex["end"],
            })

    # Merge plan sessions and exam items, then group by date
    by_date = defaultdict(list)
    for item in plan + exam_items:
        by_date[item["start"].date()].append(item)

    # Supper breaks are already added in build_study_plan, no need to add them again

    for d in sorted(by_date.keys()):
        day_title = Paragraph(d.strftime("<b>%A, %b %d, %Y</b>"), styles['Heading2'])
        doc_elements.append(day_title)
        data = [["Time", "Subject", "Paper", "Activity"]]
        row_styles = []
        for it in sorted(by_date[d], key=lambda x: x["start"]):
            start = it["start"].strftime("%H:%M")
            end = it["end"].strftime("%H:%M")
            activity = it["type"] if it.get("type") != "EXAM" else "EXAM"
            data.append([f"{start}–{end}", it["subject"], it["paper"], activity])
        # Build table
        tbl = Table(data, colWidths=[1.2*inch, 2.2*inch, 2.8*inch, 3.5*inch])
        base_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('GRID', (0, 0), (-1, -1), 0.5, dark_grey),
        ]
        # Highlight exam rows: find row indices where activity is EXAM and apply a distinct background
        for r in range(1, len(data)):
            if data[r][3] == 'EXAM':
                # Light orange background + bold text for the entire row
                base_style.append(('BACKGROUND', (0, r), (-1, r), colors.Color(1.0, 0.95, 0.85)))
                base_style.append(('FONTNAME', (0, r), (-1, r), 'Helvetica-Bold'))
        tbl.setStyle(TableStyle(base_style))
        doc_elements.append(tbl)
        doc_elements.append(Spacer(1, 10))
    doc_elements.append(PageBreak())


def generate_pdf(exam_timetable, legacy_data, filename=None):
    """Generate the complete PDF day planner"""
    year = exam_timetable['metadata']['year']
    if filename is None:
        filename = f"Grade12_Exam_Day_Planner_{year}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=landscape(A4),
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)

    doc_elements = []

    # Create exam summary page
    create_exam_summary_page(doc_elements, exam_timetable, legacy_data)

    # Create daily planner pages
    create_daily_planner_pages(doc_elements, exam_timetable, legacy_data)

    # Create study plan pages (after daily planner)
    create_study_plan_pages(doc_elements, exam_timetable, legacy_data)

    # Build the PDF
    doc.build(doc_elements)
    print(f"PDF generated successfully: {filename}")

    return filename

def export_exam_data_to_json(exam_timetable, filename="exam_timetable.json"):
    """Export the exam timetable data to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(exam_timetable, f, indent=2, ensure_ascii=False)
        print(f"Exam data exported to: {filename}")
    except Exception as e:
        print(f"Failed to export exam data: {e}")

@click.command()
@click.option('--input', '-i', 'input_file', default='custom_data.json', help='Input JSON file with exam data (default: custom_data.json)')
@click.option('--output', '-o', default=None, help='Output PDF filename (default: Grade12_Exam_Day_Planner_{year}.pdf)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def main(input_file, output, verbose):
    """Generate Grade 12 exam day planner PDF from JSON data file with color-coded subjects and highlighted exam periods."""
    
    if verbose:
        click.echo("Starting Grade 12 Exam Day Planner generation...")
        click.echo(f"Loading exam data from: {input_file}")
    
    # Load exam data from JSON file
    exam_timetable = load_exam_data(input_file)

    # Build runtime structures from current JSON (replaces legacy conversion)
    legacy_data = build_runtime_structures(exam_timetable)
    
    if verbose:
        click.echo("✓ Exam data loaded successfully")
    
    # Generate PDF
    if verbose:
        click.echo("Generating PDF...")
    pdf_filename = generate_pdf(exam_timetable, legacy_data, output)
    
    if verbose:
        click.echo(f"✓ PDF generated successfully: {pdf_filename}")
    else:
        click.echo(f"Generated: {pdf_filename}")

if __name__ == "__main__":
    main()