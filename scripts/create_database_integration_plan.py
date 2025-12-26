"""Create integration plan for industry databases"""

import json
from pathlib import Path

databases = {
    "chemical_compliance": [
        {
            "name": "TSCA Chemical Inventory",
            "source": "EPA",
            "url": "https://www.epa.gov/tsca-inventory",
            "priority": "high",
            "similar_to": "REACH, Prop 65",
            "data_format": "CSV, Excel, API"
        },
        {
            "name": "RoHS Database",
            "source": "EU",
            "url": "https://ec.europa.eu/environment/waste/rohs_eee/",
            "priority": "high",
            "similar_to": "REACH Annex XVII",
            "data_format": "PDF, Excel, HTML"
        },
        {
            "name": "GHS Classification Database",
            "source": "UN",
            "url": "https://unece.org/transport/dangerous-goods/ghs-rev9-2021",
            "priority": "medium",
            "data_format": "PDF, database"
        }
    ],
    "healthcare": [
        {
            "name": "FDA Orange Book",
            "source": "FDA",
            "url": "https://www.fda.gov/drugs/drug-approvals-and-databases/approved-drug-products-therapeutic-equivalence-evaluations-orange-book",
            "priority": "high",
            "data_format": "PDF, Excel, API"
        },
        {
            "name": "FDA Drug Approvals Database",
            "source": "FDA",
            "url": "https://www.fda.gov/drugs/drug-approvals-and-databases",
            "priority": "medium",
            "data_format": "JSON, XML, CSV"
        },
        {
            "name": "FDA Medical Device Database",
            "source": "FDA",
            "url": "https://www.fda.gov/medical-devices/device-advice-comprehensive-regulatory-assistance/medical-device-databases",
            "priority": "medium",
            "data_format": "CSV, Excel, API"
        }
    ],
    "safety_health": [
        {
            "name": "OSHA CFR Database",
            "source": "OSHA",
            "url": "https://www.osha.gov/laws-regs/regulations/standardnumber",
            "priority": "high",
            "data_format": "HTML, PDF"
        },
        {
            "name": "NIOSH Pocket Guide",
            "source": "NIOSH",
            "url": "https://www.cdc.gov/niosh/npg/",
            "priority": "high",
            "data_format": "Web database, PDF"
        },
        {
            "name": "ACGIH TLVs Database",
            "source": "ACGIH",
            "url": "https://www.acgih.org/tlv-bei-guidelines/",
            "priority": "medium",
            "data_format": "Database, PDF"
        }
    ],
    "financial": [
        {
            "name": "SEC EDGAR Database",
            "source": "SEC",
            "url": "https://www.sec.gov/edgar/searchedgar/companysearch.html",
            "priority": "medium",
            "data_format": "HTML, XML, JSON (API)"
        }
    ],
    "intellectual_property": [
        {
            "name": "USPTO Patent Database",
            "source": "USPTO",
            "url": "https://www.uspto.gov/patents/search",
            "priority": "medium",
            "data_format": "XML, JSON (API), PDF"
        }
    ],
    "standards": [
        {
            "name": "ISO Standards Database",
            "source": "ISO",
            "url": "https://www.iso.org/standards.html",
            "priority": "low",
            "data_format": "PDF (metadata available)"
        },
        {
            "name": "IEC Standards Database",
            "source": "IEC",
            "url": "https://webstore.iec.ch/",
            "priority": "low",
            "data_format": "PDF, database"
        }
    ],
    "food_agriculture": [
        {
            "name": "FDA Food Code",
            "source": "FDA",
            "url": "https://www.fda.gov/food/fda-food-code",
            "priority": "medium",
            "data_format": "PDF, HTML"
        },
        {
            "name": "USDA Food Composition Database",
            "source": "USDA",
            "url": "https://fdc.nal.usda.gov/",
            "priority": "medium",
            "data_format": "JSON, CSV, API"
        }
    ],
    "transportation": [
        {
            "name": "DOT Hazardous Materials Database",
            "source": "DOT",
            "url": "https://www.phmsa.dot.gov/hazmat",
            "priority": "medium",
            "data_format": "PDF, HTML, database"
        }
    ]
}

# Create directory structure
base_dir = Path("data/extracted_docs/compliance")
base_dir.mkdir(parents=True, exist_ok=True)

# Create integration plan
plan = {
    "high_priority": [],
    "medium_priority": [],
    "low_priority": []
}

for category, db_list in databases.items():
    for db in db_list:
        priority = db.get("priority", "medium")
        plan[f"{priority}_priority"].append({
            "name": db["name"],
            "category": category,
            "source": db["source"],
            "url": db["url"],
            "data_format": db["data_format"]
        })

# Save plan
plan_file = Path("DATABASE_INTEGRATION_PLAN.json")
with open(plan_file, 'w') as f:
    json.dump(plan, f, indent=2)

print("=" * 70)
print("DATABASE INTEGRATION PLAN CREATED")
print("=" * 70)
print()
print(f"High Priority Databases: {len(plan['high_priority'])}")
for db in plan['high_priority']:
    print(f"  - {db['name']} ({db['category']})")
print()
print(f"Medium Priority Databases: {len(plan['medium_priority'])}")
for db in plan['medium_priority']:
    print(f"  - {db['name']} ({db['category']})")
print()
print(f"Low Priority Databases: {len(plan['low_priority'])}")
for db in plan['low_priority']:
    print(f"  - {db['name']} ({db['category']})")
print()
print(f"Plan saved to: {plan_file}")
print()
print("Next steps:")
print("  1. Review INDUSTRY_DATABASES_RESEARCH.md for details")
print("  2. Choose databases to integrate")
print("  3. Create extraction scripts (similar to REACH pipeline)")
print("  4. Index extracted data using existing DocumentAgent")

