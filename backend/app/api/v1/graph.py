"""
Knowledge graph endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from loguru import logger

from app.models.schemas import Entity, Relationship, GraphQuery
from app.core.security import get_current_user

router = APIRouter()


@router.get("/entities", response_model=List[Entity])
async def list_entities(
    entity_type: str | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    List all entities in the knowledge graph

    TODO: Implement Neo4j query
    """
    logger.info(f"Listing entities (type={entity_type}, skip={skip}, limit={limit})")

    # TODO: Query Neo4j for entities

    return []


@router.get("/entities/{entity_id}", response_model=Entity)
async def get_entity(
    entity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get details for a specific entity

    TODO: Implement Neo4j lookup
    """
    logger.info(f"Getting entity: {entity_id}")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Entity {entity_id} not found"
    )


@router.get("/entities/{entity_id}/related", response_model=List[Entity])
async def get_related_entities(
    entity_id: str,
    depth: int = 2,
    current_user: dict = Depends(get_current_user)
):
    """
    Get related entities via graph traversal

    TODO: Implement Neo4j traversal
    """
    logger.info(f"Getting related entities for {entity_id} (depth={depth})")

    # TODO: Traverse Neo4j graph to depth

    return []


@router.get("/relationships", response_model=List[Relationship])
async def list_relationships(
    source_id: str | None = None,
    target_id: str | None = None,
    current_user: dict = Depends(get_current_user)
):
    """
    List relationships in the knowledge graph

    TODO: Implement Neo4j query
    """
    logger.info(f"Listing relationships (source={source_id}, target={target_id})")

    # TODO: Query Neo4j for relationships

    return []
