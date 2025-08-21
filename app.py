import streamlit as st
import fitz  # PyMuPDF
from io import BytesIO

# --- Configuration: Define the text replacements ---
# This dictionary holds the text to find (key) and the text to replace it with (value).
REPLACEMENTS = {
    "นางธนาภรณ์ พลอยวิเศษ": "นายเจษฎากร สมิทธิอรรถกร",
    "People and Organizational Development Team": "Chief Executive Officer"
}

def replace_text_on_page4(uploaded_file):
    """
    Reads an uploaded PDF file, replaces text only on page 4, and returns the modified PDF as bytes.

    Args:
        uploaded_file: A Streamlit UploadedFile object.

    Returns:
        A BytesIO stream containing the modified PDF, or None if the PDF has fewer than 4 pages.
    """
    try:
        # Read the uploaded file's content into bytes
        file_bytes = uploaded_file.getvalue()
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

        # Check if the document has at least 4 pages
        if len(pdf_document) < 4:
            st.warning(f"'{uploaded_file.name}' has fewer than 4 pages and was skipped.")
            return None

        # --- Target ONLY page 4 (index 3) ---
        page = pdf_document[3]

        # Iterate through the replacement mapping
        for search_text, replace_text in REPLACEMENTS.items():
            text_instances = page.search_for(search_text)

            for inst in text_instances:
                # Add a redaction to cover the old text with a white box
                page.add_redact_annot(inst, fill=(1, 1, 1))

                # Insert the new text at the same position
                page.insert_text(inst.tl,  # .tl is the top-left corner of the instance
                                 replace_text,
                                 fontsize=11,
                                 fontname="helv")

        # Apply the redactions to finalize the changes
        page.apply_redactions()

        # Save the modified PDF to an in-memory stream (BytesIO)
        output_stream = BytesIO()
        pdf_document.save(output_stream, garbage=3, deflate=True)
        pdf_document.close()
        
        # Rewind the stream to the beginning so it can be read
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
            # Create columns for a cleaner layout of download buttons
            cols = st.columns(3)
            col_idx = 0
            
            for uploaded_file in uploaded_files:
                modified_pdf_stream = replace_text_on_page4(uploaded_file)
                
                if modified_pdf_stream:
                    # Create a new filename for the updated file
                    new_filename = f"{uploaded_file.name.replace('.pdf', '')}_UPDATED.pdf"
                    
                    # Display the download button in the next available column
                    with cols[col_idx % 3]:
                        st.download_button(
                            label=f"⬇️ Download {new_filename}",
                            data=modified_pdf_stream,
                            file_name=new_filename,
                            mime="application/pdf"
                        )
                        # Add some space for better alignment
                        st.write("") 
                    
                    col_idx += 1
        st.success("✅ Processing complete! Your updated files are ready for download above.")

    else:
        st.warning("⚠️ Please upload at least one PDF file to process.")
