"""
Semantic Query Page
Query the knowledge base using natural language questions.
"""

import streamlit as st
import httpx
import asyncio
from typing import List, Dict, Any
import os

# Page configuration
st.set_page_config(
    page_title="Query - AetherCanon Builder",
    page_icon="🔍",
    layout="wide"
)

# API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def format_citations_markdown(citations: List[Dict[str, Any]]) -> str:
    """
    Format citations as markdown list.

    Args:
        citations: List of citation dicts

    Returns:
        Formatted markdown string
    """
    if not citations:
        return ""

    lines = ["### Sources"]
    for citation in citations:
        number = citation.get("number", 0)
        title = citation.get("document_title", "Unknown")
        page = citation.get("page_number")

        citation_text = f"**[{number}]** {title}"
        if page:
            citation_text += f", Page {page}"

        lines.append(f"- {citation_text}")

    return "\n".join(lines)


async def execute_query(query: str, top_k: int = 5, search_type: str = "vector") -> Dict[str, Any]:
    """
    Execute semantic query via API.

    Args:
        query: Query text
        top_k: Number of chunks to retrieve
        search_type: "vector" or "hybrid"

    Returns:
        Query response dict
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/api/query/",
            json={
                "query": query,
                "top_k": top_k,
                "search_type": search_type
            }
        )
        response.raise_for_status()
        return response.json()


async def get_query_stats() -> Dict[str, Any]:
    """
    Get knowledge base statistics.

    Returns:
        Stats dict
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/query/stats")
        response.raise_for_status()
        result = response.json()
        return result.get("data", {})


# Title and description
st.title("🔍 Query Your World")
st.markdown("""
Ask questions about your worldbuilding documents and get answers with citations to source material.
""")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Query Settings")

    search_type = st.selectbox(
        "Search Type",
        options=["vector", "hybrid"],
        help="Vector: semantic similarity only. Hybrid: combines semantic + keyword matching"
    )

    top_k = st.slider(
        "Number of Sources",
        min_value=1,
        max_value=10,
        value=5,
        help="Number of document chunks to retrieve for context"
    )

    show_chunks = st.checkbox(
        "Show Retrieved Chunks",
        value=False,
        help="Display the actual text chunks used to generate the answer"
    )

    st.divider()

    # Knowledge base stats
    st.header("📊 Knowledge Base")
    try:
        stats = asyncio.run(get_query_stats())
        st.metric("Total Chunks", stats.get("total_chunks", 0))
        st.metric("Vectors", stats.get("chromadb_vectors", 0))
        st.caption(f"Model: {stats.get('embeddings_model', 'N/A')}")
    except Exception as e:
        st.warning(f"Could not load stats: {str(e)}")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "query_history" not in st.session_state:
    st.session_state.query_history = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Display citations if present
        if "citations" in message and message["citations"]:
            with st.expander("📚 View Sources", expanded=False):
                st.markdown(format_citations_markdown(message["citations"]))

        # Display retrieved chunks if requested
        if show_chunks and "chunks" in message and message["chunks"]:
            with st.expander("📄 Retrieved Chunks", expanded=False):
                for idx, chunk in enumerate(message["chunks"], start=1):
                    st.markdown(f"**Chunk {idx}** (Score: {chunk['score']:.3f})")
                    st.text_area(
                        f"chunk_{idx}",
                        value=chunk["text"],
                        height=100,
                        disabled=True,
                        label_visibility="collapsed"
                    )
                    if chunk.get("document_id"):
                        st.caption(f"Document ID: {chunk['document_id']}")
                    st.divider()

# Chat input
if prompt := st.chat_input("Ask a question about your world..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Execute query
    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            try:
                # Execute query
                result = asyncio.run(execute_query(prompt, top_k, search_type))

                # Extract response components
                answer = result.get("answer", "No answer generated")
                citations = result.get("citations", [])
                chunks = result.get("retrieved_chunks", [])
                metadata = result.get("metadata", {})

                # Display answer
                st.markdown(answer)

                # Display citations
                if citations:
                    with st.expander("📚 View Sources", expanded=False):
                        st.markdown(format_citations_markdown(citations))

                # Display chunks if enabled
                if show_chunks and chunks:
                    with st.expander("📄 Retrieved Chunks", expanded=False):
                        for idx, chunk in enumerate(chunks, start=1):
                            st.markdown(f"**Chunk {idx}** (Score: {chunk['score']:.3f})")
                            st.text_area(
                                f"chunk_{idx}",
                                value=chunk["text"],
                                height=100,
                                disabled=True,
                                label_visibility="collapsed"
                            )
                            if chunk.get("document_id"):
                                st.caption(f"Document ID: {chunk['document_id']}")
                            st.divider()

                # Add assistant message to chat
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "citations": citations,
                    "chunks": chunks,
                    "metadata": metadata
                })

                # Add to query history
                st.session_state.query_history.append({
                    "query": prompt,
                    "answer": answer,
                    "chunks_retrieved": metadata.get("chunks_retrieved", 0),
                    "search_type": search_type
                })

            except httpx.HTTPError as e:
                error_msg = f"Query failed: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Action buttons in sidebar
with st.sidebar:
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.query_history = []
            st.rerun()

    with col2:
        if st.button("💾 Export Chat", use_container_width=True):
            # Format chat as markdown
            chat_export = "# AetherCanon Builder - Chat Export\n\n"
            for msg in st.session_state.messages:
                role = msg["role"].title()
                chat_export += f"## {role}\n\n{msg['content']}\n\n"
                if "citations" in msg and msg["citations"]:
                    chat_export += format_citations_markdown(msg["citations"])
                    chat_export += "\n\n"
                chat_export += "---\n\n"

            st.download_button(
                label="Download Markdown",
                data=chat_export,
                file_name="chat_export.md",
                mime="text/markdown"
            )

# Example queries
st.divider()
st.subheader("💡 Example Queries")

example_queries = [
    "Who is [character name]?",
    "What happened at [location]?",
    "Describe the relationship between [entity A] and [entity B]",
    "What are the key events in [time period/arc]?",
    "Tell me about [concept/item]"
]

cols = st.columns(len(example_queries))
for idx, (col, example) in enumerate(zip(cols, example_queries)):
    with col:
        if st.button(example, key=f"example_{idx}", use_container_width=True):
            # This would trigger a new query
            # For now, just show the example
            st.info(f"Try asking: {example}")

# Query history section
if st.session_state.query_history:
    st.divider()
    st.subheader("📜 Query History")

    with st.expander("View Recent Queries", expanded=False):
        for idx, query_item in enumerate(reversed(st.session_state.query_history), start=1):
            st.markdown(f"**Query {idx}:** {query_item['query']}")
            st.caption(
                f"Chunks: {query_item['chunks_retrieved']} | "
                f"Search: {query_item['search_type']}"
            )
            st.divider()

# Tips section
with st.expander("💡 Tips for Better Queries"):
    st.markdown("""
    - **Be specific**: Ask about particular characters, locations, or events
    - **Use full names**: If entities have multiple names, use their full canonical name
    - **Ask follow-ups**: Build on previous questions to dive deeper
    - **Check sources**: Always verify citations to ensure accuracy
    - **Adjust top_k**: Increase if answers seem incomplete, decrease for faster responses
    - **Try hybrid search**: Use hybrid mode for better keyword matching on specific terms
    """)
