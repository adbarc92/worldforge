"""
Prompt templates for LLM tasks.
Centralized location for all prompt engineering.
"""

# Entity Extraction
ENTITY_EXTRACTION_PROMPT = """You are an expert at analyzing fictional narratives and extracting structured entities.

Analyze the following text and extract entities of these types:
- character: People, creatures, sentient beings
- location: Places, buildings, regions, worlds
- event: Significant happenings, battles, ceremonies
- concept: Ideas, magic systems, philosophies, organizations
- item: Important objects, artifacts, weapons

For each entity, provide:
- name: The entity's name
- type: One of the 5 types listed above
- description: A concise description (1-2 sentences)
- confidence: Your confidence in this extraction (0.0 to 1.0)

Text to analyze:
{text}

Respond with a JSON array of entities."""

# Entity Extraction Schema
ENTITY_EXTRACTION_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "type": {"type": "string", "enum": ["character", "location", "event", "concept", "item"]},
            "description": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "required": ["name", "type", "description", "confidence"]
    }
}

# Relationship Extraction
RELATIONSHIP_EXTRACTION_PROMPT = """Given these two entities, determine if there is a meaningful relationship between them based on the provided text.

Entity 1: {entity1_name} ({entity1_type})
Entity 2: {entity2_name} ({entity2_type})

Text context:
{text}

If a relationship exists, provide:
- relation_type: The type of relationship (e.g., "located_in", "allied_with", "created_by", "participates_in", "owns")
- evidence: The exact quote from the text supporting this relationship
- confidence: Your confidence in this relationship (0.0 to 1.0)

If no meaningful relationship exists, respond with null.

Respond with JSON."""

# Relationship Extraction Schema
RELATIONSHIP_EXTRACTION_SCHEMA = {
    "oneOf": [
        {"type": "null"},
        {
            "type": "object",
            "properties": {
                "relation_type": {"type": "string"},
                "evidence": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["relation_type", "evidence", "confidence"]
        }
    ]
}

# Contradiction Detection (Simple Version)
CONTRADICTION_DETECTION_PROMPT = """You are an expert at detecting contradictions in fictional worldbuilding.

Compare these two entity descriptions and determine if they contradict each other:

Entity 1: {name1}
{description1}

Entity 2: {name2}
{description2}

Analyze if these descriptions contain contradictions, inconsistencies, or timeline conflicts.

Respond with:
- is_contradiction: true if contradictory, false if consistent/complementary
- type: "description_mismatch", "timeline_conflict", "attribute_contradiction", or "consistent"
- severity: "high" (major plot/canon break), "medium" (notable inconsistency), or "low" (minor detail)
- description: Brief description of the conflict (or why they're consistent)
- explanation: Detailed analysis

Respond with JSON."""

# Contradiction Detection (Legacy Version with Sources)
CONTRADICTION_DETECTION_PROMPT_WITH_SOURCES = """Compare these two descriptions of the same entity and determine if they contradict each other.

Entity: {entity_name} ({entity_type})

Description 1 (from {source1}):
{description1}

Description 2 (from {source2}):
{description2}

Analyze if these descriptions contain contradictions, inconsistencies, or timeline mismatches.

Provide:
- contradictory: true if there is a contradiction, false if complementary/consistent
- conflict_type: One of: "contradiction", "inconsistent_characterization", "timeline_mismatch", "complementary"
- severity: "high", "medium", or "low"
- explanation: Detailed explanation of the conflict or why they're consistent

Respond with JSON."""

# Contradiction Detection Schema
CONTRADICTION_DETECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "contradictory": {"type": "boolean"},
        "conflict_type": {
            "type": "string",
            "enum": ["contradiction", "inconsistent_characterization", "timeline_mismatch", "complementary"]
        },
        "severity": {"type": "string", "enum": ["high", "medium", "low"]},
        "explanation": {"type": "string"}
    },
    "required": ["contradictory", "conflict_type", "severity", "explanation"]
}

# Query with Citations
QUERY_WITH_CITATIONS_PROMPT = """You are a knowledgeable assistant helping users understand their fictional world.

Answer the user's question based ONLY on the provided context. Include inline citations using [^1], [^2], etc. to reference specific context sections.

Context sections:
{context}

User question:
{question}

Rules:
1. Only use information from the provided context
2. Cite sources using [^N] where N is the context section number
3. If the context doesn't contain enough information, say "I don't have enough information to answer that."
4. Be specific and detailed in your answer

Answer:"""

# Query Response Schema (for structured responses)
QUERY_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "citation_number": {"type": "integer"},
                    "context_index": {"type": "integer"},
                    "excerpt": {"type": "string"}
                },
                "required": ["citation_number", "context_index", "excerpt"]
            }
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "required": ["answer", "citations", "confidence"]
}
