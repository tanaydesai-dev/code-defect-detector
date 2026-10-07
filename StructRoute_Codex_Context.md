# StructRoute: Codex Project Context

## How to Use This File

This is the source of truth for the StructRoute project. Read it before planning, coding, reviewing experiments, or changing the architecture.

When working on this project:

1. Inspect the repository and the **Current Status** section before taking action.
2. Continue from the earliest unfinished milestone. Do not restart completed work.
3. Keep changes small, understandable, and testable.
4. Explain unfamiliar ML ideas in plain language. The project lead is comfortable with Python and CS fundamentals but is still developing an ML background.
5. Preserve the central comparison: syntax-aware routing versus the same architecture without syntax.
6. Do not introduce hosted LLM API calls. Open model weights may be downloaded and run locally.
7. Do not claim that an architecture improves performance until it has been compared on the same data split and preprocessing pipeline.
8. Do not claim that the idea is completely novel without a current literature search.
9. At the end of a substantial session, update **Current Status**, **Important Decisions**, and **Experiment Log** in this file.

---

## Current Status

**Project phase:** Milestone 1 in progress; the repository scaffold and dataset-inspection pipeline are implemented.

**Completed:**

- Project idea selected
- Core research question defined
- MVP architecture outlined
- Dataset, model, parser, evaluation metrics, budget, and ten-week schedule proposed
- Initial Python package, environment metadata, baseline configuration, and data documentation created
- CodeXGLUE loader and dataset-inspection CLI implemented with schema validation, split statistics, duplicate checks, optional CodeBERT token lengths, and sampled examples
- Dependency-free dataset utility checks pass locally

**Next milestone:** Run and record the full CodeXGLUE inspection, then implement and train the frozen-CodeBERT classifier baseline.

**Immediate next actions:**

- [x] Inspect the existing repository, if one exists.
- [x] Create the initial project structure and Python environment metadata.
- [x] Add a script that downloads or loads the selected dataset.
- [ ] Produce dataset statistics and inspect example functions.
- [ ] Tokenize examples with `microsoft/codebert-base`.
- [ ] Train a small baseline on 50 to 100 examples and verify that it can overfit them.
- [ ] Record the first baseline configuration and metrics.

Do not start the full Mixture-of-Experts implementation until the baseline and syntax-alignment pipelines work independently.

---

## Project Identity

**Name:** StructRoute

**Full title:** Syntax-Routed Mixture-of-Experts for Code Analysis

**One-line explanation:** StructRoute teaches a code model to send different parts of a program to different neural specialists based on their syntactic role.

**Initial application:** Binary function-level defect or vulnerability detection in C code.

**Project duration:** Ten weeks.

**Compute budget:** Approximately $50 to $100, with free or university resources used whenever possible.

---

## Simple Mental Model

Think of StructRoute as a team of specialists.

- CodeBERT reads a function and creates a numerical representation for every token.
- Tree-sitter identifies what each token does, such as being part of a condition, function call, assignment, loop, or return statement.
- A router looks at both the CodeBERT representation and the syntax label.
- The router chooses one small neural-network expert for each token.
- The processed token representations are combined to predict whether the function contains a defect or vulnerability.

For this code:

```c
if (count > limit) {
    return count;
}
```

Tree-sitter may identify `if` as a branch, `>` as a comparison, `count` and `limit` as identifiers, and `return` as a return statement. The router may learn to send these roles to different experts. The experts are not manually assigned jobs. Their specializations must emerge from training and must be verified through analysis.

---

## Motivation

Code transformers usually process source code as a token sequence. They can learn syntax indirectly, but they are not explicitly told what role each token plays in the program.

The same identifier may appear in a loop condition, function call, assignment, or return statement. These uses have different meanings even when the token text is similar. StructRoute tests whether explicit syntax can help a model decide which trainable computation is most useful for each token.

The project is designed to teach the team about:

- Transformers and contextual token representations
- Abstract Syntax Trees and static analysis
- Mixture-of-Experts models
- Adapter-based parameter-efficient training
- Sparse routing and load balancing
- Robustness under safe code transformations
- Baselines, ablations, and controlled ML experiments
- Model interpretation through routing analysis

