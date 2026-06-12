"""addNewContent pipeline — shared, reusable core for The Machine's
content-ingestion pipeline.

Replaces the copy-pasted one-off scripts in moviesNstuff2024/ and
MeanGirlsFiles/ with one coherent package. Each stage script (01..05 in the
parent dir) imports from here instead of re-walking folders or re-pasting
clean_html / sub_time_to_ms / natural_key.

See addNewContent-pipeline-plan.md (repo root) for the full plan + status.
"""
