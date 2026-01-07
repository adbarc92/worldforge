"""
Review Queue Page
Review and approve AI-proposed entities and relationships.
"""

import streamlit as st
import httpx
import asyncio
from typing import List, Dict, Any
import os
import json

# Page configuration
st.set_page_config(
    page_title="Review Queue - AetherCanon Builder",
    page_icon="✅",
    layout="wide"
)

# API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


async def get_queue_stats() -> Dict[str, Any]:
    """Get review queue statistics."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/review/queue/stats")
        response.raise_for_status()
        return response.json()


async def get_review_queue(
    status: str = "pending",
    content_type: str = None,
    sort_by: str = "priority",
    skip: int = 0,
    limit: int = 50
) -> Dict[str, Any]:
    """Get review queue items."""
    params = {
        "status": status,
        "sort_by": sort_by,
        "skip": skip,
        "limit": limit
    }
    if content_type:
        params["content_type"] = content_type

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/review/queue",
            params=params
        )
        response.raise_for_status()
        return response.json()


async def approve_item(item_id: str) -> Dict[str, Any]:
    """Approve a proposed item."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/review/{item_id}/approve",
            json={"reviewed_by": "user"}
        )
        response.raise_for_status()
        return response.json()


async def reject_item(item_id: str, reason: str = None) -> Dict[str, Any]:
    """Reject a proposed item."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/review/{item_id}/reject",
            json={"reason": reason, "reviewed_by": "user"}
        )
        response.raise_for_status()
        return response.json()


async def bulk_approve(item_ids: List[str]) -> Dict[str, Any]:
    """Bulk approve multiple items."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/review/bulk-approve",
            json={"item_ids": item_ids, "reviewed_by": "user"}
        )
        response.raise_for_status()
        return response.json()


# Title and description
st.title("✅ Review Queue")
st.markdown("""
Review and approve AI-proposed entities and relationships before they become part of your canon.
""")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Filters")

    status_filter = st.selectbox(
        "Status",
        options=["pending", "approved", "rejected"],
        index=0
    )

    content_type_filter = st.selectbox(
        "Content Type",
        options=["All", "entity", "relationship"],
        index=0
    )

    sort_by = st.selectbox(
        "Sort By",
        options=["priority", "date", "confidence"],
        index=0
    )

    st.divider()

    # Queue statistics
    st.header("📊 Queue Stats")
    try:
        stats = asyncio.run(get_queue_stats())

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Pending", stats.get("total_pending", 0))
        with col2:
            st.metric("With Conflicts", stats.get("items_with_conflicts", 0))

        st.caption(f"Avg Confidence: {stats.get('average_confidence', 0):.2f}")

        # By status
        with st.expander("By Status"):
            by_status = stats.get("by_status", {})
            for status, count in by_status.items():
                st.text(f"{status.capitalize()}: {count}")

        # By type
        with st.expander("By Type"):
            by_type = stats.get("by_type", {})
            for content_type, count in by_type.items():
                st.text(f"{content_type.capitalize()}: {count}")

    except Exception as e:
        st.warning(f"Could not load stats: {str(e)}")

# Initialize session state
if "selected_items" not in st.session_state:
    st.session_state.selected_items = []

if "refresh_trigger" not in st.session_state:
    st.session_state.refresh_trigger = 0

# Bulk actions
if st.session_state.selected_items:
    st.info(f"{len(st.session_state.selected_items)} items selected")

    col1, col2, col3 = st.columns([2, 2, 6])

    with col1:
        if st.button("✅ Bulk Approve", use_container_width=True):
            try:
                result = asyncio.run(bulk_approve(st.session_state.selected_items))
                st.success(f"Approved {result.get('approved_entities', 0)} entities and {result.get('approved_relationships', 0)} relationships")
                st.session_state.selected_items = []
                st.session_state.refresh_trigger += 1
                st.rerun()
            except Exception as e:
                st.error(f"Bulk approval failed: {str(e)}")

    with col2:
        if st.button("Clear Selection", use_container_width=True):
            st.session_state.selected_items = []
            st.rerun()

st.divider()

