# Agent4S-BioKG
A Knowledge Graph Checking Benchmark of AI Agent for Biomedical Science.
<p align="left">
<a href="https://github.com/westlake-autolab/Agent4S-BioKG/blob/main/LICENSE" alt="license">
    <img src="https://img.shields.io/badge/license-MIT-blue" /></a>
<!-- <a href="https://github.com/A4Bio/OpenCPD/issues" alt="resolution">
    <img src="https://img.shields.io/badge/issue%20resolution-1%20d-%23B7A800" /></a> -->
</p>

## Introduction
Pursuing artificial intelligence for biomedical science, a.k.a. AI Scientist, draws increasing attention, where one common approach is to build a copilot agent driven by Large Language Models~(LLMs).   
However, to evaluate such systems, people either rely on direct Question-Answering~(QA) to the LLM itself, or in a biomedical experimental manner. How to precisely benchmark biomedical agents from an AI Scientist perspective remains largely unexplored. To this end, we draw inspiration from one most important abilities of scientists, understanding the literature, and introduce `BioKGBench`.   
In contrast to traditional evaluation benchmark that only focuses on factual QA, where the LLMs are known to have hallucination issues, we first disentangle **Understanding Literature** into two atomic abilities, i) **Understanding** the unstructured text from research papers by performing scientific claim verification, and ii) Ability to interact with structured Knowledge-Graph Question-Answering~(KGQA) as a form of **Literature** grounding. We then formulate a novel agent task, dubbed KGCheck, using KGQA and domain-based Retrieval-Augmented Generation (RAG) to identify the factual errors of existing large-scale knowledge graph databases.   We collect over two thousand data for two atomic tasks and 225 high-quality annotated data for the agent task. Surprisingly, we discover that state-of-the-art agents, both daily scenarios and biomedical ones, have either failed or inferior performance on our benchmark. We then introduce a simple yet effective baseline, dubbed `BKGAgent`. On the widely used popular dataset, we discover over 90 factual errors which yield the effectiveness of our approach, yields substantial value for both the research community or practitioners in the biomedical domain.

## Overview
<details open>
<summary>Tasks</summary>

* **KGCheck**: Given a knowledge graph and a scientific claim, the agent needs to check whether the claim is supported by the knowledge graph. The agent can interact with the knowledge graph by asking questions and receiving answers.
* **KGQA**: Given a knowledge graph and a question, the agent needs to answer the question based on the knowledge graph.
* **SCV**: Given a scientific claim and a research paper, the agent needs to check whether the claim is supported by the research paper.

</details>

<details open>
<summary>Code Structure</summary>
</details>

<details open>
<summary>Baseline</summary>
</details>

<details open>
<summary>Dataset</summary>
</details>

## News and Updates
[2024-06-06] `BioKGBench` v0.1.0 is released.

## Installation
This project has provided an environment setting file of conda, users can easily reproduce the environment by the following commands:
```bash
conda create -n agent4s-biokg python=3.10
conda activate agent4s-biokg
pip install -r requirements.txt
```

## Getting Started

**Obtaining dataset**:
The dataset can be found in the [release]. The dataset is divided into three parts: `KGCheck`, `KGQA`, and `SCV`, every part is split into `Dev` and `Test`.

**Running Baseline**:

* `KGCheck`:
```bash
```
* `KGQA`:
```bash
```
* `SCV`:
```bash
```

## Acknowledgement

`BioKGBench` is an open-source project for Agent evaluation created by researchers in **Westlake Auto Lab** and **CAIRI Lab**. We encourage researchers interested in LLM Agent and other related fields to contribute to this project!

## Citation

## Contact
For adding new features, looking for helps, or reporting bugs associated with `BioKGBench`, please open a [GitHub issue](https://github.com/A4Bio/ProteinInvBench/issues) and [pull request](https://github.com/A4Bio/ProteinInvBench/pulls) with the tag `new features`, `help wanted`, or `enhancement`. Feel free to contact us through email if you have any questions.

- Xinna Lin(linxinna@westlake.edu.cn), Westlake University
- Siqi Ma(masiqi@westlake.edu.cn), Westlake University
- Junjie Shan(shanjunjie@westlake.edu.cn), Westlake University
- Xiaojing Zhang(zhangxiaojing@westlake.edu.cn), Westlake University

## TODO

1. Update dataset
2. Support pip installation