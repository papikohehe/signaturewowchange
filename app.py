import io, os, unicodedata
from pathlib import Path
import streamlit as st
import fitz  # PyMuPDF

# ---------- CONFIG ----------
PAGE_NUMBER_1BASED = 4
OLD_NAME_VARIANTS = [
    "(นางธนาภรณ์ พลอยวิเศษ )",
    " (นางธนาภรณ์ พลอยวิเศษ )",
    "(นางธนาภรณ์ พลอยวิเศษ)",
    " (นางธนาภรณ์ พลอยวิเศษ)",
    "（นางธนาภรณ์ พลอยวิเศษ）",       # full-width parens
    " （นางธนาภรณ์ พลอยวิเศษ）",
]
OLD_TEAM  = "People and Organizational Development Team"
NEW_NAME  = " (นายเจษฎากร สมิทธิอรรถกร)"
NEW_TITLE = "Chief Executive Officer"

# Use a Thai-capable TTF here
FONT_PATH = "fonts/NotoSansThai-Regular.ttf"  # or "fonts/THSarabunNew.ttf" / "fonts/angsa.ttf"

NAME_FONTSIZE  = 12
TITLE_FONTSIZE = 11
PADDING_MULTIPLIER = 0.22
LINE_HEIGHT = 1.25

# ---------- HELPERS ----------
def ensure_font_exists(path: str):
    if not os.path.exists(path):
        st.warning(f"Font not found at '{path}'. Put a Thai-capable .ttf there and update FONT_PATH.")
    elif not path.lower().endswith(".ttf"):
        st.warning("Your font file should be a .ttf (not .tff).")

def pad_rect(r: fitz.Rect, pad_ratio: float):
    pad_y = r.height * pad_ratio
    pad_x = r.width * pad_ratio
    return fitz.Rect(r.x0 - pad_x, r.y0 - pad_y, r.x1 + pad_x, r.y1 + pad_y)

def normalize_spaces(s: str) -> str:
    # Replace NBSP and other odd spaces with normal spaces
    return s.replace("\u00A0", " ").replace("\u2009", " ").replace("\u202F", " ")

def redact_then_write(page, old_text, new_text, font_path, fontsize):
    found_rects = page.search_for(old_text)
    if not found_rects:
        return 0
    for r in found_rects:
        pr = pad_rect(r, PADDING_MULTIPLIER)
        page.add_redact_annot(pr, fill=(1, 1, 1))
    page.apply_redactions()
    for r in found_rects:
        pr = pad_rect(r, PADDING_MULTIPLIER)
        page.insert_textbox(
            pr, new_text,
            fontsize=fontsize,
            fontname="customthai",
            fontfile=font_path,   # embeds the Thai font
            color=(0, 0, 0),
            align=1,
            lineheight=LINE_HEIGHT
        )
    return len(found_rects)

def try_thai_replacements(page, variants, new_text, font_path, fontsize):
    # try exact, then normalized-space versions
    total = 0
    report = []
    for v in variants:
        hits = redact_then_write(page, v, new_text, font_path, fontsize)
        report.append((v, hits))
        total += hits
        if hits == 0:
            nv = normalize_spaces(v)
            if nv != v:
                hits2 = redact_then_write(page, nv, new_text, font_path, fontsize)
                report.append((f"{nv} [normalized]", hits2))
                total += hits2
    return total, report

# ---------- UI ----------
st.set_page_config(page_title="PDF Text Replacer (Page 4)", page_icon="📝", layout="centered")
st.title("PDF Text Replacer — Page 4 (Thai-safe)")

ensure_font_exists(FONT_PATH)
st.write(
    "I will replace on page 4:\n"
    f"- Thai name → `{NEW_NAME}`\n"
    f"- English title → `{NEW_TITLE}`"
)

uploaded = st.file_uploader("Upload your PDF", type=["pdf"])
show_debug = st.toggle("Show match details", value=True)

if uploaded:
    try:
        pdf_bytes = uploaded.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        idx = PAGE_NUMBER_1BASED - 1
        if idx < 0 or idx >= len(doc):
            st.error(f"PDF has only {len(doc)} pages. Page {PAGE_NUMBER_1BASED} doesn't exist.")
        else:
            page = doc[idx]

            # 1) Thai line (try robust variants)
            thai_total, details = try_thai_replacements(page, OLD_NAME_VARIANTS, NEW_NAME, FONT_PATH, NAME_FONTSIZE)

            # 2) English title
            title_hits = redact_then_write(page, OLD_TEAM, NEW_TITLE, FONT_PATH, TITLE_FONTSIZE)

            # Save
            out_buf = io.BytesIO()
            doc.save(out_buf, garbage=4, deflate=True, incremental=False)
            doc.close()
            out_buf.seek(0)

            st.success(f"Done. Thai replacements: {thai_total}; English replacements: {title_hits}.")
            if show_debug:
                st.caption("Match breakdown (variant → hits):")
                for v, h in details:
                    st.code(f"{v} -> {h}")

            st.download_button(
                "⬇️ Download updated PDF",
                data=out_buf,
                file_name=f"updated_{uploaded.name}",
                mime="application/pdf"
            )

            with st.expander("Still not finding the Thai line?"):
                st.write(
                    "- The source PDF may split Thai text into separate spans. In that case, try adding a shorter "
                    "variant such as `'พลอยวิเศษ'` to OLD_NAME_VARIANTS and it will still replace the same spot.\n"
                    "- Also ensure your font file is valid and has Thai glyphs (e.g., NotoSansThai, TH Sarabun, Angsana)."
                )

    except Exception as e:
        st.error(f"Error processing PDF: {e}")
else:
    st.info("Upload a PDF to begin.")