---

## Core Research Question

**Does adding explicit token-level syntax information to a Mixture-of-Experts router improve defect detection, cross-project generalization, routing stability, or expert specialization compared with an otherwise identical router that only sees contextual token representations?**

This comparison is the center of the project. A model that uses syntax must be compared with a model that has the same encoder, experts, training data, and evaluation procedure but does not receive syntax labels.

### Working hypothesis

Syntax-aware routing may help because the router receives a useful structural clue about each token. It may produce better generalization, more stable behavior after harmless code changes, or clearer expert specialization. Higher average accuracy is one possible result, but it is not the only meaningful result.

---

## Fixed MVP Decisions

Use these decisions for the first complete implementation unless real evidence requires a change:

- **Language:** C
- **Primary task:** Binary function-level defect or vulnerability detection
- **Primary dataset:** CodeXGLUE defect-detection dataset
- **Base encoder:** `microsoft/codebert-base`
- **Syntax parser:** Tree-sitter with a C grammar
- **Framework:** Python, PyTorch, Hugging Face Transformers, and Hugging Face Datasets
- **Initial expert count:** Four experts per Mixture-of-Adapters module
- **Adapter bottleneck:** Start with 64 dimensions
- **Syntax embedding:** Start with approximately 32 dimensions
- **Final routing target:** Sparse top-1 token routing
- **Training strategy:** Freeze CodeBERT initially; train adapters, routers, syntax embeddings, and the classifier
- **Primary metrics:** F1 and Matthews Correlation Coefficient
- **Secondary metrics:** Precision, recall, AUROC, confusion matrix, memory, throughput, and latency
- **Hosted model APIs:** None

Before publishing results, verify the dataset's current documentation, license, exact number of examples, source, and label meaning. Describe the labels accurately; they should not automatically be presented as covering every kind of software bug.

---

## End-to-End System

```text
C function
   |
   +--> CodeBERT tokenizer --> token IDs and offset spans
   |
   +--> Tree-sitter parser --> AST nodes and syntax categories
                               |
                token-to-AST alignment
                               |
             syntax category for each token
                               |
CodeBERT encoder --> contextual token representations
                               |
        token representation + syntax embedding
                               |
                      learned router
                               |
                 selected adapter expert
                               |
                  updated token representation
                               |
                    classification head
                               |
             defective / non-defective probability
```

---

## Data Pipeline

### Primary dataset

Begin with the CodeXGLUE defect-detection dataset. Each example should contain a C function and a binary label.

### Required data checks

- Count training, validation, and test examples.
- Measure class balance.
- Inspect random positive and negative examples.
- Measure function length in characters and CodeBERT tokens.
- Count examples longer than the model's maximum sequence length.
- Detect exact duplicate functions across splits.
- Check near duplicates using normalized code when practical.
- Preserve repository or project metadata when available.
- Record every discarded or failed example.

### Processed example format

Each cached example should eventually contain:

```text
example_id
source_code
input_ids
attention_mask
syntax_ids
label
project_or_repository_id, when available
transformation_metadata, when applicable
```

Use the official split for benchmark comparability. Add project-disjoint or repository-disjoint evaluation when metadata allows it.

---

## Syntax Pipeline

### Tree-sitter parsing

Parse each original function with Tree-sitter. Convert detailed Tree-sitter node types into a smaller, interpretable syntax vocabulary.

Recommended initial categories:

- Special token
- Padding
- Unknown or other
- Identifier
- Function name
- Function call
- Parameter or argument
- Declaration
- Assignment
- Arithmetic expression
- Comparison
- Branch condition
- Loop
- Return statement
- Literal
- Operator
- Pointer operation
- Array access
- Type

Store the mapping in a configuration file such as `configs/syntax_categories.yaml`. Do not scatter hard-coded mappings across the codebase.

### Token-to-AST alignment

Tree-sitter and CodeBERT do not necessarily divide code in the same way. For example, Tree-sitter may treat `current_count` as one identifier while the tokenizer splits it into several subwords.

The alignment process should:

