# Grocery access in Chicago 2021–2025

Emmanuel Amissah Sampson · **Release candidate: 17 November 2026 · v1.0.0**

This study examines five verified grocery closures and one replacement opening at five Chicago locations. It combines reviewed business dates, USDA SNAP authorization histories, Chicago inspections, Census tract context and a fixed historical street network. The current release is a descriptive access study. Observed mobility and causal effects remain pending a reviewed licensed input.

## Main findings

Around the Kenwood Walmart, the population-weighted modeled walking time rises from **11.48 to 16.10 minutes** across 22 tract origins. Around the Englewood Whole Foods, it rises from **14.41 to 16.51 minutes** across 14 origins. Save A Lot at the same Englewood address reverses that modeled proximity change. Other Walmart catchments show smaller changes. These are nearest-outlet access estimates; they are not measured customer journeys or evidence of a switch from walking to driving.

## Read the research

[Public website](https://emmanuelsampson-prog.github.io/grocery-access-chicago/) · [GitHub release and full project package](https://github.com/emmanuelsampson-prog/grocery-access-chicago/releases/tag/v1.0.0)

- [Academic report source](docs/report.md)
- [Word report](outputs/public/Chicago_Grocery_Access_Report.docx)
- [PDF report](outputs/public/Chicago_Grocery_Access_Report.pdf)
- [01 Historical evidence notebook](notebooks/01_historical_evidence.ipynb)
- [02 Before and after access notebook](notebooks/02_before_after_access.ipynb)
- [03 Mobility audit and causal design notebook](notebooks/03_mobility_and_causal_design.ipynb)
- [Research protocol](docs/research_protocol.md), [data dictionary](docs/data_dictionary.md), [mobility specification](docs/mobility_data_request.md)

## Reproduce

Use Python 3.12. The dependency versions in `requirements.txt` record the tested environment.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.download
python -m src.prepare
python -m src.network
python -m src.analysis
python -m src.figures
python -m scripts.create_notebooks
python scripts/execute_notebooks.py
python -m unittest discover -s tests
python scripts/build_report.py
python scripts/build_explorer.py
python scripts/build_site.py
```

On Windows activate `.venv\Scripts\activate` instead. The source download includes a ~244 MB historical Illinois OSM extract and streams national ACS tables to retain Cook County records. Allow several GB of memory for graph preparation. Downloads are cached and checksummed. The routing cache is invalidated by input-coordinate or network changes. If kernel sockets are unavailable, `python scripts/execute_notebooks.py --inprocess` executes the actual notebook cells with IPython and captures outputs. Execution metadata identifies the backend used.

The checked-in processed data and derived network support rerunning the analysis without downloading the raw national inputs. The GitHub Release package includes the processed inputs and all four derived street-graph files. The same graph files are also available individually in the release. To reproduce the PDF, export the generated Word file with LibreOffice or Word; the supplied PDF was rendered from that same Word document. Website assets are built into `dist/`. All ten main figures and six explorer map pairs are generated with Matplotlib. The website and reports share one narrative in `scripts/publication_content.py`. Publication status and version come from `publication.json`.

## Data and interpretation

Distances use **EPSG:26916, NAD83 / UTM zone 16N, metres**. Annual maps use straight-line distance; event comparisons use a fixed 1 January 2023 OpenStreetMap network. Driving includes a directed return route. A 1.6 km catchment and 300 m maximum connector define the main comparisons.

SNAP dates are program eligibility dates, not physical openings or closures. Physical dates override only the reviewed focal events. Other destinations retain administrative eligibility. Census tract weights describe population context, not affected shoppers. Emissions are conditional scenarios with assumed trips and car shares. Spatial DiD, RDD and IV are discussed only where their identifying assumptions can be evaluated; no causal regression is invented in the absence of a valid mobility panel.

## Restricted inputs and publication

Institutional access to Advan Weekly Patterns Plus has been verified. Provider terms await the account holder's review before download. Store-week data and any provider source files belong in `data/restricted/`, which is excluded from version control and downloadable packages. License permissions must be reviewed before publishing derived mobility outputs. The public release contains only redistributable inputs and analytical outputs.

Original code: MIT. Public source files retain their respective terms. Street graphs derive from © OpenStreetMap contributors under ODbL 1.0, distributed by Geofabrik. See [data sources and checksums](data/source_manifest.json) and [network provenance](data/network_manifest.json).

See [data attribution and redistribution](docs/data_licenses.md), including the City of Chicago data notice. Adapted OpenStreetMap databases are distributed under ODbL 1.0.
