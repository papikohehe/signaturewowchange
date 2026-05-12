import io
import os
import zipfile
import streamlit as st
import fitz  # PyMuPDF

# ---------------- CONFIG ----------------
DEFAULT_PAGE_NUMBER = 4
DEFAULT_NAME = "นางสาวปัณพร ใคยศรี"

FONTS_DIR = "fonts"
DEFAULT_FONT_SIZE = 16

# ---------------- HELPERS ----------------
def list_fonts():
    if not os.path.exists(FONTS_DIR):
        return []
    return [f for f in os.listdir(FONTS_DIR) if f.lower().endswith(".ttf")]


def fill_bottom_witness_name(page, new_name, font_path, font_size, x_offset, y_offset, box_width):
    """
    Finds all 'พยาน' text on the page.
    Uses only the bottom-most one.
    Inserts name inside the existing parentheses below the line.
    Does NOT add new parentheses.
    """

   witness_rects = page.search_for("พยาน")

if witness_rects:
    # Use bottom-most พยาน
    target = max(witness_rects, key=lambda r: r.y0)

    name_rect = fitz.Rect(
        target.x0 - box_width + x_offset,
        target.y1 + 22 + y_offset,
        target.x1 + 10 + x_offset,
        target.y1 + 55 + y_offset,
    )

else:
    # Fallback fixed position near bottom of page
    page_width = page.rect.width
    page_height = page.rect.height

    name_rect = fitz.Rect(
        (page_width / 2) - 180 + x_offset,
        page_height - 140 + y_offset,
        (page_width / 2) + 180 + x_offset,
        page_height - 100 + y_offset,
    )

    page.insert_textbox(
        name_rect,
        new_name,
        fontsize=font_size,
        fontname="customthai",
        fontfile=font_path,
        color=(0, 0, 0),
        align=1,
    )

    return 1


def process_pdf(pdf_bytes, params, return_preview=False):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    page_index = params["page_num"] - 1
    if page_index < 0 or page_index >= len(doc):
        return None, None, 0

    page = doc[page_index]

    count = fill_bottom_witness_name(
        page=page,
        new_name=params["name"],
        font_path=params["font_path"],
        font_size=params["font_size"],
        x_offset=params["x_offset"],
        y_offset=params["y_offset"],
        box_width=params["box_width"],
    )

    preview_png = None
    if return_preview:
        preview_png = page.get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes("png")

    out_buf = io.BytesIO()
    doc.save(out_buf, garbage=4, deflate=True, incremental=False)
    doc.close()
    out_buf.seek(0)

    return out_buf, preview_png, count


# ---------------- UI ----------------
st.set_page_config(
    page_title="PDF Bottom Witness Name Filler",
    page_icon="📝",
    layout="centered",
)

st.title("PDF Bottom Witness Name Filler")

st.sidebar.header("Settings")

page_num = st.sidebar.number_input(
    "Page number",
    min_value=1,
    value=DEFAULT_PAGE_NUMBER,
    step=1,
)

name_text = st.sidebar.text_input(
    "Name to fill",
    DEFAULT_NAME,
)

available_fonts = list_fonts()

if available_fonts:
    default_idx = 0
    for i, f in enumerate(available_fonts):
        if f.lower() == "angsa1.ttf":
            default_idx = i
            break

    chosen_font = st.sidebar.selectbox(
        "Choose font",
        available_fonts,
        index=default_idx,
    )

    font_path = os.path.join(FONTS_DIR, chosen_font)

else:
    st.sidebar.error("No .ttf fonts found in fonts/ folder.")
    font_path = None

font_size = st.sidebar.slider("Font size", 8, 40, DEFAULT_FONT_SIZE)

st.sidebar.subheader("Position Adjustment")

x_offset = st.sidebar.slider("Move left/right", -200, 200, 61)
y_offset = st.sidebar.slider("Move up/down", -100, 100, -19)
box_width = st.sidebar.slider("Text box width", 100, 500, 330)

show_preview = st.checkbox("Show preview for first file", value=True)

params = {
    "page_num": page_num,
    "name": name_text,
    "font_path": font_path,
    "font_size": font_size,
    "x_offset": x_offset,
    "y_offset": y_offset,
    "box_width": box_width,
}

uploaded_single = st.file_uploader(
    "Step 1: Upload single PDF to test",
    type=["pdf"],
)

if uploaded_single and font_path:
    out_buf, preview_png, count = process_pdf(
        uploaded_single.read(),
        params,
        return_preview=show_preview,
    )

    if out_buf:
        st.success(f"Done. Filled {count} bottom witness field.")

        if count == 0:
            st.warning("No 'พยาน' text found on this page.")

        if show_preview and preview_png:
            st.image(preview_png, caption=f"Preview of Page {page_num}")

        st.download_button(
            "⬇️ Download updated PDF",
            data=out_buf,
            file_name=f"updated_{uploaded_single.name}",
            mime="application/pdf",
        )

uploaded_bulk = st.file_uploader(
    "Step 2: Upload multiple PDFs",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded_bulk and font_path:
    zip_buf = io.BytesIO()

    with zipfile.ZipFile(zip_buf, "w") as zipf:
        for file in uploaded_bulk:
            out_buf, _, count = process_pdf(
                file.read(),
                params,
                return_preview=False,
            )

            if out_buf:
                zipf.writestr(f"updated_{file.name}", out_buf.getvalue())
                st.write(f"{file.name}: filled {count} bottom witness field")
            else:
                st.error(f"Could not process {file.name}")

    zip_buf.seek(0)

    st.download_button(
        "⬇️ Download ALL as ZIP",
        data=zip_buf,
        file_name="updated_pdfs.zip",
        mime="application/zip",
    )
