from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register a font that supports emoji
pdfmetrics.registerFont(TTFont('NotoEmoji', 'NotoEmoji-Regular.ttf'))
c = canvas.Canvas("test.pdf")
c.setFont('NotoEmoji', 12)
c.drawString(100, 750, "Hello 😀 World")
c.save()