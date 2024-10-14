# BioKGBench
A Knowledge Graph Checking Benchmark of AI Agent for Biomedical Science.
<p align="left">
<a href="https://github.com/westlake-autolab/Agent4S-BioKG/blob/main/LICENSE" alt="license">
    <img src="https://img.shields.io/badge/license-MIT-blue" /></a>
<!-- <a href="https://github.com/A4Bio/OpenCPD/issues" alt="resolution">
    <img src="https://img.shields.io/badge/issue%20resolution-1%20d-%23B7A800" /></a> -->
</p>

## 👋 Introduction
[[Paper](https://arxiv.org/abs/2407.00466)]
[[Project Page](https://westlake-autolab.github.io/biokgbench.github.io/)]
[[HuggingFace](https://huggingface.co/datasets/AutoLab-Westlake/BioKGBench-Dataset)]

Pursuing artificial intelligence for biomedical science, a.k.a. AI Scientist, draws increasing attention, where one common approach is to build a copilot agent driven by Large Language Models (LLMs).   
However, to evaluate such systems, people either rely on direct Question-Answering (QA) to the LLM itself, or in a biomedical experimental manner. How to precisely benchmark biomedical agents from an AI Scientist perspective remains largely unexplored. To this end, we draw inspiration from one most important abilities of scientists, understanding the literature, and introduce `BioKGBench`.   
In contrast to traditional evaluation benchmark that only focuses on factual QA, where the LLMs are known to have hallucination issues, we first disentangle **Understanding Literature** into two atomic abilities, i) **Understanding** the unstructured text from research papers by performing scientific claim verification, and ii) Ability to interact with structured Knowledge-Graph Question-Answering (KGQA) as a form of **Literature** grounding. We then formulate a novel agent task, dubbed KGCheck, using KGQA and domain-based Retrieval-Augmented Generation (RAG) to identify the factual errors of existing large-scale knowledge graph databases.   We collect over two thousand data for two atomic tasks and 225 high-quality annotated data for the agent task. Surprisingly, we discover that state-of-the-art agents, both daily scenarios and biomedical ones, have either failed or inferior performance on our benchmark. We then introduce a simple yet effective baseline, dubbed `BKGAgent`. On the widely used popular dataset, we discover over 90 factual errors which yield the effectiveness of our approach, yields substantial value for both the research community or practitioners in the biomedical domain.

## 🎯 Code Structure
```
BioKGBench
|-- assets
|   `-- img
|-- config
|   |-- kg_config.yml                               # config for build kg and connect to neo4j
|   `-- llm_config.yml                              # config for llm
|-- data
|   |-- bioKG                                       # dataset for build kg
|   |-- kgcheck                                     # dataset for KGCheck experiment
|   |-- kgqa                                        # dataset for KGQA experiment
|   `-- scv                                         # dataset for SCV experiment
`-- tasks
    |-- KGCheck                                     # KGCheck task
    |-- KGQA                                        # KGQA task
    |-- SCV                                         # SCV task
    `-- utils
        |-- agent_fucs                              # agent functions
        |-- embedding                               # embedding model starter for scv task
        |-- kg                                      # kg builder and kg connecotr
        |-- constant_.py                            # constant variables
        `-- threadpool_concurrency_.py              # threadpool concurrency method
```

## 👀 Overview
<details open>
<summary>Dataset(Need to <a href="https://huggingface.co/datasets/AutoLab-Westlake/BioKGBench-Dataset">download</a> from huggingface)</summary>

* **bioKG**: The knowledge graph used in the dataset.
* **KGCheck**: Given a knowledge graph and a scientific claim, the agent needs to check whether the claim is supported by the knowledge graph. The agent can interact with the knowledge graph by asking questions and receiving answers.
  * **Dev**: 20 samples
  * **Test**: 205 samples
  * **corpus**: 51 samples
* **KGQA**: Given a knowledge graph and a question, the agent needs to answer the question based on the knowledge graph.
  * **Dev**: 60 samples
  * **Test**: 638 samples
* **SCV**: Given a scientific claim and a research paper, the agent needs to check whether the claim is supported by the research paper.
  * **Dev**: 120 samples
  * **Test**: 1265 samples
  * **corpus**: 5664 samples

</details>

<details open>
<summary>Tasks</summary>

* **KGCheck**: Given a knowledge graph and a scientific claim, the agent needs to check whether the claim is supported by the knowledge graph. The agent can interact with the knowledge graph by asking questions and receiving answers.

* **KGQA**: Given a knowledge graph and a question, the agent needs to answer the question based on the knowledge graph.
* **SCV**: Given a scientific claim and a research paper, the agent needs to check whether the claim is supported by the research paper.

</details>

<details open>
<summary>Evaluation</summary>

* **Atomic Abilities (KGQA & SCV)**
![atomic evaluation](/assets/img/atomic_evaluation.png "atomic evaluation")

* **KGCheck - BKGAgent**
![kgcheck evaluation](/assets/img/kgcheck_evaluation.png "kgcheck evaluation")

</details>


## 📰 News and Updates
[2024-06-06] `BioKGBench` v0.1.0 is released.

## ⬇️ Installation
* This project has provided an environment setting file of conda, users can easily reproduce the environment by the following commands:
  ```bash
  conda create -n agent4s-biokg python=3.10
  conda activate agent4s-biokg
  pip install -r requirements.txt
  ```
* Important Note about KG
  * Building this knowledge graph (KG) locally requires at least 26GB of disk space.
  * We provide the TSV files for constructing the KG in the `data/bioKG` directory. These files are parsed from the following databases. The databases have their own licenses, and the use of the KG and data files still requires compliance with these data use restrictions. Please, visit the data sources directly for more information:

  | Source type             | Source                              | URL                                                   | Reference                               |
  |-------------------------|-------------------------------------|-------------------------------------------------------|------------------------------------------|
  | Database                | UniProt                             | [https://www.uniprot.org/](https://www.uniprot.org/)   | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/29425356) |
  | Database                | TISSUES                             | [https://tissues.jensenlab.org/](https://tissues.jensenlab.org/) | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/29617745) |
  | Database                | STRING                              | [https://string-db.org/](https://string-db.org/)       | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/30476243) |
  | Database                | SMPDB                               | [https://smpdb.ca/](https://smpdb.ca/)                 | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/24203708) |
  | Database                | SIGNOR                              | [https://signor.uniroma2.it/](https://signor.uniroma2.it/) | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/31665520) |
  | Database                | Reactome                            | [https://reactome.org/](https://reactome.org/)         | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/31691815) |
  | Database                | Intact                              | [https://www.ebi.ac.uk/intact/](https://www.ebi.ac.uk/intact/) | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/24234451) |
  | Database                | HGNC                                | [https://www.genenames.org/](https://www.genenames.org/) | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/30304474) |
  | Database                | DisGeNET                            | [https://www.disgenet.org/](https://www.disgenet.org/) | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/25877637) |
  | Database                | DISEASES                            | [https://diseases.jensenlab.org/](https://diseases.jensenlab.org/) | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/25484339) |
  | Ontology                | Disease Ontology                    | [https://disease-ontology.org/](https://disease-ontology.org/) | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/30407550) |
  | Ontology                | Brenda Tissue Ontology              | [https://www.brenda-enzymes.org/ontology.php?ontology_id=3](https://www.brenda-enzymes.org/ontology.php?ontology_id=3) | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/25378310) |
  | Ontology                | Gene Ontology                       | [http://geneontology.org/](http://geneontology.org/)   | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/27899567) |
  | Ontology                | Protein Modification Ontology       | [https://www.ebi.ac.uk/ols/ontologies/mod](https://www.ebi.ac.uk/ols/ontologies/mod) | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/23482073) |
  | Ontology                | Molecular Interactions Ontology     | [https://www.ebi.ac.uk/ols/ontologies/mi](https://www.ebi.ac.uk/ols/ontologies/mi) | [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/23482073) |



## 🚀 Getting Started

**Obtaining dataset**:
The dataset can be found in the [release]. The dataset is divided into three parts: `KGCheck`, `KGQA`, and `SCV`, every part is split into `Dev` and `Test`.
[[🤗 BioKGBench-Dataset](https://huggingface.co/datasets/AutoLab-Westlake/BioKGBench-Dataset)]
```git
git lfs install
GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/datasets/AutoLab-Westlake/BioKGBench-Dataset ./data
cd data
git lfs pull
```

**Building Knowledge Graph**: 
* Start neo4j  
By default, we download the data to the `data/bioKG` folder, and start neo4j using docker.
  ```bash
  docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -v $PWD/data/bioKG:/var/lib/neo4j/import neo4j:4.2.3
  ```

* Config  
You need to modify the configuration file `kg_config.yml` in the `config` folder. 

  ```bash
  python -m tasks.utils.kg.graphdb_builder.builder
  ```

**Running Baseline**:
* Config  
You need to modify the configuration file `llm_config.yml` in the `config` folder.

* `KGCheck`:  
  run experiment  
  **--data_file**: the path of the dataset file.
  ```bash
  python -m tasks.KGCheck.agents --data_file data/kgcheck/dev.json
  ```
  evaluate  
  **--history_file**: the path of the log file.  
  **--golden_answer_file**: the path of the golden answer file.
  ```bash
  python -m tasks.KGCheck.evalutation.evaluate --history_file results/kgcheck/log_1718880808.620556.txt --golden_answer_file data/kgcheck/dev.json
  ```
* `KGQA`:   
  In this section, we reference the evaluation framework of AgentBench.

  First, modify the configuration files under `tasks/KGQA/configs`:
  1. You can modify the data path in the `tasks/KGQA/configs/tasks/kg.yaml` file. The default path is `data/kgqa/test.json`.
  2. In the configuration files under `tasks/KGQA/configs/agents`, configure your agent. We have provided template configuration files for the OpenAI model, ChatGLM, and locally deployed models using vLLM. Please fill in the corresponding API Key for API-based LLMs or the address of your locally deployed model for OSS LLMs.
  3. Fill in the corresponding IP and port in `tasks/KGQA/configs/assignments/definition.yaml`, and modify the task configuration in `tasks/KGQA/configs/assignments/default.yaml`. By default, `gpt-3.5-turbo-0613` will be evaluated.

  Then start the task server. Make sure the ports you use are available.
  ```bash
  python -m tasks.KGQA.start_task -a
  ```
  If the terminal shows ".... 200 OK", you can open another terminal and start the assigner:
  ```bash
  python -m tasks.KGQA.assigner
  ```
* `SCV`:  
  start embedding api server:
  ```bash
  python -m tasks.SCV.embedding.webapi
  ```
  start SCV task:
  ```bash
  python -m tasks.SCV.scv_lc -d data/scv/dev.jsonl
  ```
  analysis:  
  ```bash
  python -m tasks.SCV.analysis -r results/svc/dev_1718903779.497523_answer_Qwen1.5-72B-Chat.jsonl
  ```

## 🙏 Acknowledgement

`BioKGBench` is an open-source project for Agent evaluation created by researchers in **AutoLab** and **CAIRI Lab** from Westlake University. We encourage researchers interested in LLM Agent and other related fields to contribute to this project!

## ✍️ Citation
If you find our work helpful, please use the following citations.
```
@misc{lin2024biokgbenchknowledgegraphchecking,
      title={BioKGBench: A Knowledge Graph Checking Benchmark of AI Agent for Biomedical Science}, 
      author={Xinna Lin and Siqi Ma and Junjie Shan and Xiaojing Zhang and Shell Xu Hu and Tiannan Guo and Stan Z. Li and Kaicheng Yu},
      year={2024},
      eprint={2407.00466},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2407.00466}, 
}
```

## 📧 Contact
For adding new features, looking for helps, or reporting bugs associated with `BioKGBench`, please open a [GitHub issue](https://github.com/A4Bio/ProteinInvBench/issues) and [pull request](https://github.com/A4Bio/ProteinInvBench/pulls) with the tag `new features`, `help wanted`, or `enhancement`. Feel free to contact us through email if you have any questions.

- Xinna Lin(linxinna@westlake.edu.cn), Westlake University
- Siqi Ma(masiqi@westlake.edu.cn), Westlake University
- Junjie Shan(shanjunjie@westlake.edu.cn), Westlake University
- Xiaojing Zhang(zhangxiaojing@westlake.edu.cn), Westlake University

## 📋 TODO

1. Support pip installation
