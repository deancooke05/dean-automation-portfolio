from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

NAVY = "142B3A"
INK = "1B2730"
STEEL = "50697A"
MIST = "EEF2F4"
PEARL = "F8FAFB"
WHITE = "FFFFFF"
GOLD = "B79A62"
GREEN = "3E7562"
LINE = "D8E0E5"

FONT = "Aptos"
thin = Side(style="thin", color=LINE)
medium_navy = Side(style="medium", color=NAVY)

def fill(colour): return PatternFill("solid", fgColor=colour)
def font(size=11, bold=False, colour=INK, italic=False):
    return Font(name=FONT, size=size, bold=bold, color=colour, italic=italic)
def border(outside=False):
    side = medium_navy if outside else thin
    return Border(left=side, right=side, top=side, bottom=side)
def align(horizontal="left", vertical="center", wrap=False):
    return Alignment(horizontal=horizontal, vertical=vertical, wrap_text=wrap)