1. Parse the original UTF-8 source.
2. Obtain CodeBERT token offset mappings.
3. Handle Tree-sitter byte positions and tokenizer character positions correctly.
4. Find the deepest useful AST node covering each token span.
5. Convert that node into a broad syntax category.
6. Give every subword of a source token the appropriate syntax category.
7. Assign explicit IDs to special and padding tokens.

### Required alignment tests

- Simple declarations and assignments
- Multi-subword identifiers
- Conditions and loops
- Function calls and arguments
- Pointer and array operations
- Comments and whitespace
- Empty functions
- Parser-error examples
- Non-ASCII text or a documented decision to reject it
- Padding and special tokens

Also build a small inspection command that prints tokens beside their syntax labels. Manually review examples before using syntax labels in training.

---

## Baseline Model

The first trained model is:

```text
CodeBERT tokenizer
    -> frozen CodeBERT encoder
    -> classification-token representation
    -> dropout
    -> linear classifier
    -> binary prediction
```

The baseline has three purposes:

1. Verify that the dataset and labels are usable.
2. Verify that the training and evaluation code works.
3. Create the reference result that later architectures must beat or explain.

Before a full run, train on 50 to 100 examples and confirm that the model can overfit the small set. If it cannot, debug the pipeline before continuing.

---

## Adapter Experts

An adapter is a small neural network placed inside or after a transformer layer. The initial expert architecture is:

```text
LayerNorm
    -> Linear(768, 64)
    -> GELU
    -> Dropout
    -> Linear(64, 768)
    -> residual addition to the original token representation
```

Use four independent experts in each Mixture-of-Adapters module.

### Safe implementation sequence

1. Implement one adapter after the final encoder layer.
2. Confirm its tensor shapes, gradients, and ability to overfit a tiny batch.
3. Replace it with four experts and a dense soft router.
4. Add syntax to the router.
5. Implement sparse top-1 dispatch.
6. Add modules after layers 4, 8, and 12 if compute and integration remain manageable.

Starting with one insertion point makes debugging much easier. The planned final architecture may use layers 4, 8, and 12, counted from 1.

---

## Router

For token `i`:

- `h_i` is the token's contextual CodeBERT representation.
- `syntax_id_i` is its syntax-category ID.
- `e_i` is the learned embedding of that syntax ID.

The syntax-aware router is conceptually:

```text
normalized_h_i = LayerNorm(h_i)
router_input_i = concatenate(normalized_h_i, e_i)
router_logits_i = MLP(router_input_i)
router_probabilities_i = softmax(router_logits_i)
selected_expert_i = argmax(router_probabilities_i)
```

### Dense debugging version

Run all experts for every token and calculate a weighted sum using the router probabilities. This is computationally inefficient but easy to verify.

### Sparse top-1 version

For each expert:

1. Find the non-padding tokens assigned to it.
2. Gather those token vectors.
3. Process them with that expert.
4. Scatter the outputs back to their original batch and sequence positions.
5. Add the expert output through a residual connection.

All valid tokens should be processed. The first single-GPU implementation does not require distributed expert parallelism, fixed expert capacity, or token dropping.

---

## Training Objectives

The complete objective is:

```text
total_loss = classification_loss
           + lambda_balance * load_balancing_loss
           + lambda_consistency * consistency_loss
```

### Classification loss

Use binary cross-entropy with logits or two-class cross-entropy. Apply class weighting only if data analysis supports it.

### Load-balancing loss

The router may collapse and send nearly every token to one expert. The balancing loss should encourage meaningful use of all experts by considering:

- Average probability assigned to each expert
- Fraction of valid tokens actually routed to each expert

Exclude padding tokens from routing statistics and losses. Log expert utilization every epoch.

### Consistency loss

Create safe variants of the same function through transformations such as:

- AST-aware local-variable renaming
- Whitespace reformatting
- Comment changes when comments are retained

Begin with prediction consistency between the original and transformed function. Use symmetric KL divergence or Jensen-Shannon divergence between their output distributions.

For routing consistency, first compare routing distributions aggregated by syntax category. Exact subword-to-subword matching can be added after reliable transformation maps exist.

Avoid complicated rewrites such as replacing a `for` loop with a `while` loop until transformation correctness can be established.

