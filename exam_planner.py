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

# Exam dictionaries with datetime objects
trial_exams = {
    "Life Orientation (L.O.)": [
        {
            "paper": "CAT",
            "start": datetime(2025, 9, 1, 9, 0),
            "end": datetime(2025, 9, 1, 11, 30)
        }
    ],
    "English Home Language": [
        {
            "paper": "Paper II",
            "start": datetime(2025, 9, 2, 9, 0),
            "end": datetime(2025, 9, 2, 11, 30)
        },
        {
            "paper": "Paper III",
            "start": datetime(2025, 9, 9, 9, 0),
            "end": datetime(2025, 9, 9, 12, 0)
        },
        {
            "paper": "Paper I",
            "start": datetime(2025, 9, 11, 9, 0),
            "end": datetime(2025, 9, 11, 11, 0)
        }
    ],
    "Afrikaans First Additional Language": [
        {
            "paper": "Paper III",
            "start": datetime(2025, 9, 4, 9, 0),
            "end": datetime(2025, 9, 4, 11, 30)
        },
        {
            "paper": "Paper II",
            "start": datetime(2025, 9, 12, 9, 0),
            "end": datetime(2025, 9, 12, 11, 0)
        },
        {
            "paper": "Paper I",
            "start": datetime(2025, 9, 18, 9, 0),
            "end": datetime(2025, 9, 18, 11, 0)
        }
    ],
    "Mathematics": [
        {
            "paper": "Paper I",
            "start": datetime(2025, 9, 8, 9, 0),
            "end": datetime(2025, 9, 8, 12, 0)
        },
        {
            "paper": "Paper II",
            "start": datetime(2025, 9, 22, 9, 0),
            "end": datetime(2025, 9, 22, 12, 0)
        }
    ],
    "Life Sciences": [
        {
            "paper": "Paper I",
            "start": datetime(2025, 9, 4, 13, 0),
            "end": datetime(2025, 9, 4, 15, 30)
        },
        {
            "paper": "Paper II",
            "start": datetime(2025, 9, 17, 9, 0),
            "end": datetime(2025, 9, 17, 11, 30)
        }
    ],
    "Information Technology": [
        {
            "paper": "Paper II (Theory)",
            "start": datetime(2025, 9, 9, 13, 30),
            "end": datetime(2025, 9, 9, 16, 30)
        },
        {
            "paper": "Paper I (Practical)",
            "start": datetime(2025, 9, 10, 9, 0),
            "end": datetime(2025, 9, 10, 12, 0)
        }
    ],
    "Physical Science": [
        {
            "paper": "Paper I (Physics)",
            "start": datetime(2025, 9, 15, 9, 0),
            "end": datetime(2025, 9, 15, 12, 0)
        },
        {
            "paper": "Paper II (Chemistry)",
            "start": datetime(2025, 9, 25, 9, 0),
            "end": datetime(2025, 9, 25, 12, 0)
        }
    ]
}

final_exams = {
    "English Home Language": [
        {
            "paper": "Paper 3",
            "start": datetime(2025, 10, 23, 9, 0),
            "end": datetime(2025, 10, 23, 12, 0)
        },
        {
            "paper": "Paper 1",
            "start": datetime(2025, 10, 29, 9, 0),
            "end": datetime(2025, 10, 29, 11, 0)
        },
        {
            "paper": "Paper 2",
            "start": datetime(2025, 11, 13, 9, 0),
            "end": datetime(2025, 11, 13, 11, 30)
        }
    ],
    "Afrikaans First Additional Language": [
        {
            "paper": "Paper 3",
            "start": datetime(2025, 10, 24, 9, 0),
            "end": datetime(2025, 10, 24, 11, 30)
        },
        {
            "paper": "Paper 1",
            "start": datetime(2025, 11, 11, 9, 0),
            "end": datetime(2025, 11, 11, 11, 0)
        },
        {
            "paper": "Paper 2",
            "start": datetime(2025, 11, 21, 9, 0),
            "end": datetime(2025, 11, 21, 11, 30)
        }
    ],
    "Mathematics": [
        {
            "paper": "Paper 1",
            "start": datetime(2025, 10, 31, 9, 0),
            "end": datetime(2025, 10, 31, 12, 0)
        },
        {
            "paper": "Paper 2",
            "start": datetime(2025, 11, 3, 9, 0),
            "end": datetime(2025, 11, 3, 12, 0)
        }
    ],
    "Life Sciences": [
        {
            "paper": "Paper 1",
            "start": datetime(2025, 11, 14, 9, 0),
            "end": datetime(2025, 11, 14, 11, 30)
        },
        {
            "paper": "Paper 2",
            "start": datetime(2025, 11, 17, 9, 0),
            "end": datetime(2025, 11, 17, 11, 30)
        }
    ],
    "Information Technology": [
        {
            "paper": "Paper 1 (Practical)",
            "start": datetime(2025, 10, 22, 9, 0),
            "end": datetime(2025, 10, 22, 12, 0)
        },
        {
            "paper": "Paper 2 (Theory)",
            "start": datetime(2025, 11, 13, 14, 0),
            "end": datetime(2025, 11, 13, 17, 0)
        },
        {
            "paper": "Practical Rewrite",
            "start": datetime(2025, 11, 27, 9, 0),
            "end": datetime(2025, 11, 27, 12, 0)
        }
    ],
    "Physical Science": [
        {
            "paper": "Paper 1 (Physics)",
            "start": datetime(2025, 11, 7, 9, 0),
            "end": datetime(2025, 11, 7, 12, 0)
        },
        {
            "paper": "Paper 2 (Chemistry)",
            "start": datetime(2025, 11, 10, 9, 0),
            "end": datetime(2025, 11, 10, 12, 0)
        }
    ]
}

