import streamlit as st
import fitz  # PyMuPDF
from io import BytesIO
import os

# --- Configuration: Define the final text replacements ---
# Note: The parentheses are now included as requested.
REPLACEMENTS = {
    "นางธนาภรณ์ พลอยวิเศษ": "(นายเจษฎากร สมิทธิอรรถกร)",
    "People and Organizational Development Team": "Chief Executive Officer"
}

# --- Robust Font Path Logic ---
# This creates a reliable path to the font file, which must exist.
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()
FONT_PATH = os.path.join(SCRIPT_DIR, "fonts", "Sarabun-Regular.ttf")


def replace_text_on_page4(uploaded_file):
    """
    Reads an uploaded PDF, replaces text on page 4 using a dedicated Thai font file,
    and returns the modified PDF as bytes.
    """
    # First, check if the required font file actually exists.
    if not os.path.exists(FONT_PATH):
        st.error(f"CRITICAL ERROR: The font file is missing! Please ensure 'THSarabunNew-Regular.ttf' is inside a 'fonts' folder.")
        return None

    try:
        file_bytes = uploaded_file.getvalue()
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

        if len(pdf_document) < 4:
            st.warning(f"'{uploaded_file.name}' has fewer than 4 pages and was skipped.")
            return None

        page = pdf_document[3]

        # Register the custom Thai font for use in the document
        page.insert_font(fontfile=FONT_PATH, fontname="thai-sarabun")

        for search_text, replace_text in REPLACEMENTS.items():
            
            # Determine font and alignment for each replacement
            if "นางธนาภรณ์" in search_text:
                # Use the custom Thai font for the name
                font_name = "thai-sarabun"
                alignment = fitz.TEXT_ALIGN_CENTER
            else:
                # Use Times New Roman for the English title and center it as requested
                font_name = "TNR"
                alignment = fitz.TEXT_ALIGN_CENTER

            text_instances = page.search_for(search_text)
            for inst in text_instances:
                page.add_redact_annot(
                    inst,
                    text=replace_text,
                    fontname=font_name,
                    fontsize=11,
                    align=alignment,
                    fill=(1, 1, 1),
                    text_color=(0, 0, 0)
                )
        
        page.apply_redactions()

        output_stream = BytesIO()
        pdf_document.save(output_stream, garbage=3, deflate=True)
        pdf_document.close()
        
        output_stream.seek(0)
        return output_stream

    except Exception as e:
        st.error(f"An error occurred while processing '{uploaded_file.name}': {e}")
        return None


# --- Streamlit Application UI ---
st.set_page_config(layout="wide")
st.title("📄 Contract Signatory Updater")
st.write("This tool updates the signatory name and title on **Page 4** of your PDF contract files.")

# File Uploader
uploaded_files = st.file_uploader(
    "Drag and drop your contract PDF files here",
    type="pdf",
    accept_multiple_files=True
)

st.markdown("---")

# Process button
if st.button("✨ Process Files", type="primary"):
    if uploaded_files:
        with st.spinner("Processing... Please wait."):
            cols = st.columns(3)
            col_idx = 0
            
            for uploaded_file in uploaded_files:
                uploaded_file.seek(0)
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
        st.success("✅ Processing complete!")
    else:
        st.warning("⚠️ Please upload at least one PDF file to process.")