---

## Experiment Matrix

Run these models using the same data, splits, preprocessing, and evaluation code:

### Required models

1. **Baseline:** Frozen CodeBERT plus classifier
2. **Dense adapter:** Frozen CodeBERT plus one regular adapter
3. **Syntax-unaware MoE:** Router sees contextual token representations only
4. **StructRoute:** Router sees contextual representations and syntax embeddings
5. **StructRoute plus consistency:** Full model with safe transformation training

### Required ablations

- Real syntax labels versus shuffled syntax labels
- Context-only router versus syntax-aware router
- With and without load-balancing loss
- With and without consistency loss

### Optional ablations

- One, two, four, and eight experts
- Top-1 versus top-2 routing
- Different insertion layers
- Broad syntax categories versus raw Tree-sitter types
- Frozen encoder versus unfreezing the final one or two layers

The context-only and syntax-aware routers must otherwise be identical. This is the cleanest test of the core idea.

---

## Evaluation

### Prediction quality

Report:

- Precision
- Recall
- F1 score
- Matthews Correlation Coefficient
- AUROC when appropriate
- Confusion matrix

Do not rely on accuracy alone.

### Generalization

- Official held-out test split
- Project-disjoint or repository-disjoint split when possible
- Results on safely transformed versions of the same code

### Efficiency

- Total parameters
- Trainable parameters
- Active expert parameters per token
- Peak GPU memory
- Training time per epoch
- Inference throughput
- Median and high-percentile latency

Sparse routing does not automatically make wall-clock inference faster. Gather and scatter operations may add overhead, so measure actual runtime.

### Routing behavior

- Fraction of tokens sent to each expert
- Router entropy
- Expert utilization by layer
- Syntax-category distribution for each expert
- Relationship between syntax roles and expert choices
- Routing stability after variable renaming and formatting
- Examples with tokens colored by selected expert

Do not name an expert a “condition expert” or “memory expert” based on a few examples. Specialization claims need aggregate evidence.

### Experimental fairness

- Use identical splits across models.
- Keep preprocessing fixed.
- Save all configurations.
- Use fixed random seeds during development.
- Run the final configurations with three seeds if compute permits.
- Report mean and standard deviation.
- Record failed runs and negative results.

---

## Repository Structure

```text
structroute/
├── README.md
├── pyproject.toml
├── .gitignore
├── configs/
│   ├── baseline.yaml
│   ├── dense_adapter.yaml
│   ├── moe.yaml
│   ├── structroute.yaml
│   └── syntax_categories.yaml
├── data/
│   └── README.md
├── scripts/
│   ├── inspect_data.py
│   ├── preprocess.py
│   ├── train.py
│   ├── evaluate.py
│   ├── inspect_alignment.py
│   └── analyze_routing.py
├── src/structroute/
│   ├── data/
│   │   ├── dataset.py
│   │   ├── parser.py
│   │   ├── syntax_mapping.py
│   │   ├── token_alignment.py
│   │   └── transformations.py
│   ├── models/
│   │   ├── baseline.py
│   │   ├── adapter.py
│   │   ├── router.py
│   │   ├── sparse_moe.py
│   │   └── structroute_model.py
│   ├── training/
│   │   ├── losses.py
│   │   ├── trainer.py
│   │   └── metrics.py
│   └── analysis/
│       ├── specialization.py
│       ├── robustness.py
│       └── efficiency.py
├── tests/
│   ├── test_alignment.py
│   ├── test_adapter.py
│   ├── test_router.py
│   ├── test_sparse_dispatch.py
│   └── test_transformations.py
├── notebooks/
└── reports/
    ├── figures/
    └── results/
```

Use notebooks for exploration. Keep final preprocessing, training, evaluation, and analysis in scripts or importable modules.

---

## Development Milestones and Gates

### Milestone 1: Data and baseline

**Build:** Dataset loader, exploration script, tokenizer pipeline, frozen-CodeBERT classifier.

**Gate:** The model can overfit a small batch, a full evaluation run completes, and metrics are saved reproducibly.

### Milestone 2: Syntax alignment

