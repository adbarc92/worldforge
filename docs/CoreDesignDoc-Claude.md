# Canon Builder - Core Design Document

## Project Vision

**Canon Builder** is a tool for constructing and maintaining logically coherent knowledge systems. Primarily branded as a worldbuilding tool for fiction writers and game designers, it enables users to build internally consistent universes by iteratively proposing, reviewing, and canonizing logical extensions to an established body of knowledge.

The system can also be applied to research synthesis, policy analysis, and framework building—any domain where maintaining logical consistency across a growing corpus of information is valuable.

---

## Core Concept

Users build a "canon" (a set of established, authoritative documents) and then request logical extensions. The AI generates proposals grounded in the existing canon, which users review and either accept (canonizing them) or reject. Over time, this creates a coherent, queryable knowledge base.

**Key Insight:** By separating "canonical" (accepted truth within the system) from "proposed" (AI-generated, pending review), we create a workflow that maintains human oversight while leveraging AI's synthesis capabilities.

---

## User Workflow

### 1. Initialize Canon
- User uploads initial documents (worldbuilding notes, research papers, lore documents, etc.)
- Documents are processed, chunked, and indexed
- System creates initial canon state

### 2. Query & Explore
- User asks questions about the canon
- System retrieves relevant information and answers based solely on canonical documents
- Answers include citations to source documents

### 3. Request Extension
- User prompts: "What are the economic implications of the magic system?" or "How would the introduction of gunpowder affect this medieval society?"
- System generates a coherent extension based on canonical knowledge
- Extension is clearly marked as "Proposed"

### 4. Review & Canonize
- User reviews the proposed extension
- User can:
  - **Accept**: Proposal becomes canonical
  - **Edit**: Modify before accepting
  - **Reject**: Discard proposal
  - **Request revision**: Ask for alternative approach
- Accepted content is versioned and added to canon

### 5. Iterate
- Process repeats with expanding canon
- System maintains consistency with all previous canonized content

---

## Core Features

### Canon Management
- **Document versioning**: Track all changes to canonical documents
- **Provenance tracking**: Every canonical statement traces back to user acceptance
- **Hierarchical organization**: Tag and categorize canonical documents (e.g., "geography", "magic system", "history")
- **Export capability**: Generate consolidated worldbuilding bible/documentation

### Coherence Engine
- **Contradiction detection**: Flag when proposed content conflicts with canon
- **Entailment checking**: Identify logical implications of canonical statements
- **Consistency scoring**: Rate how well a proposal fits with existing canon
- **Gap identification**: Suggest areas where canon is incomplete or ambiguous

### Generation Capabilities
- **Q&A**: Answer questions strictly from canonical knowledge
- **Extensions**: Generate logical developments from existing canon
- **Implications**: Derive consequences of canonical facts
- **Connections**: Identify relationships between canonical elements
- **Summaries**: Synthesize canonical knowledge on specific topics

### Review Interface
- **Side-by-side comparison**: Proposed content next to relevant canonical sources
- **Conflict highlighting**: Visual indicators of potential contradictions
- **Citation view**: See which canonical documents informed the generation
- **Inline editing**: Modify proposals before accepting
- **Comment/annotation**: Add notes explaining acceptance/rejection decisions

---

## Technical Architecture

### Data Layer
```
├── Canonical Documents Store
│   ├── Original uploads (PDFs, text, markdown)
│   ├── Processed/chunked content
│   ├── Embeddings database (vector store)
│   └── Version history
│
├── Proposed Content Store
│   ├── Generated extensions (pending review)
│   ├── Generation metadata (prompt, timestamp, model)
│   └── Review status
│
└── Metadata Store
    ├── Document relationships
    ├── Tags and categories
    ├── User annotations
    └── Coherence scores
```

### Processing Pipeline
1. **Document Ingestion**: Parse, chunk, embed documents
2. **Retrieval**: Semantic search across canonical documents
3. **Generation**: LLM generates content grounded in retrieved context
4. **Validation**: Check for contradictions and coherence issues
5. **Presentation**: Format for user review with citations
6. **Canonization**: Accept user-approved content into canon

### AI Components
- **Embedding Model**: Convert text to vectors for semantic search (e.g., text-embedding-3-large, BGE)
- **Generation Model**: Produce coherent extensions (initially GPT-4/Claude, eventually local models)
- **Reasoning Module**: Logic checking and consistency validation (may require specialized prompting or symbolic reasoning layer)

### Technology Stack (Initial Recommendation)
- **Backend**: Python with FastAPI
- **RAG Framework**: LlamaIndex or LangChain
- **Vector Database**: Chroma, Pinecone, or Qdrant
- **Document Storage**: PostgreSQL + S3/local filesystem
- **Frontend**: React or Vue.js
- **LLM Provider**: OpenAI/Anthropic API initially, with plans for local model support (Ollama, llama.cpp)

---

## Key Differentiators

### vs. Standard RAG Tools
- **Canon Builder** has explicit canonization workflow and versioning
- Focuses on logical consistency, not just retrieval accuracy
- User-in-the-loop for all knowledge additions

### vs. AI Writing Assistants
- **Canon Builder** maintains strict consistency across growing corpus
- Provides structured knowledge management, not just generation
- Designed for complex, interconnected knowledge systems

