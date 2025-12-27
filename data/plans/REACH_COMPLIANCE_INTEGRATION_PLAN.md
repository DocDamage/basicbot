---
name: REACH Chemical Compliance Data Integration
overview: Integrate REACH and chemical compliance data sources into the RAG chatbot by creating extraction tools, normalizing data into Markdown files, and enhancing the chatbot for compliance queries with proper tagging and citation.
todos:
  - id: reach_extraction_agent
    content: Create REACH Extraction Agent to pull data from ECHA, EUR-Lex, and PlastChem sources
    status: pending
  - id: reach_tools
    content: Implement REACH tools for extracting substance lists, regulation text, and hazard data
    status: pending
  - id: compliance_tagging_agent
    content: Create Compliance Tagging Agent to add metadata tags (jurisdiction, domain, type, hazard categories)
    status: pending
    dependencies:
      - reach_extraction_agent
  - id: compliance_tools
    content: Build compliance tools for chemical name normalization, CAS validation, and metadata tagging
    status: pending
  - id: normalize_to_markdown
    content: Create normalization pipeline to convert extracted data into structured Markdown files
    status: pending
    dependencies:
      - reach_tools
  - id: enhance_retrieval
    content: Enhance Retrieval Agent with compliance-specific search (CAS numbers, article numbers, hazard filters)
    status: pending
    dependencies:
      - compliance_tools
  - id: compliance_schema
    content: Define compliance metadata schema and tagging structure
    status: pending
  - id: test_integration
    content: Test integration with sample REACH data and compliance queries
    status: pending
    dependencies:
      - reach_extraction_agent
      - compliance_tagging_agent
      - enhance_retrieval
---

# REACH Chemical Compliance Data Integration

## Overview

Integrate REACH (Registration, Evaluation, Authorisation and Restriction of Chemicals) and chemical compliance data sources into the existing RAG chatbot. This will enable the chatbot to answer questions about chemical regulations, hazardous substances, and compliance requirements.

## Data Sources to Integrate

1. **biobricks-ai/reach** - REACH substance extraction from ECHA
2. **PlastChem/DB** - Chemicals & polymers of concern database
3. **nature-of-eU-rules/data-extraction** - EU legislative text extraction (REACH Regulation)
4. **pkaramertzanis/regulatory_grouping** - REACH-focused ML categorization
5. **i6zToolkit** - IUCLID archive handler (if data available)

## Implementation Steps

### Step 1: Data Extraction Tools

Create new agents/tools to extract data from these sources:

**New Components:**
- `src/agents/reach_extraction_agent.py` - Agent for extracting REACH data
- `src/tools/reach_tools.py` - Tools for:
  - Extracting substance lists from ECHA (biobricks-ai/reach approach)
  - Extracting REACH Regulation text from EUR-Lex (nature-of-EU-rules approach)
  - Extracting PlastChem database data
  - Processing IUCLID archives (if available)

**Integration Points:**
- Use existing Document Agent to process extracted data
- Leverage existing BMAD agent framework for coordination

### Step 2: Data Normalization & Markdown Generation

**Normalization Pipeline:**
- Convert REACH articles/sections → individual MD files
- Convert substance lists + identifiers → MD files with metadata
- Structure data with consistent format:
  - REACH articles: Article number, title, content, jurisdiction tags
  - Substances: CAS number, name, hazard classification, REACH status
  - Restrictions: Substance, restriction type, conditions

**Metadata Schema:**
```json
{
  "source": "REACH",
  "type": "article|substance|restriction|svhc|authorization",
  "jurisdiction": "EU",
  "domain": "chemical_regulation",
  "article_number": "Article 33",
  "cas_number": "123-45-6",
  "hazard_tags": ["carcinogenic", "mutagenic"],
  "date_updated": "2024-01-01"
}
```

### Step 3: Compliance Database Structure

**Directory Structure:**
```
data/extracted_docs/
├── reach_regulation/
│   ├── articles/
│   ├── annexes/
│   └── amendments/
├── reach_substances/
│   ├── registered_substances/
│   ├── svhc_list/
│   └── authorized_substances/
├── restrictions/
└── plastchem/
    └── hazardous_chemicals/
```

