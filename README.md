# chor4o Recon Robot

Automate your bug bounty reconnaissance process with the Chor4o Recon Robot!

This Python script performs a complete workflow of subdomain and URL gathering, enumeration, and analysis using the main bug bounty recon tools, generating organized logs per domain.

---

## Main Features

- Subdomain and URL collection via **Chaos**, **Subfinder**, and **Gau**
- Deep crawling with **Katana**
- Advanced URL processing with **SlicePathsURL**
- Live host verification with **Httpx**
- Port scanning with **Naabu**
- Vulnerability analysis with **Nuclei**
- Automated XSS detection and exploitation using **gf** + **Dalfox**
- Separate, well-organized logs per domain in the `logs/` folder
- Simple terminal interface with a custom “chor4o” banner

---

## Requirements

- Linux (tested on CentOS, Ubuntu)
- Python 3.x
- Tools installed and in your PATH:
  - chaos - https://github.com/projectdiscovery/chaos-client
  - subfinder - https://github.com/projectdiscovery/subfinder
  - gau - https://github.com/lc/gau
  - katana - https://github.com/projectdiscovery/katana
  - slicepathsurl - https://github.com/erickfernandox/slicepathsurl
  - httpx - https://github.com/projectdiscovery/httpx
  - naabu - https://github.com/projectdiscovery/naabu
  - nuclei - https://github.com/projectdiscovery/nuclei
  - gf - https://github.com/tomnomnom/gf
  - dalfox - https://github.com/hahwul/dalfox

---

## Usage

The script accepts two mutually exclusive options:

- `-l <file>` : Provide a file containing a list of target domains, one per line.
- `-u <domain>` : Provide a single domain as a target.

Examples:

1. Running with a list of domains:

```bash
python robo.py -l domains.txt

By chor4o
