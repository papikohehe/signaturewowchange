import streamlit as st
import fitz  # PyMuPDF
from io import BytesIO
import os

# --- Configuration: Define the text replacements ---
REPLACEMENTS = {
    "นางธนาภรณ์ พลอยวิเศษ": "นายเจษฎากร สมิทธิอรรถกร",
    "People and Organizational Development Team": "Chief Executive Officer"
}

# --- Load Custom Font ---
FONT_PATH = os.path.join("fonts", "angsa.ttf")
try:
    CUSTOM_FONT = fitz.Font(file=FONT_PATH)
except Exception as e:
    CUSTOM_FONT = None
    st.warning(f"⚠️ Could not load custom font at {FONT_PATH}: {e}. Falling back to built-in Helvetica.")


def replace_text_on_page4(uploaded_file):
    """
    Reads an uploaded PDF file, replaces text only on page 4, and returns the modified PDF as bytes.
    """
    try:
        file_bytes = uploaded_file.getvalue()
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

        if len(pdf_document) < 4:
            st.warning(f"'{uploaded_file.name}' has fewer than 4 pages and was skipped.")
            return None

        page = pdf_document[3]  # Page index 3 = page 4

        # Try PyMuPDF's modern replace_text if available
        if hasattr(page, "replace_text"):
            for search_text, replace_text in REPLACEMENTS.items():
                page.replace_text(search_text, replace_text)

        else:
            # Manual fallback: search + redact + insert
            for search_text, replace_text in REPLACEMENTS.items():
                text_instances = page.search_for(search_text)

                for inst in text_instances:
                    # White-out old text
                    page.add_redact_annot(inst, fill=(1, 1, 1))
                    page.apply_redactions()

                    # Insert replacement text
                    page.insert_textbox(
                        inst,
                        replace_text,
                        fontsize=12,
                        font=CUSTOM_FONT if CUSTOM_FONT else "helv",
                        align=fitz.TEXT_ALIGN_LEFT
                    )

        # Save to BytesIO
        output_stream = BytesIO()
        pdf_document.save(output_stream, garbage=3, deflate=True)
        pdf_document.close()
        output_stream.seek(0)
        return output_stream

    except Exception as e:
        st.error(f"An error occurred while processing '{uploaded_file.name}': {e}")
        return None


# --- Streamlit App UI ---
st.set_page_config(layout="wide")

st.title("📄 Contract Signatory Updater")
st.write("This tool updates the signatory name and title on **Page 4** of your PDF contract files.")
st.info(f"""
The following changes will be applied:
- **Replaces:** `นางธนาภรณ์ พลอยวิเศษ` → `นายเจษฎากร สมิทธิอรรถกร`
- **Replaces:** `People and Organizational Development Team` → `Chief Executive Officer`
""")

# File Uploader
uploaded_files = st.file_uploader(
    "Drag and drop your contract PDF files here",
    type="pdf",
    accept_multiple_files=True
)

st.markdown("---")

if st.button("✨ Process Files", type="primary"):
    if uploaded_files:
        with st.spinner("Processing... Please wait."):
            cols = st.columns(3)
            col_idx = 0

            for uploaded_file in uploaded_files:
                modified_pdf_stream = replace_text_on_page4(uploaded_file)

                if modified_pdf_stream:
                    new_filename = f"{uploaded_file.name.replace('.pdf', '')}_UPDATED.pdf"

                    with cols[col_idx % 3]:
                        st.download_button(
                            label=f"⬇️ Download {new_filename}",
                            data=modified_pdf_stream,
                            file_name=new_filename,
                            mime="application/pdf"
                        )
                        st.write("")

                    col_idx += 1
        st.success("✅ Processing complete! Your updated files are ready for download above.")
    else:
        st.warning("⚠️ Please upload at least one PDF file to process.")
