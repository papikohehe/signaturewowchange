import streamlit as st
import fitz  # PyMuPDF
from io import BytesIO

# --- Configuration: Define the text to be replaced ---
REPLACEMENTS = {
    "นางธนาภรณ์ พลอยวิเศษ": "นายเจษฎากร สมิทธิอรรถกร",
    "People and Organizational Development Team": "Chief Executive Officer"
}

def replace_text_on_page4(uploaded_file):
    """
    Reads an uploaded PDF, replaces text on page 4, and returns the modified PDF as bytes.
    This version uses a built-in CJK (Chinese, Japanese, Korean) font which has
    broad Unicode support and can often render Thai characters without needing a separate font file.
    """
    try:
        # Read the file from the upload
        file_bytes = uploaded_file.getvalue()
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

        # Ensure the PDF has enough pages
        if len(pdf_document) < 4:
            st.warning(f"'{uploaded_file.name}' has fewer than 4 pages and was skipped.")
            return None

        # Target ONLY page 4 (which is at index 3)
        page = pdf_document[3]

        # Loop through the items we need to replace
        for search_text, replace_text in REPLACEMENTS.items():
            
            # Set font and alignment for each specific piece of text
            if "นางธนาภรณ์" in search_text:
                # For the Thai text, use the built-in CJK font and center it
                font_name = "cjk" 
                alignment = fitz.TEXT_ALIGN_CENTER
            else:
                # For the English text, use a standard font and left-align it
                font_name = "helv"  # Helvetica
                alignment = fitz.TEXT_ALIGN_LEFT

            # Find all occurrences of the text on the page
            text_instances = page.search_for(search_text)

            # For each occurrence, schedule a replacement
            for inst in text_instances:
                page.add_redact_annot(
                    inst,                           # The area of the old text
                    text=replace_text,              # The new text to write
                    fontname=font_name,             # The selected font
                    fontsize=11,
                    align=alignment,
                    fill=(1, 1, 1),                 # Make the background white
                    text_color=(0, 0, 0)            # Make the text black
                )
        
        # Apply all the scheduled replacements at once
        page.apply_redactions()

        # Save the modified PDF to a memory buffer
        output_stream = BytesIO()
        pdf_document.save(output_stream, garbage=3, deflate=True)
        pdf_document.close()
        
        # Go back to the beginning of the buffer to be ready for download
        output_stream.seek(0)
        return output_stream

    except Exception as e:
        st.error(f"An error occurred while processing '{uploaded_file.name}': {e}")
        return None


# --- Streamlit Application UI ---
st.set_page_config(layout="wide")

st.title("📄 Contract Signatory Updater")
st.write("This tool updates the signatory name and title on **Page 4** of your PDF contract files.")
st.info(f"""
The following changes will be applied:
- **Replaces:** `นางธนาภรณ์ พลอยวิเศษ` → `นายเจษฎากร สมิทธิอรรถกร`
- **Replaces:** `People and Organizational Development Team` → `Chief Executive Officer`
""")

# File Uploader for multiple PDFs
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
            # Create columns for a tidy layout of download buttons
            cols = st.columns(3)
            col_idx = 0
            
            for uploaded_file in uploaded_files:
                # Rewind file buffer before processing each file
                uploaded_file.seek(0)
                modified_pdf_stream = replace_text_on_page4(uploaded_file)
                
                if modified_pdf_stream:
                    new_filename = f"{uploaded_file.name.replace('.pdf', '')}_UPDATED.pdf"
                    
                    # Display the download button in the next available column
                    with cols[col_idx % 3]:
                        st.download_button(
                            label=f"⬇️ Download {new_filename}",
                            data=modified_pdf_stream,
                            file_name=new_filename,
                            mime="application/pdf"
                        )
                        st.write("") # Add some space for aesthetics
                    
                    col_idx += 1
        st.success("✅ Processing complete! Your updated files are ready for download above.")
    else:
        st.warning("⚠️ Please upload at least one PDF file to process.")
