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

# Unified exam data structure containing everything needed for rendering
exam_timetable = {
    "metadata": {
        "title": "Grade 12 Exam Schedule Overview",
        "year": 2025,
        "planner_start_date": "2025-09-01",
        "planner_end_date": "2025-11-29"
    },
    "exams": {
        "trial": {
            "display_name": "Trial Exams (September 2025)"
        },
        "final": {
            "display_name": "Final Exams (October-November 2025)"
        }
    },
    "subjects": {
        "Life Orientation (L.O.)": {
            "full_name": "Life Orientation (L.O.)",
            "abbreviation": "Life Orientation (L.O.)",
            "emoji": "🧭",
            "color": [0.68, 0.85, 1.0],  # RGB values for colors.lightblue
            "exam_types": {
                "trial": {
                    "exams": [
                        {
                            "paper": "CAT",
                            "start_datetime": "2025-09-01T09:00:00",
                            "end_datetime": "2025-09-01T11:30:00"
                        }
                    ]
                },
                "final": {
                    "exams": []
                }
            }
        },
        "English Home Language": {
            "full_name": "English Home Language",
            "abbreviation": "Eng. Home Language",
            "emoji": "📚",
            "color": [0.94, 0.5, 0.5],  # RGB values for colors.lightcoral
            "exam_types": {
                "trial": {
                    "exams": [
                        {
                            "paper": "Paper II",
                            "start_datetime": "2025-09-02T09:00:00",
                            "end_datetime": "2025-09-02T11:30:00"
                        },
                        {
                            "paper": "Paper III",
                            "start_datetime": "2025-09-09T09:00:00",
                            "end_datetime": "2025-09-09T12:00:00"
                        },
                        {
                            "paper": "Paper I",
                            "start_datetime": "2025-09-11T09:00:00",
                            "end_datetime": "2025-09-11T11:00:00"
                        }
                    ]
                },
                "final": {
                    "exams": [
                        {
                            "paper": "Paper 3",
                            "start_datetime": "2025-10-23T09:00:00",
                            "end_datetime": "2025-10-23T12:00:00"
                        },
                        {
                            "paper": "Paper 1",
                            "start_datetime": "2025-10-29T09:00:00",
                            "end_datetime": "2025-10-29T11:00:00"
                        },
                        {
                            "paper": "Paper 2",
                            "start_datetime": "2025-11-13T09:00:00",
                            "end_datetime": "2025-11-13T11:30:00"
                        }
                    ]
                }
            }
        },
        "Afrikaans First Additional Language": {
            "full_name": "Afrikaans First Additional Language",
            "abbreviation": "Afr. First Additional Language",
            "emoji": "🗣️",
            "color": [0.56, 0.93, 0.56],  # RGB values for colors.lightgreen
            "exam_types": {
                "trial": {
                    "exams": [
                        {
                            "paper": "Paper III",
                            "start_datetime": "2025-09-04T09:00:00",
                            "end_datetime": "2025-09-04T11:30:00"
                        },
                        {
                            "paper": "Paper II",
                            "start_datetime": "2025-09-12T09:00:00",
                            "end_datetime": "2025-09-12T11:00:00"
                        },
                        {
                            "paper": "Paper I",
                            "start_datetime": "2025-09-18T09:00:00",
                            "end_datetime": "2025-09-18T11:00:00"
                        }
                    ]
                },
                "final": {
                    "exams": [
                        {
                            "paper": "Paper 3",
                            "start_datetime": "2025-10-24T09:00:00",
                            "end_datetime": "2025-10-24T11:30:00"
                        },
                        {
                            "paper": "Paper 1",
                            "start_datetime": "2025-11-11T09:00:00",
                            "end_datetime": "2025-11-11T11:00:00"
                        },
                        {
                            "paper": "Paper 2",
                            "start_datetime": "2025-11-21T09:00:00",
                            "end_datetime": "2025-11-21T11:30:00"
                        }
                    ]
                }
            }
        },
        "Mathematics": {
            "full_name": "Mathematics",
            "abbreviation": "Mathematics",
            "emoji": "🧮",
            "color": [1.0, 1.0, 0.88],  # RGB values for colors.lightyellow
            "exam_types": {
                "trial": {
                    "exams": [
                        {
                            "paper": "Paper I",
                            "start_datetime": "2025-09-08T09:00:00",
                            "end_datetime": "2025-09-08T12:00:00"
                        },
                        {
                            "paper": "Paper II",
                            "start_datetime": "2025-09-22T09:00:00",
                            "end_datetime": "2025-09-22T12:00:00"
                        }
                    ]
                },
                "final": {
                    "exams": [
                        {
                            "paper": "Paper 1",
                            "start_datetime": "2025-10-31T09:00:00",
                            "end_datetime": "2025-10-31T12:00:00"
                        },
                        {
                            "paper": "Paper 2",
                            "start_datetime": "2025-11-03T09:00:00",
                            "end_datetime": "2025-11-03T12:00:00"
                        }
                    ]
                }
            }
        },
        "Life Sciences": {
            "full_name": "Life Sciences",
            "abbreviation": "Life Sciences",
            "emoji": "🧬",
            "color": [1.0, 0.71, 0.76],  # RGB values for colors.lightpink
            "exam_types": {
                "trial": {
                    "exams": [
                        {
                            "paper": "Paper I",
                            "start_datetime": "2025-09-04T13:00:00",
                            "end_datetime": "2025-09-04T15:30:00"
                        },
                        {
                            "paper": "Paper II",
                            "start_datetime": "2025-09-17T09:00:00",
                            "end_datetime": "2025-09-17T11:30:00"
                        }
                    ]
                },
                "final": {
                    "exams": [
                        {
                            "paper": "Paper 1",
                            "start_datetime": "2025-11-14T09:00:00",
                            "end_datetime": "2025-11-14T11:30:00"
                        },
                        {
                            "paper": "Paper 2",
                            "start_datetime": "2025-11-17T09:00:00",
                            "end_datetime": "2025-11-17T11:30:00"
                        }
                    ]
                }
            }
        },
        "Information Technology": {
            "full_name": "Information Technology",
            "abbreviation": "Information Technology",
            "emoji": "💻",
            "color": [0.88, 1.0, 1.0],  # RGB values for colors.lightcyan
            "exam_types": {
                "trial": {
                    "exams": [
                        {
                            "paper": "Paper II (Theory)",
                            "start_datetime": "2025-09-09T13:30:00",
                            "end_datetime": "2025-09-09T16:30:00"
                        },
                        {
                            "paper": "Paper I (Practical)",
                            "start_datetime": "2025-09-10T09:00:00",
                            "end_datetime": "2025-09-10T12:00:00"
                        }
                    ]
                },
                "final": {
                    "exams": [
                        {
                            "paper": "Paper 1 (Practical)",
                            "start_datetime": "2025-10-22T09:00:00",
                            "end_datetime": "2025-10-22T12:00:00"
                        },
                        {
                            "paper": "Paper 2 (Theory)",
                            "start_datetime": "2025-11-13T14:00:00",
                            "end_datetime": "2025-11-13T17:00:00"
                        },
                        {
                            "paper": "Practical Rewrite",
                            "start_datetime": "2025-11-27T09:00:00",
                            "end_datetime": "2025-11-27T12:00:00"
                        }
                    ]
                }
            }
        },
        "Physical Science": {
            "full_name": "Physical Science",
            "abbreviation": "Physical Science",
            "emoji": "⚗️",
            "color": [0.9, 0.9, 0.98],  # RGB values for colors.lavender
            "exam_types": {
                "trial": {
                    "exams": [
                        {
                            "paper": "Paper I (Physics)",
                            "start_datetime": "2025-09-15T09:00:00",
                            "end_datetime": "2025-09-15T12:00:00"
                        },
                        {
                            "paper": "Paper II (Chemistry)",
                            "start_datetime": "2025-09-25T09:00:00",
                            "end_datetime": "2025-09-25T12:00:00"
                        }
                    ]
                },
                "final": {
                    "exams": [
                        {
                            "paper": "Paper 1 (Physics)",
                            "start_datetime": "2025-11-07T09:00:00",
                            "end_datetime": "2025-11-07T12:00:00"
                        },
                        {
                            "paper": "Paper 2 (Chemistry)",
                            "start_datetime": "2025-11-10T09:00:00",
                            "end_datetime": "2025-11-10T12:00:00"
                        }
                    ]
                }
            }
        }
    }
}

