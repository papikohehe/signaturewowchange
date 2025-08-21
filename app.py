import streamlit as st
import fitz  # PyMuPDF
from io import BytesIO
import os

# --- Configuration: Define the text replacements ---
REPLACEMENTS = {
    "นางธนาภรณ์ พลอยวิเศษ": "นายเจษฎากร สมิทธิอรรถกร",
    "People and Organizational Development Team": "Chief Executive Officer"
}

# --- Font setup ---
# The script will look for this font file in the same directory.
THAI_FONT_PATH = "THSarabunNew.ttf"


def replace_text_on_page4(uploaded_file):
    """
    Reads an uploaded PDF file, replaces text only on page 4 with specific fonts
    and alignments, and returns the modified PDF as bytes.
    """
    try:
        file_bytes = uploaded_file.getvalue()
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

        if len(pdf_document) < 4:
            st.warning(f"'{uploaded_file.name}' has fewer than 4 pages and was skipped.")
            return None

        page = pdf_document[3]

        # --- Register the Thai font if it exists ---
        font_is_registered = False
        if os.path.exists(THAI_FONT_PATH):
            # Register the font with a custom name for use in the document.
            page.insert_font(fontfile=THAI_FONT_PATH, fontname="thai-sarabun")
            font_is_registered = True
        else:
            # Set a flag to show a persistent warning in the UI
            st.session_state.font_warning = True

        # Iterate through the replacement mapping
        for search_text, replace_text in REPLACEMENTS.items():
            
            # --- CUSTOMIZE FONT AND ALIGNMENT FOR EACH REPLACEMENT ---
            if "นางธนาภรณ์" in search_text:  # This is the Thai name
                font_name = "thai-sarabun" if font_is_registered else "helv"
                alignment = fitz.TEXT_ALIGN_CENTER
            else:  # This is the English title
                font_name = "TNR"  # "TNR" is the alias for Times New Roman
                alignment = fitz.TEXT_ALIGN_LEFT

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


# --- Streamlit App UI ---
st.set_page_config(layout="wide")

st.title("📄 Contract Signatory Updater")
st.write("This tool updates the signatory name and title on **Page 4** of your PDF contract files.")
st.info(f"""
The following changes will be applied:
- **Replaces:** `นางธนาภรณ์ พลอยวิเศษ` → `นายเจษฎากร สมิทธิอรรถกร` (Centered, Thai Sarabun font)
- **Replaces:** `People and Organizational Development Team` → `Chief Executive Officer` (Left-aligned, Times New Roman font)
""")

# Check for the font file and display a persistent warning if it's missing
if "font_warning" in st.session_state and st.session_state.font_warning:
    st.error(f"**Font Not Found:** Please add the `{THAI_FONT_PATH}` file to the app's directory. Thai text may not render correctly.")
    # Reset warning after showing it
    st.session_state.font_warning = False


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
                # We need to reset the file read position before processing
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