### vs. Knowledge Management Tools
- **Canon Builder** actively generates implications and extensions
- AI-powered coherence checking and gap identification
- Designed for synthesis, not just organization

---

## Development Phases

### Phase 1: MVP (3-4 months)
- Basic document upload and indexing
- Simple Q&A over canonical documents
- Extension generation with manual review
- Accept/reject workflow
- Basic contradiction detection

**Success Metric**: User can build a small, consistent fictional world (5-10 documents) and successfully extend it without contradictions.

### Phase 2: Enhanced Coherence (3-4 months)
- Advanced contradiction detection
- Coherence scoring for proposals
- Citation and provenance tracking
- Tagging and categorization system
- Improved review interface with conflict highlighting

**Success Metric**: System successfully flags 80%+ of actual contradictions and provides useful coherence scores.

### Phase 3: Advanced Features (4-6 months)
- Gap identification and suggestion system
- Multiple canon "branches" or "timelines"
- Collaborative features (multi-user canon building)
- Export to various formats (PDF, Markdown, JSON)
- Integration with writing tools

**Success Metric**: Power users adopt for professional worldbuilding; handle 100+ document canons.

### Phase 4: Local Models & Optimization (Ongoing)
- Support for local LLM deployment
- Fine-tuned models for specific domains
- Performance optimization for large canons
- Mobile/offline capabilities

**Success Metric**: System runs effectively on consumer hardware with local models.

---

## Target Users

### Primary (Launch Focus)
- **Fiction Writers**: Building fantasy/sci-fi worlds
- **Game Designers**: Creating consistent game lore (TTRPGs, video games)
- **RPG Game Masters**: Managing campaign worlds

### Secondary (Future Expansion)
- **Academic Researchers**: Synthesizing literature across papers
- **Policy Analysts**: Building coherent policy frameworks
- **Knowledge Workers**: Maintaining consistent internal documentation

### Tertiary (Advanced Use Cases)
- **Philosophy/Theory Building**: Constructing logically consistent philosophical systems
- **Worldview Synthesis**: Understanding coherent perspectives from multiple sources

---

## Business Model Options

### Freemium
- **Free Tier**: 10 documents, 50 queries/month, cloud-only
- **Pro Tier** ($15-30/month): Unlimited documents, unlimited queries, advanced features, priority support
- **Team Tier** ($50-100/month): Collaborative features, shared canons, admin controls

### One-Time Purchase
- Desktop application with local model support
- $50-150 one-time fee
- Appeals to privacy-conscious users and offline use cases

### Enterprise
- Self-hosted deployment
- Custom integrations
- SLA and support contracts
- Custom pricing

---

## Risk Mitigation

### Technical Risks
- **Coherence checking accuracy**: Start with conservative detection, improve iteratively with user feedback
- **Scalability**: Test with large document sets early; optimize retrieval and generation pipelines
- **Local model quality**: Begin with cloud APIs, transition to local models only when quality is sufficient

### Product Risks
- **Market fit**: Start with worldbuilding community, validate before expanding to "truth-telling" use cases
- **User adoption**: Ensure workflow is intuitive and adds clear value over existing tools (Notion, WorldAnvil)
- **"Truth" positioning**: Avoid overclaiming; emphasize "internal consistency" and "logical coherence" rather than "truth"

### Ethical Risks
- **Misinformation**: Make clear that coherence ≠ factual accuracy; add disclaimers for non-fiction use cases
- **Misuse**: Consider use cases where building "coherent falsehoods" could be harmful (propaganda, conspiracy theories)
- **Bias**: Ensure system doesn't amplify biases in source documents; provide transparency about AI limitations

---

## Success Criteria

### Year 1
- 1,000+ active users building canons
- Average canon size: 20+ documents
- User retention: 40%+ monthly active
- NPS score: 40+

### Year 2
- 10,000+ active users
- Successful case studies in game design and professional writing
- Expansion into research synthesis use cases
- Sustainable revenue (if freemium model)

### Year 3
- Local model deployment with quality parity to cloud
- Multi-user collaborative canons
- Industry recognition as leading worldbuilding tool
- Path to profitability or significant user growth

---

## Open Questions

1. **How do we handle ambiguity in source documents?** (e.g., contradictory statements in uploaded files)
2. **What's the right balance between AI autonomy and user control?** (how much should the system auto-canonize?)
3. **How do we measure "coherence" quantitatively?** (beyond LLM-based scoring)
4. **Should we support multiple competing canons/timelines?** (e.g., alternate universe versions)
5. **How do we prevent "canon drift" over long sessions?** (ensuring late additions remain consistent with early ones)

---

## Next Steps

1. **User Research**: Interview 10-20 worldbuilders and game designers to validate workflow
2. **Technical Prototype**: Build minimal RAG + review interface to test core concept
3. **Competitive Analysis**: Deep dive on WorldAnvil, Campfire, Notion AI, and RAG tools
4. **Branding & Positioning**: Develop messaging that resonates with worldbuilding community
5. **Architecture Design**: Detailed technical specification for MVP

---

*Document Version: 1.0*
*Last Updated: December 2025*
*Status: Initial Design - Pre-Development*
