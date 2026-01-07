"""
AetherCanon Builder - Streamlit Frontend
Main application entry point.
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="AetherCanon Builder",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main page
st.title("📚 AetherCanon Builder")
st.markdown("### Knowledge Coherence System for Worldbuilders")

st.markdown("""
Welcome to AetherCanon Builder, an open-source tool for maintaining logical consistency
in your fictional universes.

**Features:**
- 📄 **Document Ingestion** - Upload PDFs, DOCX, and Markdown files
- 🔍 **Semantic Query** - Ask questions about your world with AI-powered answers
- ⚠️ **Inconsistency Detection** - Automatically detect contradictions in your lore
- ✅ **Review Queue** - Review and approve AI-generated content
- 📤 **Obsidian Export** - Export your knowledge graph to Obsidian

**Getting Started:**
Use the sidebar to navigate to different features. Start by uploading documents in the Upload page.

**Current Status:**
- Backend API: Running on port 8000
- Frontend UI: Running on port 8501
- LLM Provider: Check your configuration

---

**Note:** This is the MVP version. Features are being actively developed.
""")

# Sidebar
with st.sidebar:
    st.markdown("## Navigation")
    st.markdown("Use the pages above to access features:")
    st.markdown("- 📤 Upload Documents")
    st.markdown("- 🔍 Query Knowledge")
    st.markdown("- ✅ Review Queue")
    st.markdown("- 📤 Export to Obsidian")

    st.markdown("---")
    st.markdown("### System Info")

    # TODO: Add API health check here
    st.info("API Status: Initializing...")

    st.markdown("---")
    st.markdown("**Version:** 0.1.0 MVP")
    st.markdown("[Documentation](https://github.com/yourusername/worldforge)")