# Custom colors
dark_grey = colors.Color(0.3, 0.3, 0.3)  # Dark grey for text
muted_grey = colors.Color(0.9, 0.9, 0.9)  # Muted grey for weekends

def convert_to_legacy_format():
    """Convert unified structure to legacy format for backward compatibility"""
    trial_exams_converted = {}
    final_exams_converted = {}
    subject_colors_converted = {}
    subject_abbreviations_converted = {}
    subject_emojis_converted = {}
    
    for subject_name, subject_data in exam_timetable["subjects"].items():
        # Extract subject info
        subject_colors_converted[subject_name] = colors.Color(*subject_data["color"])
        subject_abbreviations_converted[subject_name] = subject_data["abbreviation"]
        subject_emojis_converted[subject_name] = subject_data["emoji"]
        
        # Extract trial exams
        trial_exams_converted[subject_name] = []
        for exam in subject_data["exam_types"]["trial"]["exams"]:
            trial_exams_converted[subject_name].append({
                "paper": exam["paper"],
                "start": datetime.fromisoformat(exam["start_datetime"]),
                "end": datetime.fromisoformat(exam["end_datetime"])
            })
        
        # Extract final exams
        final_exams_converted[subject_name] = []
        for exam in subject_data["exam_types"]["final"]["exams"]:
            final_exams_converted[subject_name].append({
                "paper": exam["paper"],
                "start": datetime.fromisoformat(exam["start_datetime"]),
                "end": datetime.fromisoformat(exam["end_datetime"])
            })
    
    return trial_exams_converted, final_exams_converted, subject_colors_converted, subject_abbreviations_converted, subject_emojis_converted

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

# Convert unified structure to legacy format for backward compatibility
trial_exams, final_exams, subject_colors, subject_abbreviations, subject_emojis = convert_to_legacy_format()

# Legacy variables are now generated from the unified structure above

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
    year = exam_timetable['metadata']['year']
    filename = f"Grade12_Exam_Day_Planner_{year}.pdf"
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

def export_exam_data_to_json():
    """Export the exam timetable data to JSON file"""
    filename = "exam_timetable.json"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(exam_timetable, f, indent=2, ensure_ascii=False)
        print(f"Exam data exported to: {filename}")
    except Exception as e:
        print(f"Failed to export exam data: {e}")

def main():
    """Entry point for the exam-planner command"""
    # Export exam data to JSON
    export_exam_data_to_json()
    
    # Generate PDF
    generate_pdf()

if __name__ == "__main__":
    main()