# Fetch queue
try:
    content_type_param = None if content_type_filter == "All" else content_type_filter
    queue_data = asyncio.run(get_review_queue(
        status=status_filter,
        content_type=content_type_param,
        sort_by=sort_by,
        skip=0,
        limit=50
    ))

    items = queue_data.get("items", [])
    total = queue_data.get("total", 0)

    st.subheader(f"Review Items ({total} total)")

    if not items:
        st.info("No items to review")
    else:
        # Display items
        for idx, item_data in enumerate(items):
            item = item_data["item"]["item"]
            conflicts = item_data["item"]["conflicts"]
            has_conflicts = item_data["item"]["has_conflicts"]
            priority_score = item_data["item"]["priority_score"]

            item_id = item["id"]
            content = item["content"]

            # Get entity details
            entity_name = content.get("name", "Unnamed")
            entity_type = content.get("type", "unknown")
            entity_description = content.get("description", "No description")
            confidence = content.get("confidence", 0.0)

            # Card for each item
            with st.container():
                # Header with checkbox
                col1, col2, col3, col4 = st.columns([0.5, 3, 2, 2])

                with col1:
                    if status_filter == "pending":
                        is_selected = st.checkbox(
                            "Select",
                            key=f"select_{item_id}",
                            value=item_id in st.session_state.selected_items,
                            label_visibility="collapsed"
                        )

                        if is_selected and item_id not in st.session_state.selected_items:
                            st.session_state.selected_items.append(item_id)
                        elif not is_selected and item_id in st.session_state.selected_items:
                            st.session_state.selected_items.remove(item_id)

                with col2:
                    st.markdown(f"### {entity_name}")
                    st.caption(f"Type: {entity_type}")

                with col3:
                    st.metric("Confidence", f"{confidence:.2f}")
                    if has_conflicts:
                        st.error(f"⚠️ {len(conflicts)} conflict(s)")

                with col4:
                    st.metric("Priority", f"{priority_score:.2f}")

                # Description
                st.markdown(f"**Description:**\n\n{entity_description}")

                # Show conflicts if any
                if has_conflicts and conflicts:
                    with st.expander(f"⚠️ View {len(conflicts)} Conflict(s)", expanded=False):
                        for conflict in conflicts:
                            st.warning(f"**{conflict['severity'].upper()}:** {conflict['description']}")
                            st.caption(f"Conflict ID: {conflict['id']}")

                # Metadata
                with st.expander("📋 View Metadata", expanded=False):
                    st.json(item)

                # Actions
                if status_filter == "pending":
                    col1, col2, col3 = st.columns([2, 2, 6])

                    with col1:
                        if st.button("✅ Approve", key=f"approve_{item_id}", use_container_width=True):
                            try:
                                result = asyncio.run(approve_item(item_id))
                                st.success(f"Approved: {entity_name}")
                                st.session_state.refresh_trigger += 1
                                st.rerun()
                            except Exception as e:
                                st.error(f"Approval failed: {str(e)}")

                    with col2:
                        if st.button("❌ Reject", key=f"reject_{item_id}", use_container_width=True):
                            try:
                                result = asyncio.run(reject_item(item_id, reason="Manual rejection"))
                                st.warning(f"Rejected: {entity_name}")
                                st.session_state.refresh_trigger += 1
                                st.rerun()
                            except Exception as e:
                                st.error(f"Rejection failed: {str(e)}")

                st.divider()

        # Pagination info
        if total > len(items):
            st.info(f"Showing {len(items)} of {total} items")

except httpx.HTTPError as e:
    st.error(f"Failed to fetch review queue: {str(e)}")
except Exception as e:
    st.error(f"Unexpected error: {str(e)}")

# Tips section
with st.expander("💡 Review Tips"):
    st.markdown("""
    ### How to Review Effectively

    - **Check Conflicts**: Items with conflicts need careful review
    - **Verify Accuracy**: Ensure descriptions match your world's canon
    - **Use Confidence Scores**: Low confidence items may need editing
    - **Bulk Approve**: Select multiple high-confidence items for faster review
    - **Priority First**: High-priority items have conflicts or low confidence

    ### Actions Available

    - **Approve**: Move to canonical entity table
    - **Reject**: Dismiss incorrect or duplicate entities
    - **Bulk Approve**: Approve multiple items at once (high-confidence only)

    ### Priority Scoring

    Higher priority score means the item needs more careful review:
    - **High conflicts** boost priority
    - **Low confidence** increases priority
    - **Recent items** are prioritized
    """)
