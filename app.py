import io
import os
from pathlib import Path
import streamlit as st
import fitz  # PyMuPDF

# ---------------- CONFIG ----------------
PAGE_NUMBER_1BASED = 4

OLD_TEAM  = "People and Organizational Development Team"
NEW_NAME  = " (นายเจษฎากร สมิทธิอรรถกร)"
NEW_TITLE = "Chief Executive Officer"

# A Thai-capable TTF (put it in ./fonts/)
# e.g. fonts/NotoSansThai-Regular.ttf, fonts/THSarabunNew.ttf, or fonts/angsa.ttf
FONT_PATH = "fonts/NotoSansThai-Regular.ttf"

NAME_FONTSIZE  = 12
TITLE_FONTSIZE = 11
LINE_HEIGHT    = 1.25

# How far above the English line to place the Thai line (in relation to the English bbox height)
NAME_ABOVE_FACTOR_TOP  = 1.25   # top edge above
NAME_ABOVE_FACTOR_BOTTOM = 0.15 # bottom edge above

# Slight padding when redacting the English text
REDACT_PAD_RATIO = 0.12

# --------------- HELPERS ----------------
def ensure_font(path: str):
    if not os.path.exists(path):
        st.warning(
            f"Font not found at '{path}'. Put a Thai-capable .ttf there and update FONT_PATH."
        )
    elif not path.lower().endswith(".ttf"):
        st.warning("Your font file should be a .ttf (not .tff).")

def pad_rect(r: fitz.Rect, ratio: float) -> fitz.Rect:
    dx = r.width * ratio
    dy = r.height * ratio
    return fitz.Rect(r.x0 - dx, r.y0 - dy, r.x1 + dx, r.y1 + dy)

def replace_team_with_name_and_title(page, old_team, new_name, new_title,
                                     font_path, name_size, title_size) -> int:
    # Find the English anchor
    rects = page.search_for(old_team)
    if not rects:
        return 0

    # Redact found English text
    for r in rects:
        page.add_redact_annot(pad_rect(r, REDACT_PAD_RATIO), fill=(1, 1, 1))
    page.apply_redactions()

    # Draw Thai name above, and English title in place
    for r in rects:
        # Rectangle for Thai name just above the original English bbox
        # Use proportional vertical shift based on the found rect height so it adapts to different PDFs
        h = r.height
        name_rect = fitz.Rect(r.x0, r.y0 - h * NAME_ABOVE_FACTOR_TOP,
                              r.x1, r.y0 - h * NAME_ABOVE_FACTOR_BOTTOM)

        # Thai name (centered)
        page.insert_textbox(
            name_rect,
            new_name,
            fontsize=name_size,
            fontname="customthai",
            fontfile=font_path,   # embed Thai-capable font
            color=(0, 0, 0),
            align=1,              # center
            lineheight=LINE_HEIGHT
        )

        # English title in place of old text (centered)
        page.insert_textbox(
            r,
            new_title,
            fontsize=title_size,
            fontname="customthai",
            fontfile=font_path,
            color=(0, 0, 0),
            align=1,
            lineheight=LINE_HEIGHT
        )
    return len(rects)

# ------------------ UI -------------------
st.set_page_config(page_title="PDF Anchor Replace (Page 4)", page_icon="📝", layout="centered")
st.title("PDF Text Replace via Anchor — Page 4")

st.write(
    "This app finds **'People and Organizational Development Team'** on page 4, "
    "replaces it with **'Chief Executive Officer'**, and inserts the Thai name **above** it.\n\n"
    f"- New Thai line: `{NEW_NAME}`\n"
    f"- New English line: `{NEW_TITLE}`"
)

ensure_font(FONT_PATH)

uploaded = st.file_uploader("Upload your PDF", type=["pdf"])
if uploaded:
    try:
        pdf_bytes = uploaded.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        idx = PAGE_NUMBER_1BASED - 1
        if idx < 0 or idx >= len(doc):
            st.error(f"PDF has {len(doc)} page(s). Page {PAGE_NUMBER_1BASED} doesn't exist.")
        else:
            page = doc[idx]

            hits = replace_team_with_name_and_title(
                page,
                OLD_TEAM,
                NEW_NAME,
                NEW_TITLE,
                FONT_PATH,
                NAME_FONTSIZE,
                TITLE_FONTSIZE
            )

            out_buf = io.BytesIO()
            doc.save(out_buf, garbage=4, deflate=True, incremental=False)
            doc.close()
            out_buf.seek(0)

            if hits == 0:
                st.warning(
                    "Could not find the English anchor text on page 4. "
                    "Check spelling/spaces or confirm it’s on page 4."
                )
            else:
                st.success(
                    f"Done! Replaced English line and inserted Thai name above. Matches on page 4: {hits}"
                )
                st.download_button(
                    "⬇️ Download updated PDF",
                    data=out_buf,
                    file_name=f"updated_{uploaded.name}",
                    mime="application/pdf"
                )

            with st.expander("Adjust spacing if needed"):
                st.write(
                    "- If the Thai line is too close/far from the title, tweak "
                    "`NAME_ABOVE_FACTOR_TOP` and `NAME_ABOVE_FACTOR_BOTTOM`.\n"
                    "- If the redaction clips the old English baseline, increase `REDACT_PAD_RATIO`."
                )

    except Exception as e:
        st.error(f"Error processing PDF: {e}")
else:
    st.info("Upload a PDF to begin.")
