# Manual Download Guides for Industry Databases

Some databases require manual downloads due to authentication, complex forms, or JavaScript rendering. This guide provides step-by-step instructions for each database.

## Databases Requiring Manual Downloads

### 1. TSCA Chemical Inventory (EPA)
**URL:** https://www.epa.gov/tsca-inventory

**Steps:**
1. Visit https://www.epa.gov/tsca-inventory
2. Look for "Download" or "Data" section
3. Download the latest TSCA Inventory CSV or Excel file
4. Save to: `data/extracted_docs/compliance/tsca_chemical_inventory/raw/tsca_inventory_manual_[YYYYMMDD].csv`

**Alternative:** EPA may provide API access - check https://www.epa.gov/tsca-inventory/tsca-inventory-data

---

### 2. FDA Orange Book
**URL:** https://www.fda.gov/drugs/drug-approvals-and-databases/approved-drug-products-therapeutic-equivalence-evaluations-orange-book

**Steps:**
1. Visit the Orange Book page
2. Click "Download" or "Data Files" link
3. Download the Excel or CSV file
4. Save to: `data/extracted_docs/compliance/fda_orange_book/raw/fda_orange_book_manual_[YYYYMMDD].xlsx`

**Note:** FDA also provides API access at https://open.fda.gov/

---

### 3. ACGIH TLVs Database
**URL:** https://www.acgih.org/tlv-bei-guidelines/

**Steps:**
1. Visit the ACGIH website
2. **Note:** ACGIH TLVs require membership/subscription
3. If you have access:
   - Log in to your account
   - Navigate to TLVs section
   - Download the database or PDF
   - Save to: `data/extracted_docs/compliance/acgih_tlvs_database/raw/acgih_tlvs_manual_[YYYYMMDD].pdf`

**Alternative:** Use publicly available TLVs from OSHA or NIOSH

---

### 4. ISO Standards Database
**URL:** https://www.iso.org/standards.html

**Steps:**
1. Visit ISO website
2. **Note:** ISO standards require purchase
3. For metadata only:
   - Search for standards
   - Export search results as CSV
   - Save to: `data/extracted_docs/compliance/iso_standards_database/raw/iso_standards_metadata_[YYYYMMDD].csv`

**Alternative:** Use ISO API if available (may require API key)

---

### 5. IEC Standards Database
**URL:** https://webstore.iec.ch/

**Steps:**
1. Visit IEC webstore
2. **Note:** IEC standards require purchase
3. For metadata only:
   - Search for standards
   - Export search results
   - Save to: `data/extracted_docs/compliance/iec_standards_database/raw/iec_standards_metadata_[YYYYMMDD].csv`

---

### 6. GHS Classification Database
**URL:** https://unece.org/transport/dangerous-goods/ghs-rev9-2021

**Steps:**
1. Visit UNECE GHS page
2. Look for "Download" or "Data" section
3. Download GHS classification tables (PDF or Excel)
4. Save to: `data/extracted_docs/compliance/ghs_classification_database/raw/ghs_classification_manual_[YYYYMMDD].pdf`

---

### 7. FDA Food Code
**URL:** https://www.fda.gov/food/fda-food-code

**Steps:**
1. Visit FDA Food Code page
2. Download the latest Food Code PDF
3. Save to: `data/extracted_docs/compliance/fda_food_code/raw/fda_food_code_manual_[YYYYMMDD].pdf`

---

## After Manual Download

Once you've manually downloaded files:

1. **Place files in the correct directory:**
   - Each database has a `raw/` subdirectory
   - Use the naming convention: `[database_name]_manual_[YYYYMMDD].[ext]`

2. **Run the extractor again:**
   ```bash
   python extract_and_index_all_databases.py
   ```

3. **The extractor will:**
   - Detect the new manual files
   - Parse them using the same logic
   - Generate markdown files
   - Index them in the vector database

## API Keys (Optional)

Some databases offer API access with better data quality:

### FDA OpenFDA API
- **URL:** https://open.fda.gov/
- **Registration:** Free, requires email
- **Documentation:** https://open.fda.gov/apis/

### SEC EDGAR API
- **URL:** https://www.sec.gov/edgar/sec-api-documentation
- **Registration:** Free, no key required (rate limits apply)
- **Documentation:** https://www.sec.gov/edgar/sec-api-documentation

### USPTO Patent API
- **URL:** https://developer.uspto.gov/
- **Registration:** Free, requires registration
- **Documentation:** https://developer.uspto.gov/

### USDA FoodData Central API
- **URL:** https://fdc.nal.usda.gov/api-guide.html
- **Registration:** Free, API key available
- **Documentation:** https://fdc.nal.usda.gov/api-guide.html

---

## Automation Notes

For databases that require JavaScript rendering (dynamic content):

1. **Selenium/Playwright Support:**
   - Some extractors can be enhanced with browser automation
   - See `src/extractors/` for extractors that support this

2. **API First Approach:**
   - Always try API access first (better data quality)
   - Fall back to web scraping if API unavailable
   - Use manual download as last resort

3. **Scheduled Updates:**
   - Set up cron jobs or scheduled tasks to re-run extractors
   - Check for updates weekly/monthly depending on database

---

## Questions?

If you need help with manual downloads or API setup, check:
- Database-specific documentation in `INDUSTRY_DATABASES_RESEARCH.md`
- Extractor source code in `src/extractors/[category]/[database]_extractor.py`