# Color scheme for subjects
subject_colors = {
    "Life Orientation (L.O.)": colors.lightblue,
    "English Home Language": colors.lightcoral,
    "Afrikaans First Additional Language": colors.lightgreen,
    "Mathematics": colors.lightyellow,
    "Life Sciences": colors.lightpink,
    "Information Technology": colors.lightcyan,
    "Physical Science": colors.lavender
}

# Subject abbreviations
subject_abbreviations = {
    "Life Orientation (L.O.)": "Life Orientation (L.O.)",
    "English Home Language": "Eng. Home Language",
    "Afrikaans First Additional Language": "Afr. First Additional Language",
    "Mathematics": "Mathematics",
    "Life Sciences": "Life Sciences",
    "Information Technology": "Information Technology",
    "Physical Science": "Physical Science"
}

# Custom colors
dark_grey = colors.Color(0.3, 0.3, 0.3)  # Dark grey for text
muted_grey = colors.Color(0.9, 0.9, 0.9)  # Muted grey for weekends

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

# Subject emojis (whimsical symbols for fun)
subject_emojis = {
    "Life Orientation (L.O.)": "🧭",  # Compass for life orientation
    "English Home Language": "📚",   # Books for English
    "Afrikaans First Additional Language": "🗣️",  # Speaking for Afrikaans
    "Mathematics": "🧮",              # Abacus for math
    "Life Sciences": "🧬",            # DNA for life sciences
    "Information Technology": "💻",   # Computer for IT
    "Physical Science": "⚗️"          # Test tube for physical science
}

def create_exam_paragraph(subject, exam):
    """Create a paragraph with emoji and text using different fonts"""
    emoji = subject_emojis[subject]
    subject_abbrev = subject_abbreviations[subject]
    paper = exam['paper']
    
    # Create paragraph with mixed fonts - emoji font for emoji, bold text font for text
    content = f'<font name="{EMOJI_FONT}">{emoji}</font> <font name="{TEXT_FONT}"><b>{subject_abbrev}<br/>{paper}</b></font>'
    
    # Create paragraph style
    style = ParagraphStyle(
        'ExamStyle',
        fontSize=9,  # Increased from 7 to 9
        textColor=dark_grey,
        alignment=TA_CENTER,
        leading=10  # Increased leading proportionally
    )
    
    return Paragraph(content, style)

def create_exam_summary_page(doc_elements):
    """Create the first page with exam summary tables side by side"""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER
    )

    # Title
    title = Paragraph("Grade 12 Exam Schedule Overview", title_style)
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

    # Create side-by-side layout with titles
    trial_title = Paragraph("<b>Trial Exams (September 2025)</b>", styles['Heading3'])
    final_title = Paragraph("<b>Final Exams (October-November 2025)</b>", styles['Heading3'])

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

def get_exam_for_datetime(dt):
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

def create_daily_planner_pages(doc_elements):
    """Create daily planner pages with 4 days per page"""
    start_date = datetime(2025, 8, 26)
    end_date = datetime(2025, 11, 29)
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

        for hour in range(7, 24):  # 7 AM to 11 PM
            if hour == 12:
                time_str = "12:00 PM"
            elif hour > 12:
                time_str = f"{hour-12}:00 PM"
            else:
                time_str = f"{hour}:00 AM"

            # Check for exams at this time for all days
            row_data = [time_str]
            for day in days:
                dt = day.replace(hour=hour, minute=0, second=0, microsecond=0)
                subject, exam = get_exam_for_datetime(dt)

                day_content = ""
                if subject and exam:
                    day_content = create_exam_paragraph(subject, exam)

                row_data.append(day_content)

            table_data.append(row_data)

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

        # Highlight exam blocks
        for row_idx, row_data in enumerate(table_data[1:], 1):
            for col_idx, day_content in enumerate(row_data[1:], 1):  # Skip time column
                if day_content:  # If there's content (Paragraph object), it's an exam
                    # For Paragraph objects, we need to check the text content
                    if hasattr(day_content, 'text'):
                        content_text = day_content.text
                    else:
                        content_text = str(day_content)
                    
                    # Find the subject to get the right color
                    for subject in subject_colors:
                        if subject_abbreviations[subject] in content_text:
                            table_style.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), subject_colors[subject]))
                            break

        day_table.setStyle(TableStyle(table_style))
        doc_elements.append(day_table)

        # Move to next set of days
        current_date += timedelta(days=4)

        # Add page break if not the last page
        if current_date <= end_date:
            doc_elements.append(PageBreak())

def generate_pdf():
    """Generate the complete PDF day planner"""
    filename = "Grade12_Exam_Day_Planner_2025.pdf"
    doc = SimpleDocTemplate(filename, pagesize=landscape(A4),
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)

    doc_elements = []

    # Create exam summary page
    create_exam_summary_page(doc_elements)

    # Create daily planner pages
    create_daily_planner_pages(doc_elements)

    # Build the PDF
    doc.build(doc_elements)
    print(f"PDF generated successfully: {filename}")

    return filename

def main():
    """Entry point for the exam-planner command"""
    generate_pdf()

if __name__ == "__main__":
    main()