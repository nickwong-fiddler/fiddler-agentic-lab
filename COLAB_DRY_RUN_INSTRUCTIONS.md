# Pre-Lab Dry Run — Fiddler Agentic Monitoring (Offline Variant in Google Colab)

Hi AIG team,

Before our hands-on Fiddler agentic monitoring lab next week, please run through this short dry run in **Google Colab** to confirm the notebook works end-to-end and that you have the access you'll need on lab day. It should take ~15 minutes.

If anything fails, capture the full error text and send it back to me so we can fix it before the session — not during it.

---

## What you're verifying

1. The Colab link opens and the notebook runs through the pre-Fiddler cells cleanly.
2. You can reach the Fiddler sandbox URL from your browser.
3. You can create a **GenAI Application** and an **Access Key** in the sandbox.
4. The instrumented agent successfully sends traces to Fiddler.
5. (Optional) The Fiddler Guardrails endpoint is reachable from Colab.

---

## Prerequisites (≈2 min to check)

- [ ] A Google account (any personal or work Google account; Colab is free).
- [ ] Browser HTTPS access to the **Fiddler sandbox URL** — I'll share this separately. Open it once now and confirm you can log in.
- [ ] Your sandbox account has permission to:
  - Create a **GenAI Application** inside the shared project `fiddler_day_lab`.
  - Create an **Access Key** under your user (Settings → Credentials → Access Keys).

If any of those three boxes can't be checked, stop here and ping me.

---

## Step 1 — Open the notebook in Google Colab (1 click)

Click this link:

```
https://colab.research.google.com/github/nickwong-fiddler/fiddler-agentic-lab/blob/main/Fiddler_Ecommerce_Agent_Offline.ipynb
```

When Colab opens the notebook:

1. Click **File → Save a copy in Drive** so your changes (pasted credentials, run outputs) persist.
2. Confirm the runtime is connected (top-right: "Connect" → "Connected" with a green check). Default CPU runtime is fine — no GPU needed.

---

## Step 2 — Run cells top-to-bottom through "Run the Agent" (≈3 min)

Use **Shift+Enter** on each cell, or **Runtime → Run all** through the third `ask(...)` cell.

Expected checkpoints:

| Cell | Expected output |
|---|---|
| `%pip install -q langgraph ...` | Finishes in ~60 s. A couple of `pip` dependency warnings are normal — ignore them. |
| **Fetch `cassette.json`** (new cell) | Prints `Downloaded cassette.json (~20,000 bytes)` on first run. |
| `LLM_MODEL = "gpt-4o-mini"` | `Using replayed responses for model: gpt-4o-mini` |
| Dataset cell | `Dataset: 500 orders, 11 columns` then a table of 5 rows. |
| `ReplayChatModel` definition | `ReplayChatModel ready.` |
| `model = ReplayChatModel(...)` / agent creation | `Loaded cassette: N recorded interactions` + `Agent ready.` (**no** `⚠️ WARNING: SYSTEM_PROMPT has changed...` line) |
| `ask("What are the top 5 products by total revenue?")` | A coherent answer listing products with revenue figures. |
| `ask("What is the average order value by region?")` | A coherent answer with 4 region figures. |
| `ask("Are there any anomalies in revenue?")` | A coherent answer about outlier revenue values. |

> **🛑 Stop point:** if all the above worked, the notebook + cassette + Colab path are verified. If any cell failed, stop and report the full error text — do not continue to Step 3.

---

## Step 3 — Create your Fiddler Application & Access Key (≈3 min)

In a new browser tab, log in to the Fiddler sandbox URL I shared.

### 3a. Onboard a GenAI Application

Follow **§ 1.A** in the notebook (the markdown is detailed; skim it). Quick version:

1. Left sidebar → **GenAI Applications** icon → **+ Add Application**.
2. **Step 1:** Use Existing Project → select `fiddler_day_lab` → **Next**.
3. **Step 2:** Application Name = `lab-<your-initials>-ecom-agent-DRYRUN` → **Create Application**.
   - The `-DRYRUN` suffix matters: it lets us delete this app at the end without touching your lab-day app.
