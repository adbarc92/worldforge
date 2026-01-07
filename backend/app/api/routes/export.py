"""
API routes for exporting content to various formats.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from backend.app.database.connection import get_db
from backend.app.api.schemas import ExportRequest, ExportResponse, APIResponse
from backend.app.export.obsidian import ObsidianExporter
from backend.app.export.graph_builder import GraphBuilder


router = APIRouter()


@router.post("/obsidian", response_model=ExportResponse)
async def export_to_obsidian(
    request: ExportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Export all canonical content to Obsidian vault format.

    Creates a directory with:
    - One .md file per entity with YAML frontmatter
    - Wikilinks [[Entity Name]] for relationships
    - index.md with entity listing
    - README.md with instructions
    - graph.json (if requested)

    Args:
        request: Export configuration
        db: Database session

    Returns:
        Export summary with file paths
    """
    try:
        exporter = ObsidianExporter()

        # Export canon
        result = await exporter.export_full_canon(
            db=db,
            export_name=request.export_name
        )

        # Add graph if requested
        if request.include_graph:
            export_dir = Path(result["export_path"])
            graph_builder = GraphBuilder()

            await graph_builder.export_graph_json(
                db=db,
                export_path=export_dir,
                format_type=request.graph_format
            )

        return ExportResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/obsidian/{export_name}/download")
async def download_export(export_name: str):
    """
    Download exported vault as ZIP file.

    Args:
        export_name: Name of the export

    Returns:
        ZIP file download
    """
    try:
        exporter = ObsidianExporter()
        export_dir = exporter.export_path / export_name

        if not export_dir.exists():
            raise HTTPException(status_code=404, detail="Export not found")

        # Create ZIP
        zip_path = await exporter.create_zip(export_dir)

        return FileResponse(
            path=zip_path,
            filename=f"{export_name}.zip",
            media_type="application/zip"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Download failed: {str(e)}"
        )


@router.get("/graph", response_model=APIResponse)
async def get_graph_data(
    format_type: str = "d3",
    db: AsyncSession = Depends(get_db)
):
    """
    Get graph visualization data.

    Args:
        format_type: Graph format (d3, cytoscape, simple)
        db: Database session

    Returns:
        Graph data in requested format
    """
    try:
        builder = GraphBuilder()
        graph_data = await builder.build_graph_json(db, format_type)

        return APIResponse(
            success=True,
            data=graph_data
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build graph: {str(e)}"
        )


@router.get("/graph/metrics", response_model=APIResponse)
async def get_graph_metrics(db: AsyncSession = Depends(get_db)):
    """
    Get graph analysis metrics.

    Args:
        db: Database session

    Returns:
        Graph metrics (connectivity, centrality, etc.)
    """
    try:
        builder = GraphBuilder()
        metrics = await builder.compute_graph_metrics(db)

        return APIResponse(
            success=True,
            data=metrics
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute metrics: {str(e)}"
        )
