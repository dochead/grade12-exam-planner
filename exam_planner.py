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