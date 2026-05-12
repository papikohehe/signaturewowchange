import io
import os
import zipfile
import streamlit as st
import fitz  # PyMuPDF

# ---------------- CONFIG ----------------
PAGE_NUMBER_1BASED = 4

DEFAULT_NAME = "นางสาวปัณพร ใคยศรี"

FONTS_DIR = "fonts"
DEFAULT_FONT_SIZE = 16

# Adjust these if text appears too high/low
Y_OFFSET = 0
X_OFFSET = 0

# ---------------- HELPERS ----------------
def list_fonts():
    if not os.path.exists(FONTS_DIR):
        return []
    return [f for f in os.listdir(FONTS_DIR) if f.lower().endswith(".ttf")]


def find_parentheses_blanks(page):
    """
    Finds blank name fields that look like:
    (                )
    """
    words = page.get_text("words")
    results = []

    # Search for left and right parentheses
    lefts = [w for w in words if "(" in w[4]]
    rights = [w for w in words if ")" in w[4]]

    for l in lefts:
        lx0, ly0, lx1, ly1, _text, *_ = l

        for r in rights:
            rx0, ry0, rx1, ry1, _text, *_ = r

            # Same line / close vertical position
            if abs(ly0 - ry0) < 8 and rx0 > lx0:
                rect = fitz.Rect(lx0, ly0, rx1, ry1)
                results.append(rect)
                break

    return results


def fill_name_below_witness(page, new_name, font_path, font_size):
    rects = page.search_for("พยาน")

    if not rects:
        return 0

    count = 0

    for r in rects:
        # Create box below "พยาน"
        name_rect = fitz.Rect(
            r.x0 - 230,      # move left
            r.y1 + 22,       # move down
            r.x1 + 20,       # right edge
            r.y1 + 55        # box height
        )

        page.insert_textbox(
            name_rect,
            f"( {new_name} )",
            fontsize=font_size,
            fontname="customthai",
            fontfile=font_path,
            color=(0, 0, 0),
            align=1,
        )

        count += 1

    return count


def process_pdf(pdf_bytes, params, return_preview=False):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    page_index = params["page_num"] - 1
    if page_index < 0 or page_index >= len(doc):
        return None, None, 0

    page = doc[page_index]

    count = fill_name_below_witness(
    page=page,
    new_name=params["name"],
    font_path=params["font_path"],
    font_size=params["font_size"],
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
    page_title="PDF Blank Name Filler",
    page_icon="📝",
    layout="centered",
)

st.title("PDF Blank Name Filler")

st.sidebar.header("Settings")

page_num = st.sidebar.number_input(
    "Page number",
    min_value=1,
    value=PAGE_NUMBER_1BASED,
    step=1,
)

name_text = st.sidebar.text_input(
    "Name to fill inside parentheses",
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

font_size = st.sidebar.slider(
    "Font size",
    8,
    40,
    DEFAULT_FONT_SIZE,
)

show_preview = st.checkbox("Show preview for first file", value=True)

params = {
    "page_num": page_num,
    "name": name_text,
    "font_path": font_path,
    "font_size": font_size,
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
        st.success(f"Done. Filled {count} blank field(s).")

        if count == 0:
            st.warning("No blank parentheses were found on this page.")

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
                zipf.writestr(
                    f"updated_{file.name}",
                    out_buf.getvalue(),
                )

                st.write(f"{file.name}: filled {count} blank field(s)")

            else:
                st.error(f"Could not process {file.name}")

    zip_buf.seek(0)

    st.download_button(
        "⬇️ Download ALL as ZIP",
        data=zip_buf,
        file_name="updated_pdfs.zip",
        mime="application/zip",
    )
