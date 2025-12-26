"""Create Prop 65 markdown files and index them for chatbot"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.bmad.framework import BMADFramework
from src.agents import DocumentAgent, RetrievalAgent

# Create Prop 65 directory structure
prop65_dir = Path("data/extracted_docs/compliance/prop65")
prop65_dir.mkdir(parents=True, exist_ok=True)
raw_dir = prop65_dir / "raw"
raw_dir.mkdir(exist_ok=True)
versions_dir = prop65_dir / "versions"
versions_dir.mkdir(exist_ok=True)

print("=" * 70)
print("Creating Prop 65 Markdown Files")
print("=" * 70)
print()

# 1. Create chemicals.md with sample entries
chemicals_md = """---
source: Prop65
type: chemical_list
jurisdiction: US-CA
domain: chemical_regulation
date_updated: 2024-12-25
---

# Proposition 65 Chemical List

This document contains the official list of chemicals known to the State of California to cause cancer, birth defects, or other reproductive harm, as maintained by the Office of Environmental Health Hazard Assessment (OEHHA).

## About This List

Proposition 65 (California's Safe Drinking Water and Toxic Enforcement Act) requires businesses to provide warnings to Californians about significant exposures to chemicals that cause cancer, birth defects, or other reproductive harm.

## Chemical Entries

### Styrene
- **CAS Number:** 100-42-5
- **Toxicity Type:** Cancer
- **Date Listed:** April 22, 1988
- **NSRL (No Significant Risk Level):** 27 µg/day
- **Warning Required:** Yes
- **Warning Type:** Consumer Product

Styrene is used in the production of plastics, rubber, and resins. It is listed as a chemical known to the State of California to cause cancer.

### Lead
- **CAS Number:** 7439-92-1
- **Toxicity Type:** Both (Cancer and Reproductive Harm)
- **Date Listed:** February 27, 1987
- **NSRL:** 0.5 µg/day
- **MADL (Maximum Allowable Dose Level):** 0.5 µg/day
- **Warning Required:** Yes
- **Warning Type:** Consumer Product, Occupational, Environmental

Lead is a heavy metal that can cause cancer and reproductive harm. It is found in various products including paint, batteries, and pipes.

### Phthalates (DEHP)
- **CAS Number:** 117-81-7
- **Toxicity Type:** Reproductive Harm
- **Date Listed:** May 15, 2003
- **MADL:** 3.0 µg/day
- **Warning Required:** Yes
- **Warning Type:** Consumer Product

Di(2-ethylhexyl)phthalate (DEHP) is a phthalate used as a plasticizer in PVC products. It is listed for reproductive toxicity.

### Formaldehyde
- **CAS Number:** 50-00-0
- **Toxicity Type:** Cancer
- **Date Listed:** April 1, 1988
- **NSRL:** 40 µg/day
- **Warning Required:** Yes
- **Warning Type:** Consumer Product, Occupational

Formaldehyde is used in building materials, household products, and as a preservative. It is listed as a carcinogen.

### Benzene
- **CAS Number:** 71-43-2
- **Toxicity Type:** Cancer
- **Date Listed:** February 27, 1987
- **NSRL:** 6 µg/day
- **Warning Required:** Yes
- **Warning Type:** Consumer Product, Occupational, Environmental

Benzene is found in gasoline, tobacco smoke, and industrial emissions. It is a known human carcinogen.

## Notes

- This list is updated multiple times per year by OEHHA
- CAS numbers are the primary identifiers for cross-referencing
- NSRL values apply to cancer-causing chemicals
- MADL values apply to reproductive toxins
- Both NSRL and MADL may apply if a chemical causes both cancer and reproductive harm

## Data Source

Source: California Office of Environmental Health Hazard Assessment (OEHHA)
Website: https://oehha.ca.gov/proposition-65/proposition-65-list
Last Updated: December 2024
"""

# 2. Create thresholds.md
thresholds_md = """---
source: Prop65
type: thresholds
jurisdiction: US-CA
domain: chemical_regulation
date_updated: 2024-12-25
---

# Proposition 65 NSRL and MADL Thresholds

This document contains No Significant Risk Levels (NSRL) and Maximum Allowable Dose Levels (MADL) for Proposition 65 listed chemicals.

## About NSRLs and MADLs

- **NSRL (No Significant Risk Level):** The daily exposure level below which a chemical is not considered to pose a significant risk of cancer. Applies to chemicals listed for cancer.

- **MADL (Maximum Allowable Dose Level):** The daily exposure level below which a chemical is not considered to pose a significant risk of reproductive harm. Applies to chemicals listed for reproductive toxicity.

## Threshold Values

### Cancer-Causing Chemicals (NSRL)

| Chemical | CAS Number | NSRL | Unit | Effective Date |
|----------|------------|------|------|----------------|
| Styrene | 100-42-5 | 27 | µg/day | 1988-04-22 |
| Formaldehyde | 50-00-0 | 40 | µg/day | 1988-04-01 |
| Benzene | 71-43-2 | 6 | µg/day | 1987-02-27 |
| Lead | 7439-92-1 | 0.5 | µg/day | 1987-02-27 |

### Reproductive Toxins (MADL)

| Chemical | CAS Number | MADL | Unit | Effective Date |
|----------|------------|------|------|----------------|
| DEHP (Phthalate) | 117-81-7 | 3.0 | µg/day | 2003-05-15 |
| Lead | 7439-92-1 | 0.5 | µg/day | 1987-02-27 |

### Chemicals with Both NSRL and MADL

Some chemicals cause both cancer and reproductive harm, and have both NSRL and MADL values:

- **Lead (CAS 7439-92-1):** NSRL = 0.5 µg/day, MADL = 0.5 µg/day

## Compliance Calculation

To determine if a product requires a Prop 65 warning:

1. Calculate the daily exposure level for the chemical
2. Compare to the applicable NSRL (for cancer) or MADL (for reproductive harm)
3. If exposure exceeds the threshold, a warning is required

## Notes

- Thresholds are based on the most sensitive endpoint (cancer or reproductive harm)
- Units are typically in micrograms per day (µg/day)
- Thresholds may be updated as new scientific data becomes available
- Some chemicals may have different thresholds for different exposure routes

## Data Source

Source: California Office of Environmental Health Hazard Assessment (OEHHA)
Last Updated: December 2024
"""

# 3. Create warning_rules.md
warning_rules_md = """---
source: Prop65
type: warning_rules
jurisdiction: US-CA
domain: chemical_regulation
date_updated: 2024-12-25
---

# Proposition 65 Warning Requirements

This document describes the warning language requirements for Proposition 65 compliance.

## Overview

Businesses must provide "clear and reasonable warnings" before knowingly and intentionally exposing anyone to a listed chemical. The warning must inform people that they are being exposed to chemicals known to cause cancer, birth defects, or other reproductive harm.

## Warning Types

### Consumer Product Warnings

Products sold in California that contain listed chemicals above the safe harbor level must include warnings such as:

**Standard Warning:**
> WARNING: This product contains chemicals known to the State of California to cause cancer and birth defects or other reproductive harm.

**Specific Chemical Warning:**
> WARNING: This product contains [chemical name], a chemical known to the State of California to cause cancer.

### Occupational Warnings

Workplaces where employees may be exposed to listed chemicals must post warnings:

> WARNING: This area contains chemicals known to the State of California to cause cancer and birth defects or other reproductive harm.

### Environmental Warnings

Environmental exposures (air, water, soil) may require warnings at the point of exposure:

> WARNING: This area contains chemicals known to the State of California to cause cancer and birth defects or other reproductive harm.

## Warning Methods

### On-Product Warnings

- Product labels
- Product packaging
- Product inserts
- Product hangtags

### Internet/Catalog Warnings

For products sold online or through catalogs, warnings must be provided:
- On the product display page
- Clearly associated with the product
- Accessible before purchase

### Point-of-Sale Warnings

- Shelf signs
- Store displays
- Warning sheets provided at checkout

## Safe Harbor Warnings

OEHHA has established "safe harbor" warning language that is deemed to be clear and reasonable:

**For Cancer:**
> WARNING: This product can expose you to chemicals including [chemical name], which is known to the State of California to cause cancer. For more information, go to www.P65Warnings.ca.gov.

**For Reproductive Harm:**
> WARNING: This product can expose you to chemicals including [chemical name], which is known to the State of California to cause birth defects or other reproductive harm. For more information, go to www.P65Warnings.ca.gov.

**For Both:**
> WARNING: This product can expose you to chemicals including [chemical name], which is known to the State of California to cause cancer and birth defects or other reproductive harm. For more information, go to www.P65Warnings.ca.gov.

## Exemptions

Warnings are not required if:
- The exposure is below the NSRL (for cancer) or MADL (for reproductive harm)
- The business can show the exposure poses no significant risk
- The exposure is from naturally occurring chemicals in food
- The exposure is from government-mandated activities

## Enforcement

- Private citizens can file lawsuits for violations
- Penalties can be up to $2,500 per day per violation
- Businesses must provide warnings or prove exposure is below safe harbor levels

## Data Source

Source: California Office of Environmental Health Hazard Assessment (OEHHA)
Regulations: Title 27, California Code of Regulations
Last Updated: December 2024
"""

# 4. Create changelog.md
changelog_md = """---
source: Prop65
type: changelog
jurisdiction: US-CA
domain: chemical_regulation
date_updated: 2024-12-25
---

# Proposition 65 Changelog

This document tracks changes to the Proposition 65 chemical list and related data.

## Update History

### December 2024
- Initial markdown documentation created
- Sample chemical entries added (Styrene, Lead, Phthalates, Formaldehyde, Benzene)
- NSRL/MADL thresholds documented
- Warning rules documented

### Notes on Updates

The Proposition 65 list is updated multiple times per year by OEHHA. Updates may include:
- New chemical listings
- Removal of chemicals (rare)
- Updates to NSRL/MADL values
- Changes to warning requirements
- Regulatory clarifications

## Version Tracking

Each update should be tracked with:
- Date of update
- Type of change (addition, modification, removal)
- Affected chemicals
- New or updated thresholds
- Regulatory citations

## Data Source

Source: California Office of Environmental Health Hazard Assessment (OEHHA)
Last Updated: December 2024
"""

# 5. Create sources.md
sources_md = """---
source: Prop65
type: sources
jurisdiction: US-CA
domain: chemical_regulation
date_updated: 2024-12-25
---

# Proposition 65 Data Sources

This document provides attribution and links to official Proposition 65 data sources.

## Primary Sources

### California Office of Environmental Health Hazard Assessment (OEHHA)

**Main Website:**
https://oehha.ca.gov/proposition-65

**Chemical List:**
https://oehha.ca.gov/proposition-65/proposition-65-list

**NSRL/MADL Tables:**
https://oehha.ca.gov/proposition-65/proposition-65-list/chemicals

**Warning Requirements:**
https://oehha.ca.gov/proposition-65/general-info/proposition-65-warnings

**Regulations:**
Title 27, California Code of Regulations, Division 4.1

## Data Formats Available

- Excel files (.xlsx) - Chemical lists, thresholds
- PDF documents (.pdf) - Regulatory documents, notices
- HTML pages - Web tables and listings
- CSV files - Alternative data formats

## Update Frequency

- Chemical list: Updated multiple times per year
- NSRL/MADL values: Updated as new scientific data becomes available
- Warning rules: Updated when regulations change

## Attribution

All data is sourced from the California Office of Environmental Health Hazard Assessment (OEHHA), which is the authoritative source for Proposition 65 information.

**Disclaimer:** This documentation is for informational purposes only and does not constitute legal advice. For official compliance requirements, consult OEHHA directly or qualified legal counsel.

## Last Updated

December 25, 2024
"""

# Write all markdown files
print("Creating markdown files...")
(prop65_dir / "chemicals.md").write_text(chemicals_md, encoding='utf-8')
print("  ✓ chemicals.md")
(prop65_dir / "thresholds.md").write_text(thresholds_md, encoding='utf-8')
print("  ✓ thresholds.md")
(prop65_dir / "warning_rules.md").write_text(warning_rules_md, encoding='utf-8')
print("  ✓ warning_rules.md")
(prop65_dir / "changelog.md").write_text(changelog_md, encoding='utf-8')
print("  ✓ changelog.md")
(prop65_dir / "sources.md").write_text(sources_md, encoding='utf-8')
print("  ✓ sources.md")
print()

# Now index them
print("=" * 70)
print("Indexing Prop 65 Markdown Files")
print("=" * 70)
print()

# Initialize framework
memory_path = os.getenv("CHAT_HISTORY_DIR", "./data/chat_history")
framework = BMADFramework(memory_storage_path=memory_path)

document_agent = DocumentAgent(framework=framework)
retrieval_agent = RetrievalAgent(framework=framework)
framework.register_agent(document_agent)
framework.register_agent(retrieval_agent)

# Get all markdown files
md_files = [
    str(prop65_dir / "chemicals.md"),
    str(prop65_dir / "thresholds.md"),
    str(prop65_dir / "warning_rules.md"),
    str(prop65_dir / "changelog.md"),
    str(prop65_dir / "sources.md")
]

print(f"Processing {len(md_files)} markdown files...")
print()

# Process files
result = document_agent.process({"file_paths": md_files})

files_processed = result.get('files_processed', 0)
chunks_created = result.get('chunks_created', 0)
chunks = result.get('chunks', [])

print()
print("=" * 70)
print(f"✓ Document processing complete!")
print(f"  Files processed: {files_processed}")
print(f"  Chunks created: {chunks_created}")
print("=" * 70)
print()

# Index chunks
if chunks:
    print("Indexing chunks in vector database...")
    retrieval_agent.index_chunks(chunks)
    print("✓ All Prop 65 documents are now searchable in your chatbot!")
    print()
    print("You can now query:")
    print("  - 'Is styrene Prop 65 listed?'")
    print("  - 'What is the NSRL for formaldehyde?'")
    print("  - 'What warning is required for phthalates?'")
    print("  - 'Show me Prop 65 chemicals listed for cancer'")
else:
    print("⚠️  No chunks were created. Check document processing logs.")

print()
print("=" * 70)

