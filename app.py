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
# Looks for angsa.ttf inside a 'fonts' sub-folder
FONT_PATH = os.path.join("fonts", "angsa.ttf")


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

        page = pdf_document[3]  # Target ONLY page 4

        # --- Register the custom Thai font if it exists ---
        font_is_registered = False
        if os.path.exists(FONT_PATH):
            page.insert_font(fontfile=FONT_PATH, fontname="custom-thai")
            font_is_registered = True
        else:
            # Set a flag to show a persistent warning in the UI
            st.session_state.font_warning = True

        # --- Use the reliable single-step replacement method ---
        for search_text, replace_text in REPLACEMENTS.items():
            
            # Customize font and alignment for each replacement
            if "นางธนาภรณ์" in search_text:  # This is the Thai name
                font_name = "custom-thai" if font_is_registered else "helv"
                alignment = fitz.TEXT_ALIGN_CENTER
            else:  # This is the English title
                font_name = "TNR"  # Times New Roman
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
        
        # Apply all scheduled replacements at once
        page.apply_redactions()

        # Save the modified PDF to an in-memory stream
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

# Check for the font file and display a persistent warning if it's missing
if "font_warning" in st.session_state and st.session_state.font_warning:
    st.error(f"**Font Not Found:** Please make sure the font file exists at `{FONT_PATH}`. Thai text may not render correctly.")
    st.session_state.font_warning = False # Reset warning


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
                uploaded_file.seek(0) # Rewind file buffer before processing
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
