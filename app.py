import io
import os
import streamlit as st
import fitz  # PyMuPDF

# ---------------- CONFIG ----------------
PAGE_NUMBER_1BASED = 4
OLD_TEAM  = "People and Organizational Development Team"
NEW_NAME  = " (นายเจษฎากร สมิทธิอรรถกร)"
NEW_TITLE = "Chief Executive Officer"

# A Thai-capable TTF (put in ./fonts/)
FONT_PATH = "fonts/NotoSansThai-Regular.ttf"

LINE_HEIGHT = 1.25
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
                                     font_path, name_size, title_size,
                                     above_top, above_bottom):
    rects = page.search_for(old_team)
    if not rects:
        return 0

    for r in rects:
        page.add_redact_annot(pad_rect(r, REDACT_PAD_RATIO), fill=(1, 1, 1))
    page.apply_redactions()

    for r in rects:
        h = r.height
        # Position Thai name relative to found rect
        name_rect = fitz.Rect(
            r.x0, r.y0 - h * above_top,
            r.x1, r.y0 - h * above_bottom
        )

        # Thai name
        page.insert_textbox(
            name_rect,
            new_name,
            fontsize=name_size,
            fontname="customthai",
            fontfile=font_path,
            color=(0, 0, 0),
            align=1,
            lineheight=LINE_HEIGHT
        )

        # English title
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
st.title("PDF Text Replace via Anchor — Page 4 (Live Preview)")

st.write(
    "This app finds **'People and Organizational Development Team'** on page 4, "
    "replaces it with **'Chief Executive Officer'**, and inserts the Thai name **above** it.\n\n"
    "👉 Use sliders to adjust font size and placement, then preview the result live."
)

ensure_font(FONT_PATH)

uploaded = st.file_uploader("Upload your PDF", type=["pdf"])

# --- Sliders ---
st.sidebar.header("Adjust Placement & Size")
NAME_FONTSIZE  = st.sidebar.slider("Thai font size", 8, 14, 10)
TITLE_FONTSIZE = st.sidebar.slider("English font size", 8, 14, 10)
NAME_ABOVE_FACTOR_TOP = st.sidebar.slider("Thai position (top factor)", 0.5, 1.5, 0.9, 0.05)
NAME_ABOVE_FACTOR_BOTTOM = st.sidebar.slider("Thai position (bottom factor)", -0.5, 0.5, -0.1, 0.05)

show_preview = st.checkbox("Show live preview of page 4", value=True)

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
                TITLE_FONTSIZE,
                NAME_ABOVE_FACTOR_TOP,
                NAME_ABOVE_FACTOR_BOTTOM
            )

            if hits == 0:
                st.warning("Could not find the English anchor text on page 4.")
            else:
                st.success(f"Applied replacement (matches found: {hits}).")

                if show_preview:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for clarity
                    st.image(pix.tobytes("png"), caption="Preview of Page 4")

                out_buf = io.BytesIO()
                doc.save(out_buf, garbage=4, deflate=True, incremental=False)
                doc.close()
                out_buf.seek(0)

                st.download_button(
                    "⬇️ Download updated PDF",
                    data=out_buf,
                    file_name=f"updated_{uploaded.name}",
                    mime="application/pdf"
                )

    except Exception as e:
        st.error(f"Error processing PDF: {e}")
else:
    st.info("Upload a PDF to begin.")
