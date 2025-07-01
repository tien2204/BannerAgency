# BannerAgency: Advertising Banner Design with Multimodal LLM Agents

An autonomous agent system for editable banner ad image generation empowered by multiple multimodal LLMs.

<img src='assets/teaser.png' width='100%' />

<br>
<a href="https://arxiv.org/pdf/2503.11060"><img src="https://img.shields.io/static/v1?label=Paper&message=2503.11060&color=red&logo=arxiv"></a>
<a href="https://banneragency.github.io/"><img src="https://img.shields.io/static/v1?label=Project%20Page&message=Github.io&color=blue&logo=github-pages"></a>



**BannerAgency: Advertising Banner Design with Multimodal LLM Agents**

Authors: [Heng Wang](https://scholar.google.com.au/citations?user=jPj4ViQAAAAJ&hl=en), [Yotaro Shimose](https://github.com/yotaro-shimose), and [Shingo Takamatsu](https://scholar.google.co.jp/citations?user=oCVG8wQAAAAJ&hl=en) from Sony Group Corporation

## Installation

```bash
# Clone the repository
conda create -n baenv python=3.10
pip install -r requirements.txt
```

Please specify your API keys by copying `.env.example` to `.env`.

## Scheduled Releases
July 1, 2025
- [x] BannerRequest400 dataset release.
- [x] Evaluation code release.

## BannerRequest400 Benchmark
### Logo images
The 100 logos were generated semi-automatically with the assistance of [Claude-3.5 Sonnet](https://www.anthropic.com/news/claude-3-5-sonnet). We manualy checked the content to ensure quality. We release both the rendered `.png` format (`BannerRequest400/logos_png`) and the raw `.svg` format (`BannerRequest400/logos_svg`) to suit custom needs.

### Banner requests
Accompanying the 100 logo images are 400 abstract banner requests (`BannerRequest400/abstract_400.jsonl`) with four different target-purpose pairs for each logo. The abstract banner requests are derived from the [DESIGNERINTENTION](https://docs.google.com/spreadsheets/d/1e1-xFgPg_gzwy61xvsmtCpI_YjT8ofrYr9SqfthxgYg/edit?gid=0#gid=0) proposed in COLE [1]. We use [GPT-4o](https://openai.com/index/hello-gpt-4o/) for the target-purpose pair creation.

We also extend the 400 abstract banner requests to 5200 concrete requests across 13 standard banner dimensions with detailed banner specifications (`BannerRequest400/concrete_5k.jsonl`) via GPT-4o.

[1] Jia, Peidong, et al. "COLE: A Hierarchical Generation Framework for Multi-Layered and Editable Graphic Design." arXiv preprint arXiv:2311.16974 (2023).

## Evaluation
```bash
python3 eval.py --logo_file --image_file --banner_request 
```

## Citation
If you find our work helpful in your research, please kindly cite our paper via:
```bibtex
@article{wang2025banneragency,
  title     = {BannerAgency: Advertising Banner Design with Multimodal LLM Agents},
  author    = {Wang, Heng and Shimose, Yotaro and Takamatsu, Shingo},
  url = {arxiv},
  year      = {2025},
}
```

## Contact
If you have any questions or suggestions about this repo, please feel free to contact me! ([heng.wang@sony.com](heng.wang@sony.com))