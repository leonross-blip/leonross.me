---
title: "Paper: GEARS — predicting transcriptional outcomes of novel multigene perturbations"
date: 2026-10-20
type: paper
summary: GEARS uses a gene-relationship graph to predict expression changes for unseen single and two-gene perturbations. The headline numbers are strong, but later benchmarks suggest simple baselines close much of the gap.
link: https://doi.org/10.1038/s41587-023-01905-6
tags: [perturbation, single-cell, graph-neural-networks]
obsidian_vault: research-notes
aliases: [gears]
---

## Claim

GEARS (Roohani, Huang & Leskovec, *Nature Biotechnology* 2023) claims to predict post-perturbation gene expression for perturbations never seen in training — including two-gene combinations where neither gene was perturbed during training — by combining Perturb-seq data with a knowledge graph of gene–gene relationships.

## What it actually shows

On Norman et al.'s combinatorial Perturb-seq data, GEARS beats the baselines the authors chose, and the ability to flag synergistic gene pairs is genuinely useful for designing combinatorial screens. But the evaluation metric (change in expression of the top differentially expressed genes) flatters any model that gets the big movers roughly right, and follow-up benchmarking work has repeatedly found that "predict the training-set mean shift" style baselines are much closer to GEARS than the paper implies. The honest reading: the knowledge graph helps generalise to unseen perturbations somewhat, which is the hard and interesting part, but absolute predictive accuracy is still far from replacing the experiment.

## Method in plain words

Instead of treating each gene as an arbitrary label, GEARS places genes in two graphs — one from co-expression, one from shared Gene Ontology annotations — so that perturbing a gene the model has never seen still means something: the model borrows information from that gene's neighbours. A graph neural network turns each perturbation into an embedding, combines it with a baseline cell state, and decodes the predicted expression change per gene. Combinations are handled by composing the embeddings of the individual perturbations, which is where the synergy predictions come from.

## What I'd do next

Re-run the evaluation with stronger baselines (mean-shift, linear models on perturbation embeddings) and metrics that score the full expression profile rather than top-20 DE genes, and test transfer across cell lines — the setting that actually matters for target discovery, and where graph-based priors should in principle shine or visibly break.

## Link

[Paper in Nature Biotechnology](https://doi.org/10.1038/s41587-023-01905-6)
