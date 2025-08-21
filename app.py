import io
import os
import zipfile
import streamlit as st
import fitz  # PyMuPDF

# ---------------- CONFIG ----------------
PAGE_NUMBER_1BASED = 4
DEFAULT_ANCHOR = "People and Organizational Development Team"
DEFAULT_THAI   = "(         นายเจษฎากร สมิทธิอรรถกร        )"
DEFAULT_EN     = "Chief Executive Officer"

FONT_PATH = "fonts/NotoSansThai-Regular.ttf"
LINE_HEIGHT = 1.25
REDACT_PAD_RATIO = 0.12

# --------------- HELPERS ----------------
def ensure_font(path: str):
    if not os.path.exists(path):
        st.warning(f"Font not found at '{path}'. Put a Thai-capable .ttf there.")
    elif not path.lower().endswith(".ttf"):
        st.warning("Font file should be .ttf, not .tff")

def pad_rect(r: fitz.Rect, ratio: float) -> fitz.Rect:
    dx = r.width * ratio
    dy = r.height * ratio
    return fitz.Rect(r.x0 - dx, r.y0 - dy, r.x1 + dx, r.y1 + dy)

def replace_anchor(page, anchor, new_thai, new_en,
                   font_path, name_size, title_size,
                   above_top, above_bottom):
    rects = page.search_for(anchor)
    if not rects:
        return 0

    for r in rects:
        page.add_redact_annot(pad_rect(r, REDACT_PAD_RATIO), fill=(1, 1, 1))
    page.apply_redactions()

    for r in rects:
        h = r.height
        name_rect = fitz.Rect(
            r.x0, r.y0 - h * above_top,
            r.x1, r.y0 - h * above_bottom
        )

        page.insert_textbox(
            name_rect,
            new_thai,
            fontsize=name_size,
            fontname="customthai",
            fontfile=font_path,
            color=(0, 0, 0),
            align=1,
            lineheight=LINE_HEIGHT
        )

        page.insert_textbox(
            r,
            new_en,
            fontsize=title_size,
            fontname="customthai",
            fontfile=font_path,
            color=(0, 0, 0),
            align=1,
            lineheight=LINE_HEIGHT
        )
    return len(rects)

def process_pdf(pdf_bytes, params, return_preview=False):
    """Apply replacement to one PDF and return buffer (+preview if requested)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    idx = params["page_num"] - 1
    if idx < 0 or idx >= len(doc):
        return None, None

    page = doc[idx]
    _ = replace_anchor(
        page,
        params["anchor"],
        params["thai"],
        params["en"],
        params["font_path"],
        params["name_size"],
        params["title_size"],
        params["above_top"],
        params["above_bottom"]
    )

    preview_png = None
    if return_preview:
        preview_png = page.get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes("png")

    out_buf = io.BytesIO()
    doc.save(out_buf, garbage=4, deflate=True, incremental=False)
    doc.close()
    out_buf.seek(0)

    return out_buf, preview_png

# ------------------ UI -------------------
st.set_page_config(page_title="Bulk PDF Text Replace", page_icon="📝", layout="centered")
st.title("Bulk PDF Text Replace — Page 4")

st.write(
    "1. Upload **one PDF** first → adjust texts, fonts, and placement with preview.\n"
    "2. Then upload multiple PDFs → same parameters will be applied to all.\n"
    "3. Download each file or all as a ZIP."
)

ensure_font(FONT_PATH)

# --- Sidebar controls ---
st.sidebar.header("Replacement Parameters")

anchor_text = st.sidebar.text_input("Anchor text (search target)", DEFAULT_ANCHOR)
thai_text   = st.sidebar.text_input("Thai text (above)", DEFAULT_THAI)
en_text     = st.sidebar.text_input("English text (replace anchor)", DEFAULT_EN)

name_size  = st.sidebar.slider("Thai font size", 8, 14, 10)
title_size = st.sidebar.slider("English font size", 8, 14, 10)

above_top    = st.sidebar.slider("Thai position (top factor)", 0.5, 1.5, 0.9, 0.05)
above_bottom = st.sidebar.slider("Thai position (bottom factor)", -0.5, 0.5, -0.1, 0.05)

show_preview = st.checkbox("Show preview (for first file)", value=True)

params = {
    "page_num": PAGE_NUMBER_1BASED,
    "anchor": anchor_text,
    "thai": thai_text,
    "en": en_text,
    "font_path": FONT_PATH,
    "name_size": name_size,
    "title_size": title_size,
    "above_top": above_top,
    "above_bottom": above_bottom
}

# --- Single file preview ---
uploaded_single = st.file_uploader("Step 1: Upload a single PDF to tune parameters", type=["pdf"])
if uploaded_single:
    out_buf, preview_png = process_pdf(uploaded_single.read(), params, return_preview=show_preview)
    if out_buf:
        st.success("Applied replacement on this file.")
        if show_preview and preview_png:
            st.image(preview_png, caption="Preview of Page 4")
        st.download_button(
            "⬇️ Download updated single PDF",
            data=out_buf,
            file_name=f"updated_{uploaded_single.name}",
            mime="application/pdf"
        )
    else:
        st.error("Could not process this PDF.")

# --- Bulk upload ---
uploaded_bulk = st.file_uploader("Step 2: Upload multiple PDFs for bulk processing", type=["pdf"], accept_multiple_files=True)
if uploaded_bulk:
    st.info(f"Processing {len(uploaded_bulk)} files with the tuned parameters...")

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zipf:
        for file in uploaded_bulk:
            out_buf, _ = process_pdf(file.read(), params, return_preview=False)
            if out_buf:
                # Add to ZIP
                zipf.writestr(f"updated_{file.name}", out_buf.getvalue())
                # Individual download button
                st.download_button(
                    f"⬇️ Download updated {file.name}",
                    data=out_buf,
                    file_name=f"updated_{file.name}",
                    mime="application/pdf"
                )
            else:
                st.error(f"Could not process {file.name}")

    zip_buf.seek(0)
    st.download_button(
        "⬇️ Download ALL as ZIP",
        data=zip_buf,
        file_name="updated_pdfs.zip",
        mime="application/zip"
    )
