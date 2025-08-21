import io
import os
from pathlib import Path
import streamlit as st
import fitz  # PyMuPDF

# ---------- CONFIG ----------
PAGE_NUMBER_1BASED = 4  # the page the user wants to edit
OLD_NAME  = " (นางธนาภรณ์ พลอยวิเศษ )"
OLD_TEAM  = "People and Organizational Development Team"
NEW_NAME  = " (นายเจษฎากร สมิทธิอรรถกร)"
NEW_TITLE = "Chief Executive Officer"

# Put your Thai-capable font here (TTF)
# e.g. fonts/NotoSansThai-Regular.ttf  (recommended)
FONT_PATH = "fonts/NotoSansThai-Regular.ttf"

# Appearance
NAME_FONTSIZE  = 12
TITLE_FONTSIZE = 11
PADDING_MULTIPLIER = 0.2  # enlarge redaction box slightly for safety
LINE_HEIGHT = 1.25

# ---------- HELPERS ----------
def ensure_font_exists(path: str):
    if not os.path.exists(path):
        st.warning(
            f"Font not found at '{path}'. "
            "Please put a Thai-capable .ttf in a 'fonts/' folder and update FONT_PATH."
        )

def pad_rect(r: fitz.Rect, pad_ratio: float):
    """Expand a rect by a ratio of its height to avoid clipping."""
    pad_y = r.height * pad_ratio
    pad_x = r.width * pad_ratio
    return fitz.Rect(r.x0 - pad_x, r.y0 - pad_y, r.x1 + pad_x, r.y1 + pad_y)

def redact_then_write(page, old_text, new_text, font_path, fontsize):
    """
    - Find all occurrences of old_text on the page
    - Redact them (white)
    - Insert new_text centered in the redacted area (wrap if needed)
    """
    found_rects = page.search_for(old_text)
    if not found_rects:
        return 0

    # Create redactions with a bit of padding
    for r in found_rects:
        pr = pad_rect(r, PADDING_MULTIPLIER)
        page.add_redact_annot(pr, fill=(1, 1, 1))  # white box

    # Apply all redactions at once
    page.apply_redactions()

    # Insert new text centered in the original region
    for r in found_rects:
        pr = pad_rect(r, PADDING_MULTIPLIER)
        # Use fontfile argument to embed the Thai font
        page.insert_textbox(
            pr,
            new_text,
            fontsize=fontsize,
            fontname="customthai",
            fontfile=font_path,
            color=(0, 0, 0),
            align=1,  # 0=left, 1=center, 2=right, 3=justify
            lineheight=LINE_HEIGHT
        )
    return len(found_rects)

# ---------- UI ----------
st.set_page_config(page_title="PDF Text Replacer (Page 4)", page_icon="📝", layout="centered")
st.title("PDF Text Replacer — Page 4")

st.write(
    "Upload a PDF. The app will **find and replace on page 4**:\n"
    f"- `{OLD_NAME}` → `{NEW_NAME}`\n"
    f"- `{OLD_TEAM}` → `{NEW_TITLE}`"
)

ensure_font_exists(FONT_PATH)

uploaded = st.file_uploader("Upload your PDF", type=["pdf"])
if uploaded:
    try:
        pdf_bytes = uploaded.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        # Zero-based index for PyMuPDF
        target_index = PAGE_NUMBER_1BASED - 1
        if target_index < 0 or target_index >= len(doc):
            st.error(f"PDF has only {len(doc)} pages. Page {PAGE_NUMBER_1BASED} doesn't exist.")
        else:
            page = doc[target_index]

            # First pass: replace the Thai name
            n1 = redact_then_write(page, OLD_NAME, NEW_NAME, FONT_PATH, NAME_FONTSIZE)
            # Second pass: replace the English team line
            n2 = redact_then_write(page, OLD_TEAM, NEW_TITLE, FONT_PATH, TITLE_FONTSIZE)

            # Save to buffer
            out_buf = io.BytesIO()
            # Clean & optimize a bit
            doc.save(out_buf, garbage=4, deflate=True, incremental=False)
            doc.close()
            out_buf.seek(0)

            st.success(
                f"Done! Replaced occurrences on page {PAGE_NUMBER_1BASED}: "
                f"{OLD_NAME} → {NEW_NAME}: {n1} match(es); "
                f"{OLD_TEAM} → {NEW_TITLE}: {n2} match(es)."
            )
            st.download_button(
                "⬇️ Download updated PDF",
                data=out_buf,
                file_name=f"updated_{uploaded.name}",
                mime="application/pdf"
            )

            with st.expander("What if it doesn't line up perfectly?"):
                st.write(
                    "- This uses exact text search. If your source PDF has slightly different spacing or hidden characters, "
                    "you may need to tweak the `OLD_*` strings (e.g., extra spaces). "
                    "You can also lower the strictness by normalizing spaces before searching."
                )

    except Exception as e:
        st.error(f"Error processing PDF: {e}")
else:
    st.info("Upload a PDF to begin.")
