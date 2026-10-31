"""Feet-and-inches formatting for furniture sizes and clearances (rounded to the nearest 1/8 inch)."""
from fractions import Fraction


def ftin(m, step=8):
    """0.6 -> 1'-11 5/8\" ; negative values keep their sign."""
    sign = "-" if m < 0 else ""
    total = round(abs(m) / 0.0254 * step) / step
    ft = int(total // 12)
    inch = total - ft * 12
    whole = int(inch)
    frac = Fraction(inch - whole).limit_denominator(step)
    if frac == 1:
        whole, frac = whole + 1, Fraction(0)
    if whole == 12:
        ft, whole = ft + 1, 0
    s = f"{whole}" + (f" {frac.numerator}/{frac.denominator}" if frac else "")
    return f"{sign}{ft}'-{s}\""


def size(w, d):
    return f"{ftin(w)} x {ftin(d)}"