**Build:** Tree-sitter parser, syntax mapping, token alignment, cached syntax IDs, inspection command.

**Gate:** Unit tests pass and manually reviewed examples show correct token labels.

### Milestone 3: Adapter baseline

**Build:** One bottleneck adapter with a residual connection.

**Gate:** Tensor shapes and gradients are correct, and the model can overfit a small batch.

### Milestone 4: Syntax-unaware MoE

**Build:** Four experts, router, dense routing, then sparse top-1 routing.

**Gate:** Dense and sparse implementations have matching outputs within tolerance when configured equivalently, and every expert receives gradients or assigned tokens.

### Milestone 5: StructRoute

**Build:** Syntax embeddings and syntax-conditioned router.

**Gate:** Syntax IDs reach every routing layer, padding is excluded, utilization is logged, and training is stable.

### Milestone 6: Robustness and analysis

**Build:** Safe transformations, consistency loss, routing analysis, efficiency measurements.

**Gate:** Required baselines and ablations run on identical splits and produce a complete results table.

---

## Ten-Week Plan

### Week 1

Repository setup, environment, dataset loading, dataset inspection, and evaluation plan.

### Week 2

Frozen-CodeBERT classifier baseline and reproducible baseline metrics.

### Week 3

Tree-sitter parsing, syntax categories, and token-to-AST alignment.

### Week 4

Single dense adapter baseline.

### Week 5

Syntax-unaware Mixture-of-Adapters and routing diagnostics.

### Week 6

Syntax embeddings and the complete StructRoute architecture.

### Week 7

Load balancing, safe transformations, and consistency training.

### Week 8

Main baselines, ablations, and limited hyperparameter tuning.

### Week 9

Cross-project evaluation, efficiency measurements, and expert analysis.

### Week 10

Clean reproduction, final README, report, figures, and demonstration.

The complete architecture should run by the end of Week 6. Weeks 7 through 10 are for testing its value and presenting credible evidence.

---

## Team Workstreams

Divide the team into these workstreams and combine roles if the team is small.

### Data and syntax

- Dataset preparation
- Tree-sitter parsing
- Syntax-category mapping
- Token alignment
- Safe transformations

### Model architecture

- Adapter experts
- Router
- Dense and sparse dispatch
- CodeBERT integration

### Training and evaluation

- Training loop
- Metrics and checkpointing
- Baselines and ablations
- Generalization experiments

### Analysis and infrastructure

- Routing visualizations
- Efficiency measurements
- Experiment tracking
- Documentation and final demo

Every member should understand the overall data flow even if they own one component.

---

## Engineering Rules for Codex

- Inspect existing code before creating new files or architecture.
- Preserve user changes and avoid unrelated rewrites.
- Use configuration files for experiment settings.
- Keep data and checkpoints out of Git unless they are intentionally small fixtures.
- Use type hints and concise docstrings for non-obvious interfaces.
- Keep tensor shapes documented at routing boundaries.
- Validate masks and exclude padding from routing losses and statistics.
- Use small deterministic fixtures for alignment and dispatch tests.
- Include a command that reproduces every reported experiment.
- Record dependency versions and random seeds.
- Prefer clear single-GPU PyTorch code over premature distributed optimization.
- Explain each change, why it was needed, how it was validated, and what remains uncertain.
- Do not add features from the stretch list until the current milestone passes its gate.

---

## Resources

### Software

- Python
- PyTorch
- Hugging Face Transformers, Tokenizers, and Datasets
- Tree-sitter and a C grammar
- NumPy and pandas
- scikit-learn
- Matplotlib or Seaborn
- PyYAML
- Git and GitHub

### Compute

- Local CPU for parsing, preprocessing, and tests
- Free notebook or university GPU resources for development
- Rented 16 to 24 GB GPU for final experiments if necessary

### Budget

Target total spending is $50 to $100. Use paid GPU time for final comparisons and repeated-seed runs rather than early debugging.

---

## Main Risks

### Misaligned syntax labels

This would invalidate the central experiment. Test offsets carefully and inspect examples visually.

### Router collapse

One expert may receive most tokens. Track utilization and use a load-balancing regularizer.

### Data leakage

