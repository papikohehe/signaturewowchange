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

FONTS_DIR = "fonts"
LINE_HEIGHT = 1.25
REDACT_PAD_RATIO = 0.12

# --------------- HELPERS ----------------
def list_fonts():
    """List available TTF fonts in fonts/ directory."""
    if not os.path.exists(FONTS_DIR):
        return []
    return [f for f in os.listdir(FONTS_DIR) if f.lower().endswith(".ttf")]

def pad_rect(r: fitz.Rect, ratio: float) -> fitz.Rect:
    dx = r.width * ratio
    dy = r.height * ratio
    return fitz.Rect(r.x0 - dx, r.y0 - dy, r.x1 + dx, r.y1 + dy)

def expand_rect_for_font(rect: fitz.Rect, font_size: int, base_size: int = 10) -> fitz.Rect:
    """Expand rectangle height depending on font size so text never disappears."""
    scale_factor = font_size / base_size
    if scale_factor <= 1:
        return rect
    extra = rect.height * (scale_factor - 1) * 1.2
    return fitz.Rect(rect.x0, rect.y0 - extra, rect.x1, rect.y1 + extra)

def safe_expand_rect(r: fitz.Rect, font_size: int) -> fitz.Rect:
    """Guarantee rect has enough height for text (avoid disappearing when shifted)."""
    rect = expand_rect_for_font(r, font_size)
    min_height = font_size * 2  # ensure tall enough
    if rect.height < min_height:
        rect = fitz.Rect(rect.x0, rect.y0 - min_height/2, rect.x1, rect.y0 + min_height/2)
    return rect

def replace_anchor(page, anchor, new_thai, new_en,
                   font_path, name_size, title_size,
                   t_top, t_bottom, e_top, e_bottom):
    rects = page.search_for(anchor)
    if not rects:
        return 0

    for r in rects:
        page.add_redact_annot(pad_rect(r, REDACT_PAD_RATIO), fill=(1, 1, 1))
    page.apply_redactions()

    for r in rects:
        h = r.height

        # Thai rect
        thai_rect = fitz.Rect(
            r.x0, r.y0 - h * t_top,
            r.x1, r.y0 - h * t_bottom
        )
        thai_rect = safe_expand_rect(thai_rect, name_size)

        page.insert_textbox(
            thai_rect,
            new_thai,
            fontsize=name_size,
            fontname="customthai",
            fontfile=font_path,
            color=(0, 0, 0),
            align=1,
            lineheight=LINE_HEIGHT
        )

        # English rect
        en_rect = fitz.Rect(
            r.x0, r.y0 - h * e_top,
            r.x1, r.y0 - h * e_bottom
        )
        en_rect = safe_expand_rect(en_rect, title_size)

        page.insert_textbox(
            en_rect,
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
        params["t_top"],
        params["t_bottom"],
        params["e_top"],
        params["e_bottom"]
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

# --- Sidebar controls ---
st.sidebar.header("Replacement Parameters")

anchor_text = st.sidebar.text_input("Anchor text (search target)", DEFAULT_ANCHOR)
thai_text   = st.sidebar.text_input("Thai text (above)", DEFAULT_THAI)
en_text     = st.sidebar.text_input("English text (replace anchor)", DEFAULT_EN)

# Font selection
available_fonts = list_fonts()
if available_fonts:
    default_idx = 0
    for i, f in enumerate(available_fonts):
        if f.lower() == "angsa1.ttf":  # preferred default
            default_idx = i
            break
    chosen_font = st.sidebar.selectbox("Choose font", available_fonts, index=default_idx)
    font_path = os.path.join(FONTS_DIR, chosen_font)
else:
    st.sidebar.error("No .ttf fonts found in fonts/ directory!")
    font_path = None

# Font sizes — expanded range
name_size  = st.sidebar.slider("Thai font size", 8, 40, 15)
title_size = st.sidebar.slider("English font size", 8, 40, 15)

# Thai positioning
t_top    = st.sidebar.slider("Thai position (top factor)", 0.5, 2.0, 0.75, 0.05)
t_bottom = st.sidebar.slider("Thai position (bottom factor)", -0.5, 1.0, 0.10, 0.05)

# English positioning
e_top    = st.sidebar.slider("English position (top factor)", -0.5, 2.0, 0.0, 0.05)
e_bottom = st.sidebar.slider("English position (bottom factor)", -0.5, 2.0, 0.0, 0.05)

show_preview = st.checkbox("Show preview (for first file)", value=True)

params = {
    "page_num": PAGE_NUMBER_1BASED,
    "anchor": anchor_text,
    "thai": thai_text,
    "en": en_text,
    "font_path": font_path,
    "name_size": name_size,
    "title_size": title_size,
    "t_top": t_top,
    "t_bottom": t_bottom,
    "e_top": e_top,
    "e_bottom": e_bottom
}

# --- Single file preview ---
uploaded_single = st.file_uploader("Step 1: Upload a single PDF to tune parameters", type=["pdf"])
if uploaded_single and font_path:
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
if uploaded_bulk and font_path:
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
