"""
Document Upload Page
Upload and process PDF, DOCX, and Markdown files.
"""

import streamlit as st
import httpx
import time

# Page configuration
st.set_page_config(
    page_title="Upload Documents - AetherCanon Builder",
    page_icon="📤",
    layout="wide"
)

# API base URL (configured for Docker environment)
API_BASE_URL = "http://localhost:8000"

st.title("📤 Upload Documents")
st.markdown("Upload your worldbuilding documents for processing and analysis.")

# File uploader
st.markdown("### Upload a Document")
st.markdown("**Supported formats:** PDF, DOCX, Markdown (.md), Text (.txt)")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["pdf", "docx", "md", "txt", "markdown"],
    help="Upload a document to extract entities and build your knowledge base"
)

# Upload options
col1, col2 = st.columns(2)

with col1:
    custom_title = st.text_input(
        "Document Title (optional)",
        placeholder="Leave blank to use filename",
        help="Provide a custom title or leave blank to use the filename"
    )

with col2:
    extract_entities = st.checkbox(
        "Extract Entities",
        value=True,
        help="Use AI to extract characters, locations, events, etc."
    )

# Upload button
if uploaded_file is not None:
    if st.button("🚀 Process Document", type="primary"):
        with st.spinner("Processing document... This may take a minute."):
            try:
                # Prepare the file for upload
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

                # Prepare form data
                params = {
                    "extract_entities": extract_entities
                }

                if custom_title:
                    params["title"] = custom_title

                # Make API request
                start_time = time.time()

                with httpx.Client(timeout=300.0) as client:  # 5 minute timeout
                    response = client.post(
                        f"{API_BASE_URL}/api/documents/upload",
                        files=files,
                        params=params
                    )

                processing_time = time.time() - start_time

                if response.status_code == 200:
                    result = response.json()
                    document = result["document"]

                    # Success message
                    st.success(f"✅ Document processed successfully in {processing_time:.1f} seconds!")

                    # Display results
                    st.markdown("### Processing Results")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Chunks Created", result["chunks_created"])

                    with col2:
                        st.metric("Entities Extracted", result["entities_extracted"])

                    with col3:
                        st.metric("Processing Time", f"{result['processing_time_seconds']:.1f}s")

                    # Document details
                    with st.expander("📄 Document Details"):
                        st.json(document)

                    # Next steps
                    st.markdown("### Next Steps")
                    st.info(
                        "✅ Your document has been processed!\n\n"
                        "- **Review Queue**: Check the Review page to approve or reject extracted entities\n"
                        "- **Query**: Ask questions about your world in the Query page\n"
                        "- **View Documents**: See all uploaded documents below"
                    )

                else:
                    st.error(f"❌ Error: {response.status_code}")
                    st.code(response.text)

            except httpx.TimeoutException:
                st.error(
                    "⏱️ Request timed out. The document may be too large or the server is busy. "
                    "Try again or upload a smaller document."
                )
            except Exception as e:
                st.error(f"❌ Error uploading document: {str(e)}")

else:
    st.info("👆 Select a file to upload")

# Divider
st.markdown("---")

# List existing documents
st.markdown("### 📚 Your Documents")

try:
    with httpx.Client(timeout=10.0) as client:
        response = client.get(f"{API_BASE_URL}/api/documents/")

    if response.status_code == 200:
        data = response.json()
        documents = data.get("documents", [])
        total = data.get("total", 0)

        if total > 0:
            st.markdown(f"**Total documents:** {total}")

            for doc in documents:
                with st.expander(f"📄 {doc['title']} ({doc['file_type']})"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Status:** {doc['status']}")
                        st.write(f"**Uploaded:** {doc['upload_date'][:19]}")

                    with col2:
                        st.write(f"**Chunks:** {doc['chunk_count']}")
                        st.write(f"**Entities:** {doc['entity_count']}")

                    with col3:
                        st.write(f"**ID:** `{doc['id'][:8]}...`")

                    # Delete button
                    if st.button(f"🗑️ Delete", key=f"delete_{doc['id']}"):
                        with st.spinner("Deleting..."):
                            try:
                                del_response = client.delete(
                                    f"{API_BASE_URL}/api/documents/{doc['id']}"
                                )
                                if del_response.status_code == 200:
                                    st.success("Document deleted!")
                                    st.rerun()
                                else:
                                    st.error(f"Error deleting document: {del_response.text}")
                            except Exception as e:
                                st.error(f"Error: {e}")
        else:
            st.info("No documents uploaded yet. Upload your first document above!")

    else:
        st.warning(f"Could not fetch documents (Status: {response.status_code})")

except httpx.ConnectError:
    st.error(
        "❌ Cannot connect to backend API. "
        "Make sure the backend is running at http://localhost:8000"
    )
except Exception as e:
    st.error(f"Error fetching documents: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    "*Tip: For best results, upload documents with clear narrative structure. "
    "Entity extraction works best with fiction, worldbuilding guides, and game lore.*"
)
