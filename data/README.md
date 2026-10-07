# Data

Dataset files and processed caches are intentionally excluded from Git.
StructRoute uses `google/code_x_glue_cc_defect_detection` from the Hugging Face
Hub for the initial benchmark. It contains C functions from Devign with the
official CodeXGLUE train, validation, and test splits.

The dataset card lists the C-UDA license. Review and comply with that agreement
before downloading or redistributing the data.

The inspection command uses the Hugging Face cache by default. If later stages
materialize project-specific files, put source downloads in `data/raw/` and
derived artifacts in `data/processed/`; both are ignored by Git.