4. **Step 3:** On the "Setup Complete!" screen, **copy the App ID UUID**. Leave this dialog open.

### 3b. Create an Access Key

1. From the "Setup Complete!" dialog, click **Create API Key** (opens Settings → Credentials → Access Keys).
2. **+ Create Key** → name it `lab-<your-initials>-ecom-agent-DRYRUN-key` → **Create Key**.
3. **Copy the access key immediately** (starts with `fkh_`). You cannot view it again.

### 3c. Paste credentials into the notebook

Back in Colab, find the **§ 1.C config cell** and fill in all three values:

```python
FIDDLER_URL            = "<the sandbox URL I shared>"
FIDDLER_API_KEY        = "fkh_..."                          # from 3b
FIDDLER_APPLICATION_ID = "xxxxxxxx-xxxx-xxxx-xxxx-..."     # from 3a
```

Run the cell. Expected output: `Fiddler config looks good.`

If you see `AssertionError: FIDDLER_URL not set ...` or `ValueError: badly formed hexadecimal UUID string`, you missed a paste. Re-check and re-run.

---

## Step 4 — Verify the agent sends traces to Fiddler (≈2 min)

1. Run the **§ 2** instrumentation cell. Expected output: `Instrumented. Conversation ID: lab_<uuid>`.
2. Run the **§ 3** cell (two `ask(...)` calls).
3. In the Fiddler UI: go to your application → **Trace Explorer** tab.
4. Within ~30 seconds you should see **2 new traces** appear. Click one and expand its span tree — you should see a `chain` span at the top, with nested `tool` and `llm` spans underneath.
5. Filter by **Session ID** = the conversation ID printed by the § 2 cell → you should see your two traces grouped.

If no traces appear after 60 seconds:
- Double-check the URL/key/App ID in the § 1.C config cell.
- Check the Colab cell output for any HTTP errors during `agent.invoke()`.
- Report what you see.

---

## Step 5 (optional) — Verify the Guardrails endpoint (≈1 min)

This confirms `/v3/guardrails/ftl-safety` is reachable from Colab. Run the **§ 5** cell that defines `safety_check`, then in a new scratch cell:

```python
safety_check("hello")
```

Expected: a dict of `fdl_*` score keys with float values. Any HTTP error means the guardrail endpoint isn't reachable — report it.

You can skip the `guarded_ask(...)` demo cells; the smoke test above is enough.

---

## Step 6 — Cleanup (≈1 min)

So the lab-day view isn't cluttered with dry-run artifacts:

1. In the Fiddler UI → your application → settings → **Delete Application** (the `-DRYRUN` one you just created).
2. In Settings → Credentials → Access Keys → delete the `-DRYRUN-key` you created.

---

## What to report back

Please send me a one-line pass/fail for each of these, plus full error text for any failures:

- [ ] Step 2 — notebook runs through the three `ask(...)` cells without errors.
- [ ] Step 3 — created an App and Access Key in the sandbox; § 1.C config cell printed `Fiddler config looks good.`
- [ ] Step 4 — two traces appeared in **Trace Explorer** within 60 seconds.
- [ ] Step 5 (optional) — `safety_check("hello")` returned a dict of scores.
- [ ] Step 6 — cleanup done.

---

## Common gotchas

| Symptom | Fix |
|---|---|
| `FileNotFoundError: cassette.json` | The fetch cell was skipped. Re-run the cell directly under the `%pip install` cell. |
| `RuntimeError: No recorded response for fingerprint ...` | You edited a sample query, the system prompt, or a tool. Use the notebook as shipped — don't modify text in the `ask(...)` calls. |
| `ModuleNotFoundError: fiddler_langgraph` | The `%pip install` cell was skipped or the Colab runtime restarted. Re-run from the top. |
| `requests.exceptions.ConnectionError` against the Fiddler URL | Your network is blocking the sandbox URL. Try a different network or check with your IT team. |
| App ID UUID validation error | You probably pasted the application *name* instead of the App ID UUID. Go back to the "Setup Complete!" screen and copy the UUID. |

---

Thanks — getting these checks done ahead of time means we spend the lab on the interesting parts, not on setup. Ping me with any blockers.

— Nick