Duplicate or related functions may appear across splits. Use exact and normalized hashes and preserve project metadata.

### No accuracy improvement

The project can still produce a useful result if syntax improves routing stability, cross-project behavior, interpretability, or trainable-parameter efficiency. Report negative findings honestly.

### Sparse routing is slower

Sparse computation may add dispatch overhead. Measure real runtime before making efficiency claims.

### Excessive scope

Protect the baseline, syntax alignment, core comparison, and Week 6 architecture checkpoint. Treat extra datasets, languages, and line localization as later work.

---

## Relationship to Existing Work

Existing work already combines code structure, ASTs, graph representations, and Mixture-of-Experts models. Related directions include GraphCodeBERT-style structural representations and syntax-aware sparse MoE systems for software vulnerability detection.

StructRoute's proposed distinction is the combination of:

- Token-level syntax-conditioned routing
- Lightweight adapter experts attached to a mostly frozen encoder
- Direct comparison with a syntax-unaware router
- Consistency under safe code transformations
- Analysis of expert specialization and routing stability

This is a meaningful AI Club and portfolio project. Publication-level novelty would require an updated literature review, stronger experiments, and a clear new finding.

---

## Definition of Done

The project is complete when it has:

- A reproducible data pipeline
- Verified token-to-AST alignment
- A frozen-CodeBERT baseline
- A dense-adapter baseline
- A syntax-unaware Mixture-of-Adapters baseline
- A working syntax-aware StructRoute model
- Load-balancing diagnostics
- At least one safe transformation-based consistency experiment
- Controlled evaluation on identical splits
- Performance, generalization, and efficiency results
- Expert-utilization and specialization visualizations
- Saved configurations and important checkpoints
- A README that another student can follow
- A final report that includes limitations and unsuccessful experiments

Strong outcomes include improved F1 or MCC, better cross-project performance, more stable predictions after harmless changes, meaningful expert specialization, or competitive results with far fewer trainable parameters.

---

## Important Decisions

Record dated decisions here as the project develops.

- **Initial scope:** C function-level defect or vulnerability detection.
- **Initial dataset:** CodeXGLUE defect-detection data, subject to verification during Week 1.
- **Initial encoder:** `microsoft/codebert-base`.
- **Initial parser:** Tree-sitter C grammar.
- **Initial architecture:** Frozen encoder, four 64-dimensional bottleneck experts, 32-dimensional syntax embeddings, and top-1 routing.
- **Development path:** Baseline, syntax alignment, single adapter, context-only MoE, syntax-aware MoE, then consistency training.
- **Budget:** $50 to $100.
- **Hosted LLM APIs:** Excluded from the model pipeline.
- **2026-10-06 dataset access:** Use the Hugging Face Parquet dataset `google/code_x_glue_cc_defect_detection`; record the requested revision and loaded fingerprints in inspection reports.
- **2026-10-06 Python support:** Target Python 3.10 through 3.12; use Python 3.11 when creating the development environment.

---

## Experiment Log

Add one short entry for each meaningful run:

```text
Date:
Commit or code version:
Configuration:
Dataset split:
Random seed:
Trainable parameters:
Main metrics:
Routing statistics:
Runtime and hardware:
Result or lesson:
Next action:
```

```text
Date: 2026-10-06
Commit or code version: Initial uncommitted scaffold
Configuration: Dependency-free dataset utility smoke test
Dataset split: Two synthetic train and validation fixtures
Random seed: N/A
Trainable parameters: N/A
Main metrics: N/A
Routing statistics: N/A
Runtime and hardware: Local CPU, under one second
Result or lesson: Source normalization, label counts, and exact/cross-split duplicate checks passed; pytest and Ruff still require installing the development environment.
Next action: Create a Python 3.11 environment, install dependencies, and run the full CodeXGLUE inspection.
```

---

## First Instruction to Codex

When this context is first loaded, inspect the available repository. If the repository is empty, scaffold the structure required for **Milestone 1**, create the environment configuration, implement a dataset-inspection script, and document the exact commands to run it. Do not implement the experts or router during the same step. If a repository already exists, report which milestone is currently satisfied, identify the first unmet gate, and continue from there.
