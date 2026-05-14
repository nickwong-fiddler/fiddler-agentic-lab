# Lab Prerequisites

Welcome! To make the most of our 60-minute hands-on Fiddler agentic monitoring lab, **please complete the setup below before the session.** We will not have time to debug environment issues during the lab.

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
- HTTPS access to `api.openai.com` and the Fiddler sandbox URL (provided by your instructor)

### Step 1 — Clone the lab repo

```bash
git clone https://github.com/nickwong-fiddler/fiddler-agentic-monitoring-lab.git
cd fiddler-agentic-monitoring-lab
```

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

Open `Fiddler_Ecommerce_Agent.ipynb` in your editor. In the top-right of the notebook, open the kernel picker and select **"Python (fiddler-lab)"**.

> ⚠️ **Critical — read this:** `%pip install` installs into whichever kernel is *currently selected*, NOT the venv you `source`'d in your terminal. If the wrong kernel is selected in step 3, the install cell may succeed but later imports will fail with confusing errors. This is the #1 cause of "it doesn't work" during labs.

### Step 4 — Verify

Run the first two cells of the notebook (the `%pip install` cell and the LLM config cell). If both complete without errors, you're ready for the lab.

---

## Option B — Google Colab

Your instructor will share a Colab link on the day of the lab. Colab provides Python and an isolated runtime per notebook — nothing to install in advance.

---

## What you'll need on the day of the lab

Your instructor will provide:

- A Fiddler sandbox URL
- A shared OpenAI API key (already pre-populated in the notebook by your instructor)

You will create your own (during the lab, ~7 min total):

- Fiddler GenAI Application (walkthrough in § 1 of the notebook)
- Fiddler API access key (walkthrough in § 1 of the notebook)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `%pip install` succeeds but `import pandas` fails | Wrong kernel selected | Re-do Step 3 — make sure "Python (fiddler-lab)" is the active kernel |
| `assert LLM_API_KEY ...` fires when running the LLM config cell | Instructor's key hasn't been pasted yet | Ask your instructor for the shared key |
| Network errors when calling Fiddler or OpenAI | VPN / venue Wi-Fi blocking | Try a personal hotspot |
| `ModuleNotFoundError: fiddler_langgraph` after install cell | Wrong kernel, or install cell skipped | Re-run the install cell with the correct kernel selected |

---

Questions? Reach out to your instructor before the session.
