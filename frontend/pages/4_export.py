"""
Export Page
Export canonical content to various formats.
"""

import streamlit as st
import httpx
import asyncio
import os

# Page configuration
st.set_page_config(
    page_title="Export - AetherCanon Builder",
    page_icon="📦",
    layout="wide"
)

# API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


async def export_to_obsidian(export_name=None, include_graph=True, graph_format="d3"):
    """Export to Obsidian format."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/api/export/obsidian",
            json={
                "export_name": export_name,
                "include_graph": include_graph,
                "graph_format": graph_format
            }
        )
        response.raise_for_status()
        return response.json()


async def get_graph_metrics():
    """Get graph metrics."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/export/graph/metrics")
        response.raise_for_status()
        result = response.json()
        return result.get("data", {})


# Title and description
st.title("📦 Export Your Canon")
st.markdown("""
Export your worldbuilding canon to various formats for use in other tools.
""")

# Sidebar
with st.sidebar:
    st.header("📊 Canon Overview")

    try:
        metrics = asyncio.run(get_graph_metrics())

        st.metric("Total Entities", metrics.get("total_nodes", 0))
        st.metric("Total Relationships", metrics.get("total_edges", 0))
        st.metric("Graph Density", f"{metrics.get('density', 0):.3f}")

        if metrics.get("most_connected"):
            with st.expander("Most Connected Entities"):
                for entity in metrics["most_connected"][:5]:
                    st.text(f"{entity['name']}: {entity['centrality']:.3f}")

    except Exception as e:
        st.warning(f"Could not load metrics: {str(e)}")

# Main content
tab1, tab2 = st.tabs(["📝 Obsidian Export", "📊 Graph Visualization"])

with tab1:
    st.header("Export to Obsidian")

    st.markdown("""
    Export your canon as an Obsidian vault with:
    - One Markdown file per entity
    - YAML frontmatter with metadata
    - Wikilinks `[[Entity Name]]` for relationships
    - Index file with all entities
    - Graph JSON for visualization
    """)

    # Export configuration
    col1, col2 = st.columns(2)

    with col1:
        export_name = st.text_input(
            "Export Name (optional)",
            placeholder="my_world_export",
            help="Leave blank for auto-generated timestamp"
        )

    with col2:
        graph_format = st.selectbox(
            "Graph Format",
            options=["d3", "cytoscape", "simple"],
            help="Format for graph.json file"
        )

    include_graph = st.checkbox("Include Graph JSON", value=True)

    st.divider()

    # Export button
    if st.button("🚀 Export to Obsidian", type="primary", use_container_width=True):
        with st.spinner("Exporting canon..."):
            try:
                result = asyncio.run(export_to_obsidian(
                    export_name=export_name if export_name else None,
                    include_graph=include_graph,
                    graph_format=graph_format
                ))

                st.success("✅ Export completed!")

                # Show results
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Entities Exported", result.get("entities_exported", 0))

                with col2:
                    st.metric("Relationships Exported", result.get("relationships_exported", 0))

                with col3:
                    st.metric("Files Created", result.get("files_created", 0))

                st.info(f"📁 Export location: `{result.get('export_path')}`")

                # Download button
                export_name_for_download = result.get("export_name")
                if export_name_for_download:
                    download_url = f"{API_BASE_URL}/api/export/obsidian/{export_name_for_download}/download"

                    st.markdown(f"""
                    ### Download Your Export

                    [⬇️ Download ZIP]({download_url})

                    Or copy the export directory from the server.
                    """)

            except Exception as e:
                st.error(f"❌ Export failed: {str(e)}")

    # Instructions
    with st.expander("📖 How to Use in Obsidian"):
        st.markdown("""
        ### Opening the Export in Obsidian

        1. **Download** the ZIP file or copy the export folder
        2. **Extract** the ZIP to your desired location
        3. **Open Obsidian** and click "Open folder as vault"
        4. **Select** the extracted export folder
        5. **Browse** using `index.md` or the file explorer

        ### Features

        - **Wikilinks**: Click `[[Entity Name]]` to navigate between entities
        - **Graph View**: Use Obsidian's graph view (Ctrl/Cmd + G) to visualize relationships
        - **Search**: Use Obsidian's powerful search (Ctrl/Cmd + Shift + F)
        - **Tags**: Entities are tagged by type (#character, #location, etc.)

        ### Customization

        - Edit entity descriptions directly in Obsidian
        - Add your own notes and links
        - Customize with Obsidian plugins
        - Create new entities manually with the same format
        """)

with tab2:
    st.header("Graph Visualization")

    st.markdown("""
    Visualize the relationships between entities in your canon.
    """)

    # Graph format selector
    viz_format = st.radio(
        "Visualization Type",
        options=["Interactive D3", "Metrics Only"],
        horizontal=True
    )

    if viz_format == "Interactive D3":
        st.info("📊 Interactive D3 visualization will be available after exporting to Obsidian. Open `graph_visualization.html` from the export folder.")

        st.markdown("""
        ### Graph Visualization Features

        - **Force-directed layout**: Nodes repel each other for clarity
        - **Color-coded by type**: Different colors for characters, locations, etc.
        - **Interactive**: Drag nodes to explore relationships
        - **Tooltips**: Hover for entity details
        - **Zoom and pan**: Navigate large graphs easily
        """)

    else:
        # Show metrics
        st.subheader("Graph Metrics")

        try:
            metrics = asyncio.run(get_graph_metrics())

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Nodes", metrics.get("total_nodes", 0))
                st.metric("Edges", metrics.get("total_edges", 0))

            with col2:
                st.metric("Density", f"{metrics.get('density', 0):.3f}")
                st.metric("Connected", "Yes" if metrics.get("is_connected") else "No")

            with col3:
                st.metric("Components", metrics.get("connected_components", 0))
                st.metric("Largest Component", metrics.get("largest_component_size", 0))

            # Most connected entities
            if metrics.get("most_connected"):
                st.subheader("Most Connected Entities")

                st.markdown("These entities have the most relationships:")

                for idx, entity in enumerate(metrics["most_connected"][:10], start=1):
                    st.text(f"{idx}. {entity['name']} - Centrality: {entity['centrality']:.3f}")

        except Exception as e:
            st.error(f"Failed to load metrics: {str(e)}")

# Tips section
with st.expander("💡 Export Tips"):
    st.markdown("""
    ### Best Practices

    - **Review first**: Approve all proposed entities before exporting
    - **Resolve conflicts**: Fix contradictions for a consistent canon
    - **Name your export**: Use descriptive names for multiple versions
    - **Regular exports**: Create snapshots as your world evolves

    ### What Gets Exported

    - ✅ All approved entities from the canonical Entity table
    - ✅ All approved relationships
    - ✅ Entity metadata and confidence scores
    - ❌ Proposed content (not yet approved)
    - ❌ Rejected items
    - ❌ Source documents

    ### Graph Formats

    - **D3**: Best for interactive web visualizations
    - **Cytoscape**: For use with Cytoscape.js or Cytoscape Desktop
    - **Simple**: Basic nodes/edges JSON for custom tools
    """)
