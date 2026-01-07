"""
Graph visualization data builder for entity relationships.
Generates JSON format compatible with various graph visualization tools.
"""

import json
from typing import Dict, List, Any
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import networkx as nx

from backend.app.database.models import Entity, Relationship


class GraphBuilder:
    """
    Build graph visualization data from entities and relationships.

    Supports multiple output formats:
    - D3.js force-directed graph
    - Cytoscape.js
    - NetworkX (for analysis)
    - Simple nodes/edges JSON
    """

    def __init__(self):
        """Initialize graph builder."""
        pass

    async def build_graph_json(
        self,
        db: AsyncSession,
        format_type: str = "d3"
    ) -> Dict[str, Any]:
        """
        Build graph data in specified format.

        Args:
            db: Database session
            format_type: Output format ("d3", "cytoscape", "simple")

        Returns:
            Graph data dict
        """
        # Fetch all entities
        entity_result = await db.execute(select(Entity))
        entities = entity_result.scalars().all()

        # Fetch all relationships
        rel_result = await db.execute(select(Relationship))
        relationships = rel_result.scalars().all()

        # Build graph based on format
        if format_type == "d3":
            return self._build_d3_graph(entities, relationships)
        elif format_type == "cytoscape":
            return self._build_cytoscape_graph(entities, relationships)
        elif format_type == "simple":
            return self._build_simple_graph(entities, relationships)
        else:
            raise ValueError(f"Unknown format type: {format_type}")

    def _build_d3_graph(
        self,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> Dict[str, Any]:
        """
        Build D3.js force-directed graph format.

        Args:
            entities: List of entities
            relationships: List of relationships

        Returns:
            D3 graph object
        """
        # Create entity lookup
        entity_lookup = {entity.id: entity for entity in entities}

        # Build nodes
        nodes = []
        for entity in entities:
            nodes.append({
                "id": entity.id,
                "name": entity.name,
                "type": entity.type,
                "description": (entity.canonical_description or "")[:100],  # Truncate
                "confidence": entity.confidence_score or 0.5,
                "group": self._get_type_group(entity.type)
            })

        # Build links
        links = []
        for rel in relationships:
            source_entity = entity_lookup.get(rel.source_entity_id)
            target_entity = entity_lookup.get(rel.target_entity_id)

            if source_entity and target_entity:
                links.append({
                    "source": rel.source_entity_id,
                    "target": rel.target_entity_id,
                    "type": rel.relation_type,
                    "value": rel.confidence_score or 0.5  # Link strength
                })

        return {
            "nodes": nodes,
            "links": links,
            "metadata": {
                "total_nodes": len(nodes),
                "total_links": len(links),
                "format": "d3-force-directed"
            }
        }

    def _build_cytoscape_graph(
        self,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> Dict[str, Any]:
        """
        Build Cytoscape.js graph format.

        Args:
            entities: List of entities
            relationships: List of relationships

        Returns:
            Cytoscape elements object
        """
        elements = []

        # Add nodes
        for entity in entities:
            elements.append({
                "data": {
                    "id": entity.id,
                    "label": entity.name,
                    "type": entity.type,
                    "description": entity.canonical_description or "",
                    "confidence": entity.confidence_score or 0.5
                },
                "group": "nodes",
                "classes": entity.type
            })

        # Add edges
        for rel in relationships:
            elements.append({
                "data": {
                    "id": f"edge_{rel.id}",
                    "source": rel.source_entity_id,
                    "target": rel.target_entity_id,
                    "label": rel.relation_type,
                    "type": rel.relation_type
                },
                "group": "edges"
            })

        return {
            "elements": elements,
            "metadata": {
                "total_nodes": len([e for e in elements if e["group"] == "nodes"]),
                "total_edges": len([e for e in elements if e["group"] == "edges"]),
                "format": "cytoscape"
            }
        }

    def _build_simple_graph(
        self,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> Dict[str, Any]:
        """
        Build simple nodes/edges format.

        Args:
            entities: List of entities
            relationships: List of relationships

        Returns:
            Simple graph object
        """
        nodes = []
        for entity in entities:
            nodes.append({
                "id": entity.id,
                "name": entity.name,
                "type": entity.type,
                "description": entity.canonical_description or ""
            })

        edges = []
        for rel in relationships:
            edges.append({
                "id": rel.id,
                "source": rel.source_entity_id,
                "target": rel.target_entity_id,
                "type": rel.relation_type
            })

        return {
            "nodes": nodes,
            "edges": edges
        }

    def _get_type_group(self, entity_type: str) -> int:
        """
        Get group number for entity type (for color coding).

        Args:
            entity_type: Entity type

        Returns:
            Group number (1-5)
        """
        groups = {
            "character": 1,
            "location": 2,
            "event": 3,
            "concept": 4,
            "item": 5
        }

        return groups.get(entity_type, 0)

    async def export_graph_json(
        self,
        db: AsyncSession,
        export_path: Path,
        format_type: str = "d3"
    ) -> Path:
        """
        Export graph to JSON file.

        Args:
            db: Database session
            export_path: Directory to export to
            format_type: Graph format

        Returns:
            Path to created JSON file
        """
        graph_data = await self.build_graph_json(db, format_type)

        # Write to file
        json_path = export_path / "graph.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

        return json_path

    async def build_networkx_graph(
        self,
        db: AsyncSession
    ) -> nx.DiGraph:
        """
        Build NetworkX directed graph for analysis.

        Args:
            db: Database session

        Returns:
            NetworkX DiGraph
        """
        # Fetch entities and relationships
        entity_result = await db.execute(select(Entity))
        entities = entity_result.scalars().all()

        rel_result = await db.execute(select(Relationship))
        relationships = rel_result.scalars().all()

        # Create graph
        G = nx.DiGraph()

        # Add nodes
        for entity in entities:
            G.add_node(
                entity.id,
                name=entity.name,
                type=entity.type,
                description=entity.canonical_description or "",
                confidence=entity.confidence_score or 0.5
            )

        # Add edges
        for rel in relationships:
            G.add_edge(
                rel.source_entity_id,
                rel.target_entity_id,
                type=rel.relation_type,
                confidence=rel.confidence_score or 0.5
            )

        return G

    async def compute_graph_metrics(
        self,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Compute graph analysis metrics.

        Args:
            db: Database session

        Returns:
            Graph metrics
        """
        G = await self.build_networkx_graph(db)

        # Compute metrics
        metrics = {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "density": nx.density(G),
            "is_connected": nx.is_weakly_connected(G) if G.number_of_nodes() > 0 else False
        }

        # Most connected entities (by degree)
        if G.number_of_nodes() > 0:
            degree_centrality = nx.degree_centrality(G)
            top_entities = sorted(
                degree_centrality.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            # Get entity names
            entity_result = await db.execute(
                select(Entity).where(Entity.id.in_([e[0] for e in top_entities]))
            )
            entities = {e.id: e.name for e in entity_result.scalars().all()}

            metrics["most_connected"] = [
                {
                    "id": entity_id,
                    "name": entities.get(entity_id, "Unknown"),
                    "centrality": centrality
                }
                for entity_id, centrality in top_entities
            ]

        # Connected components
        if G.number_of_nodes() > 0:
            weakly_connected = list(nx.weakly_connected_components(G))
            metrics["connected_components"] = len(weakly_connected)
            metrics["largest_component_size"] = max(len(c) for c in weakly_connected) if weakly_connected else 0

        return metrics

    def create_html_visualization(
        self,
        graph_data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """
        Create standalone HTML visualization.

        Args:
            graph_data: Graph data (D3 format)
            output_path: Path to write HTML file

        Returns:
            Path to HTML file
        """
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Worldbuilding Canon Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            margin: 0;
            overflow: hidden;
            font-family: Arial, sans-serif;
        }
        #graph {
            width: 100vw;
            height: 100vh;
        }
        .node {
            stroke: #fff;
            stroke-width: 1.5px;
            cursor: pointer;
        }
        .link {
            stroke: #999;
            stroke-opacity: 0.6;
        }
        .node text {
            font-size: 10px;
            pointer-events: none;
        }
        #info {
            position: absolute;
            top: 10px;
            left: 10px;
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div id="info">
        <h3>Canon Graph</h3>
        <p>Nodes: <span id="nodeCount"></span></p>
        <p>Links: <span id="linkCount"></span></p>
    </div>
    <div id="graph"></div>

    <script>
        const graphData = """ + json.dumps(graph_data) + """;

        const width = window.innerWidth;
        const height = window.innerHeight;

        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.links).id(d => d.id))
            .force("charge", d3.forceManyBody().strength(-100))
            .force("center", d3.forceCenter(width / 2, height / 2));

        const link = svg.append("g")
            .selectAll("line")
            .data(graphData.links)
            .join("line")
            .attr("class", "link");

        const node = svg.append("g")
            .selectAll("circle")
            .data(graphData.nodes)
            .join("circle")
            .attr("class", "node")
            .attr("r", 5)
            .attr("fill", d => {
                const colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"];
                return colors[d.group - 1] || "#999";
            })
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("title")
            .text(d => `${d.name} (${d.type})`);

        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
        });

        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }

        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }

        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }

        document.getElementById("nodeCount").textContent = graphData.nodes.length;
        document.getElementById("linkCount").textContent = graphData.links.length;
    </script>
</body>
</html>
        """

        html_path = output_path / "graph_visualization.html"
        html_path.write_text(html_template, encoding="utf-8")

        return html_path
