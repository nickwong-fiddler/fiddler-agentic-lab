# Lab Prerequisites — Offline Variant

Welcome! To make the most of our 60-minute hands-on Fiddler agentic monitoring lab, **please complete the setup below before the session.** We will not have time to debug environment issues during the lab.

> **About this variant:** this notebook (`Fiddler_Ecommerce_Agent_Offline.ipynb`) uses **pre-recorded LLM responses** bundled in `cassette.json`. No external LLM API access is required. You only need network access to the Fiddler sandbox URL provided by your instructor.

## Two ways to participate

Pick whichever you prefer:

| Option | Best for | Setup effort |
|---|---|---|
| **A. Run locally** with your own Python + Jupyter | Folks comfortable with Python tooling | ~5 min |
| **B. Run in Google Colab** (link provided by your instructor) | Everyone else — zero local setup | 0 min |

If you pick **Option B**, you can stop reading here. Just click the Colab link your instructor sends you on the day of the lab.

---

## Option A — Local setup

### Requirements

- Python **3.10 or newer** (`python --version`)
- A code editor with Jupyter notebook support (VS Code recommended, or classic Jupyter)
- ~500 MB free disk space for dependencies
- HTTPS access to the **Fiddler sandbox URL** provided by your instructor
  - **No** external LLM access required (the offline variant uses pre-recorded responses)

### Step 1 — Clone the lab repo

```bash
git clone https://github.com/nickwong-fiddler/fiddler-agentic-monitoring-lab.git
cd fiddler-agentic-monitoring-lab
```

Confirm the repo includes `cassette.json` (~20 KB) at the top level. The offline notebook reads its LLM responses from this file.

### Step 2 — Create a dedicated virtual environment

Pick **one** of the following:

#### Option 2a — `venv` (built-in, recommended)

```bash
python -m venv .venv-fiddler-lab

# Activate the venv
source .venv-fiddler-lab/bin/activate     # macOS / Linux
.venv-fiddler-lab\Scripts\activate        # Windows

# Register it as a Jupyter kernel
pip install ipykernel
python -m ipykernel install --user --name fiddler-lab \
    --display-name "Python (fiddler-lab)"
```

#### Option 2b — `conda`

```bash
conda create -n fiddler-lab python=3.11 ipykernel -y
conda activate fiddler-lab
python -m ipykernel install --user --name fiddler-lab \
    --display-name "Python (fiddler-lab)"
```

### Step 3 — Open the notebook and select the right kernel

Open `Fiddler_Ecommerce_Agent_Offline.ipynb` in your editor. In the top-right of the notebook, open the kernel picker and select **"Python (fiddler-lab)"**.

> ⚠️ **Critical — read this:** `%pip install` installs into whichever kernel is *currently selected*, NOT the venv you `source`'d in your terminal. If the wrong kernel is selected in step 3, the install cell may succeed but later imports will fail with confusing errors. This is the #1 cause of "it doesn't work" during labs.

### Step 4 — Verify

Run the first three cells of the notebook (the `%pip install` cell, the LLM config cell, and the dataset cell). If all three complete without errors, you're ready for the lab.

---

## Option B — Google Colab

Your instructor will share a Colab link on the day of the lab. Colab provides Python and an isolated runtime per notebook — nothing to install in advance.

> **Note for Colab:** the offline variant requires `cassette.json` to be uploaded alongside the notebook. The Colab link your instructor shares will already include it.

---

## What you'll need on the day of the lab

Your instructor will provide:

- A Fiddler sandbox URL

You will create your own (during the lab, ~7 min total):

- Fiddler GenAI Application (walkthrough in § 1 of the notebook)
- Fiddler API access key (walkthrough in § 1 of the notebook)

That's it. **No LLM API key is required for the offline variant.**

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `%pip install` succeeds but `import pandas` fails | Wrong kernel selected | Re-do Step 3 — make sure "Python (fiddler-lab)" is the active kernel |
| `FileNotFoundError: cassette.json` | Cassette not in the same directory as the notebook | Confirm `cassette.json` exists in the working directory; re-clone the repo if missing |
| `RuntimeError: No recorded response for fingerprint ...` | The notebook's prompt or tools have drifted from the cassette | Don't edit `SYSTEM_PROMPT`, the tool definitions, or the sample queries. If the error persists, ask your instructor — they may need to re-record the cassette |
| Network errors when calling Fiddler | VPN / venue Wi-Fi blocking the Fiddler sandbox URL | Try a personal hotspot, or confirm with your IT team that the sandbox URL is reachable |
| `ModuleNotFoundError: fiddler_langgraph` after install cell | Wrong kernel, or install cell skipped | Re-run the install cell with the correct kernel selected |

---

Questions? Reach out to your instructor before the session.
