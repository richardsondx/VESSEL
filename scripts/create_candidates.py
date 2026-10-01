"""Create an unreviewed development curation queue; NEVER evaluation gold."""

import json
from pathlib import Path

DOMAINS = {
    "economics": (
        "https://www.imf.org/en/Publications/WEO",
        [
            "Find the official visual comparing inflation across advanced and emerging economies.",
            "Locate primary evidence of changes in global real GDP growth since the pandemic.",
            "Find an official chart showing how government debt differs across major economies.",
            "Locate a primary visual relating policy interest rates to inflation "
            "over a tightening cycle.",
            "Find a central-bank chart comparing nominal and real wage growth.",
            "Locate official evidence of changes in household saving rates.",
            "Find the original visual comparing trade volumes across regions.",
            "Locate a chart showing the difference between headline and core inflation.",
            "Find an official visualization of current-account balances across countries.",
            "Find a primary-source table of alternative economic growth projections.",
        ],
    ),
    "finance": (
        "https://www.sec.gov/edgar/search/",
        [
            "Find the original investor visual comparing data-center and other segment revenues.",
            "Locate the source table distinguishing GAAP and adjusted operating income.",
            "Find a company presentation chart showing subscription revenue over several quarters.",
            "Locate a primary-source table showing debt maturity buckets.",
            "Find the original visual describing changes in a bank’s loan-loss provisions.",
            "Locate the source visual showing regional revenue exposure for a public company.",
            "Find a filing table separating operating cash flow from capital expenditures.",
            "Locate primary visual evidence of dilution from stock-based compensation.",
            "Find a published company chart comparing unit sales with average selling prices.",
            "Locate the original visual showing how an insurer’s investment "
            "portfolio is allocated.",
        ],
    ),
    "energy": (
        "https://www.iea.org/data-and-statistics/charts",
        [
            "Find the original agency chart projecting worldwide data-center electricity demand.",
            "Locate primary evidence comparing solar and wind generation growth.",
            "Find the publisher visual showing electricity generation by fuel over time.",
            "Locate an official map of electricity transmission infrastructure.",
            "Find an original chart comparing residential and industrial electricity prices.",
            "Locate a primary visual comparing energy demand under alternative policy scenarios.",
            "Find an official visual showing oil demand by sector.",
            "Locate the original chart separating installed capacity from actual generation.",
            "Find primary evidence comparing battery storage deployment across regions.",
            "Locate an agency table of electricity emissions intensity and underlying data.",
        ],
    ),
    "ai": (
        "https://epoch.ai/research",
        [
            "Find a primary visual showing how training compute has changed for frontier models.",
            "Locate the original benchmark chart comparing model quality and inference cost.",
            "Find published visual evidence of changing inference throughput.",
            "Locate a scientific figure showing the scaling relationship between data and loss.",
            "Find the original multi-panel figure comparing reasoning performance across tasks.",
            "Locate a primary diagram explaining a model’s attention architecture.",
            "Find a publisher chart reporting AI adoption by occupational group.",
            "Locate a primary visual showing benchmark saturation over time.",
            "Find the source table documenting benchmark methodology and model versions.",
            "Locate an original chart comparing accelerator utilization during training.",
        ],
    ),
    "climate": (
        "https://www.ipcc.ch/reports/",
        [
            "Find the original figure comparing warming pathways under emissions scenarios.",
            "Locate the primary multi-panel visual separating human and natural warming drivers.",
            "Find an official map of projected changes in extreme heat.",
            "Locate a publisher chart showing the emissions gap under current policies.",
            "Find the source visual comparing mitigation potential across sectors.",
            "Locate original evidence of changes in ocean heat content.",
            "Find the primary map showing regional exposure to coastal flooding.",
            "Locate an original multi-panel figure on precipitation changes.",
            "Find the official chart distinguishing annual emissions from cumulative emissions.",
            "Locate a report table of uncertainty ranges for climate projections.",
        ],
    ),
    "demographics": (
        "https://population.un.org/wpp/",
        [
            "Find the original population pyramid comparing two census years.",
            "Locate an official map of population change by region.",
            "Find a primary visual comparing fertility rates across countries.",
            "Locate the original chart showing the share of older adults over time.",
            "Find official visual evidence of urban population growth.",
            "Locate a primary map distinguishing population density from total population.",
            "Find the source table showing alternative population projection scenarios.",
            "Locate the original visual comparing life expectancy by sex.",
            "Find an official diagram of population components and migration.",
            "Locate primary visual evidence of changes in household size.",
        ],
    ),
    "labor": (
        "https://www.bls.gov/charts/",
        [
            "Find the original labor-agency chart showing unemployment during a recession.",
            "Locate primary evidence comparing employment and labor-force participation.",
            "Find an official chart of job vacancies relative to unemployment.",
            "Locate a source table separating nominal and inflation-adjusted earnings.",
            "Find the original map of employment growth by region.",
            "Locate an official visual comparing employment across industries.",
            "Find primary evidence of differences in unemployment by age group.",
            "Locate the original multi-panel visual comparing wage growth and productivity.",
            "Find an agency chart showing underemployment alongside headline unemployment.",
            "Locate an official table documenting revisions to payroll estimates.",
        ],
    ),
    "housing": (
        "https://www.census.gov/topics/housing.html",
        [
            "Find an official chart comparing housing starts and building permits.",
            "Locate the original map of rent burdens across metropolitan areas.",
            "Find primary evidence of changes in housing vacancy rates.",
            "Locate a publisher chart comparing rents and home values over time.",
            "Find the official table separating owner-occupied and rental housing.",
            "Locate a primary visual showing mortgage rates and housing affordability.",
            "Find the original map of urban expansion across multiple years.",
            "Locate primary evidence of commercial property vacancy by property type.",
            "Find the source diagram explaining a housing affordability measure.",
            "Locate an original chart of new-home inventory and sales.",
        ],
    ),
    "science": (
        "https://www.nature.com/",
        [
            "Find an original multi-panel figure comparing experimental and control outcomes.",
            "Locate the primary diagram describing an experimental apparatus.",
            "Find the source table documenting measurements and uncertainty.",
            "Locate an original scientific map showing field sampling locations.",
            "Find the original multi-panel figure comparing observed and modeled results.",
            "Locate a publisher figure showing a dose-response relationship.",
            "Find the original technical diagram explaining a measurement pipeline.",
            "Locate a primary visual displaying a distribution rather than just a mean.",
            "Find a scientific table reporting replication across independent experiments.",
            "Locate the original multi-panel figure showing sensitivity to model assumptions.",
        ],
    ),
    "policy": (
        "https://www.cbo.gov/topics/budget",
        [
            "Find an official chart showing projected deficits under a budget baseline.",
            "Locate the original table separating mandatory and discretionary spending.",
            "Find a primary map of drought severity for a specified week.",
            "Locate the official visual comparing revenues and outlays over time.",
            "Find the original flow diagram explaining a public program’s funding.",
            "Locate an official table of alternative policy cost estimates.",
            "Find primary visual evidence of public debt composition.",
            "Locate the original infographic describing an agency’s statistical methodology.",
            "Find an official table of public-service access by geography.",
            "Locate primary evidence showing differences between policy scenarios.",
        ],
    ),
}
rows = []
for domain, (url, queries) in DOMAINS.items():
    for j, query in enumerate(queries):
        rows.append(
            {
                "candidate_id": f"{domain}-{j + 1:02}",
                "domain": domain,
                "information_need": query,
                "publisher_starting_point": url,
                "status": "discovery_required",
                "membership": "unknown",
                "evaluation_eligible": False,
                "gold": None,
                "reviews": [],
                "note": "Development candidate, not a verified answer.",
            }
        )
# Type is a curation target, not a claim about a source item that has not been selected.
for row in rows:
    query = row["information_need"].lower()
    row["target_visual_type"] = (
        "multi_panel"
        if "multi-panel" in query
        else "table"
        if "table" in query
        else "map"
        if "map" in query
        else "diagram"
        if "diagram" in query
        else "other"
        if "infographic" in query
        else "chart"
    )
path = Path(__file__).resolve().parents[1] / "data/core-100-candidates.jsonl"
path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