**Tagging System:**
- Each MD file tagged with:
  - `jurisdiction`: EU, US, etc.
  - `domain`: chemical_regulation, hazard_data, etc.
  - `type`: article, substance, restriction, svhc, authorization
  - `chemical_class`: polymer, organic, inorganic, etc.
  - `hazard_category`: carcinogenic, mutagenic, reprotoxic, etc.

### Step 4: Enhanced RAG for Compliance Queries

**New Features:**
- Compliance-specific retrieval strategies
- Chemical name/CAS number lookup
- Article citation with proper formatting
- Hazard classification filtering
- Multi-jurisdiction support

**Enhanced Retrieval:**
- Chemical name normalization (synonyms, IUPAC names)
- CAS number exact matching
- Article number search
- Hazard tag filtering

## Technical Implementation

### New Agents

1. **REACH Extraction Agent** (`src/agents/reach_extraction_agent.py`)
   - Extracts data from ECHA, EUR-Lex, PlastChem
   - Coordinates with Document Agent for processing
   - Handles API calls, web scraping, file downloads

2. **Compliance Tagging Agent** (`src/agents/compliance_tagging_agent.py`)
   - Tags documents with compliance metadata
   - Validates chemical identifiers (CAS numbers)
   - Links substances to regulations

### New Tools

1. **REACH Tools** (`src/tools/reach_tools.py`)
   - `extract_echa_substances()` - Pull from ECHA database
   - `extract_reach_regulation()` - Extract from EUR-Lex
   - `extract_plastchem_data()` - Process PlastChem DB
   - `normalize_chemical_name()` - Standardize names
   - `validate_cas_number()` - Validate CAS format

2. **Compliance Tools** (`src/tools/compliance_tools.py`)
   - `tag_compliance_metadata()` - Add compliance tags
   - `link_substance_to_regulation()` - Create links
   - `extract_hazard_classification()` - Parse hazard data

### Enhanced Retrieval

- Add chemical name/CAS number filters to vector search
- Implement exact match for identifiers
- Support article number queries
- Filter by hazard categories

## File Structure

```
src/
├── agents/
│   ├── reach_extraction_agent.py    # NEW
│   └── compliance_tagging_agent.py  # NEW
├── tools/
│   ├── reach_tools.py               # NEW
│   └── compliance_tools.py          # NEW
└── config/
    └── compliance_schema.json       # NEW - metadata schema
```

## Integration with Existing System

- **Document Agent**: Process extracted REACH data into MD files
- **Retrieval Agent**: Enhanced with compliance-specific search
- **GUI Agent**: Add compliance query templates/suggestions
- **Memory Agent**: Store compliance query patterns

## Dependencies to Add

- `requests` or `httpx` - For API calls to ECHA/EUR-Lex
- `beautifulsoup4` or `lxml` - For HTML/XML parsing
- `pandas` - For processing substance lists
- `rdkit` or `pubchempy` - For chemical name normalization (optional)

## Workflow

1. **Extraction Phase**:
   - REACH Extraction Agent downloads/processes data
   - Converts to structured format
   - Saves as MD files with metadata

2. **Processing Phase**:
   - Document Agent processes MD files
   - Compliance Tagging Agent adds metadata tags
   - Chunks are created with compliance context

3. **Indexing Phase**:
   - Retrieval Agent indexes with compliance metadata
   - Vector store includes compliance tags for filtering

4. **Query Phase**:
   - Users query about chemicals, regulations, compliance
   - Retrieval uses compliance-specific strategies
   - Responses cite REACH articles, substances, restrictions

## Example Queries Supported

- "What are the REACH restrictions for phthalates?"
- "Is CAS 117-81-7 on the SVHC list?"
- "What does Article 33 of REACH require?"
- "Which chemicals in plastics are of concern according to PlastChem?"
- "What are the authorization requirements for lead compounds?"

## Next Steps

1. Create REACH extraction tools
2. Build compliance tagging system
3. Enhance retrieval for compliance queries
4. Test with sample REACH data
5. Integrate into main chatbot workflow

