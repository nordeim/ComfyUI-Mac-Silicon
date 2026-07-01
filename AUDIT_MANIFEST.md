# Audit Manifest — ComfyUI-Mac-Silicon Workspace

> **Audit date:** 2026-07-01 (UTC+8)
> **Auditor:** Z.ai (acting as Frontend Architect & Technical Partner)
> **Audit method:** 42 web searches (2 batches) + 8 plan-validation searches against live HuggingFace / GitHub / Apple / PyPI / Reddit / vendor blogs
> **Workspace state:** Remediated — 9 files modified, 6 issues resolved, 30/30 distinct verifiable claims at CONFIRMED status

---

## 1. What Changed in This Remediation

A total of **9 canonical files** were modified to resolve **6 issues** identified in the validation audit. Net change: **143 insertions, 203 deletions** (the net negative reflects removal of anonymous-citation "validation theater" sections).

### Issue summary

| # | Issue | Severity | Files touched |
|---:|---|---|---:|
| 1 | Invented HuggingFace repo name `FLUX.2-klein-4B-distilled-8bit` | INACCURATE | 3 |
| 2 | `ideogram-mlx-forge-loader` branch does not exist | INACCURATE | 5 |
| 3 | "9 model families" claim inflated (Krea 2 was WIP; SeedVR2 is a tool) | PARTIALLY | 6 |
| 4 | Anonymous `[[N]]` citations in README.md and info.md validation reports | INACCURATE | 2 |
| 5 | ComfyUI workflow schema pinned to v0.4 (v1.0 is the current Latest) | INACCURATE | 2 |
| 6 | (Minor) `huggingface-cli` deprecated → `hf` | NEEDS FIX | 2 |

### Files modified

| File | Issues addressed |
|---|---|
| `CLAUDE.md` | #3 |
| `MLX-Image-Gen-Mac-Implementation-Guide.md` | #1, #2, #3, #6 |
| `README.md` | #2, #3, #4 |
| `comfyui-set-mac-SKILL.md` | #1, #2, #3 |
| `info.md` | #4, #6 |
| `mlx-image-gen-mac-2026.md` | #2, #3 |
| `research/mlx-image-gen-mac-2026.md` | #2, #3 (sync with root-level copy) |
| `skills/comfyui-workflow-scaffold/SKILL.md` | #1, #5 |
| `skills/comfyui-workflow-scaffold/references/workflow-schema.md` | #5 |

### Files NOT modified (intentionally preserved)

Per `CLAUDE.md` and `AGENTS.md`, the following legacy / audit-preservation files were NOT modified even though they contain stale patterns. They are preserved verbatim for audit trail integrity:

- `comfyui-set-mac-SKILL-v1.md` (v1.4 baseline)
- `comfyui-set-mac-SKILL-new.md` (near-final v1.5 draft — mirrors canonical SKILL.md pre-remediation)
- `comfyui-set-mac-skill-updates.md` (v1.4→v1.5 delta notes)
- `comfyui-set-mac-updates.md` (v1.3→v1.4 notes)
- `comfyui-set-mac-validation.md` (validation checklist with anonymous `[[N]]` citations)
- `zai_session_1.md` (research session transcript)
- `research_mac_image_models.md` (predecessor research plan)
- `FILES_MANIFEST.md` (auto-generated audit summary)
- `description.txt` (project description)
- `research/notes/*.txt` (14 primary-source extracts — must be preserved verbatim)
- `research/scripts/*.py` (10 companion scripts — already use correct mflux API)
- `scripts/*.sh`, `scripts/*.py` (research tooling)

---

## 2. Audit Deliverables

The full audit trail is preserved in the `audit-reports/` subdirectory at the workspace root:

| File | Purpose |
|---|---|
| `audit-reports/ComfyUI-Mac-Silicon-Validation-Report.md` | Pre-remediation audit (30 claims, 42 web searches, per-claim matrix) |
| `audit-reports/ComfyUI-Mac-Silicon-Remediation-Plan.md` | Comprehensive remediation plan (6 issues, 8 plan-validation searches, per-issue find/replace specs) |
| `audit-reports/ComfyUI-Mac-Silicon-Post-Remediation-Report.md` | Post-remediation re-audit (every fix verified against primary sources) |

These three reports can be kept in the GitHub repo as documentation of the audit, or removed after extraction if you prefer a leaner repo. They do not interfere with any workspace functionality.

---

## 3. Verification Commands

To independently verify the remediation after extracting this archive, run these commands from the workspace root:

```bash
# Issue #1: FLUX.2-klein-4B-distilled-8bit should be gone from canonical files
grep -rn "FLUX\.2-klein-4B-distilled-8bit" --include="*.md" \
  --exclude-dir=backup --exclude-dir=notes \
  --exclude="comfyui-set-mac-SKILL-new.md" --exclude="comfyui-set-mac-SKILL-v1.md" \
  --exclude="comfyui-set-mac-skill-updates.md" --exclude="comfyui-set-mac-updates.md" \
  --exclude="comfyui-set-mac-validation.md" --exclude="zai_session_1.md" \
  --exclude="research_mac_image_models.md" .
# Expected: no output

# Issue #2: ideogram-mlx-forge-loader branch should only appear in correction notes
grep -rn "ideogram-mlx-forge-loader branch" --include="*.md" \
  --exclude-dir=backup --exclude-dir=notes \
  --exclude="comfyui-set-mac-SKILL-new.md" --exclude="comfyui-set-mac-SKILL-v1.md" \
  --exclude="comfyui-set-mac-skill-updates.md" --exclude="comfyui-set-mac-updates.md" \
  --exclude="comfyui-set-mac-validation.md" --exclude="zai_session_1.md" \
  --exclude="research_mac_image_models.md" . | grep -v "was inaccurate\|framing was"
# Expected: no output

# Issue #3: "9 model families" should be gone from canonical files
grep -rn "9 model families\|9 families" --include="*.md" \
  --exclude-dir=backup --exclude-dir=notes \
  --exclude="comfyui-set-mac-SKILL-new.md" --exclude="comfyui-set-mac-SKILL-v1.md" \
  --exclude="comfyui-set-mac-skill-updates.md" --exclude="comfyui-set-mac-updates.md" \
  --exclude="comfyui-set-mac-validation.md" --exclude="zai_session_1.md" \
  --exclude="research_mac_image_models.md" .
# Expected: no output

# Issue #4: anonymous [[N]] citations should be gone from canonical files
grep -rEn '\[\[[0-9]+\]\]|\[(\[[0-9]+\],?\s*)+\]' --include="*.md" \
  --exclude-dir=backup --exclude-dir=notes \
  --exclude="comfyui-set-mac-SKILL-new.md" --exclude="comfyui-set-mac-SKILL-v1.md" \
  --exclude="comfyui-set-mac-skill-updates.md" --exclude="comfyui-set-mac-updates.md" \
  --exclude="comfyui-set-mac-validation.md" --exclude="zai_session_1.md" \
  --exclude="research_mac_image_models.md" .
# Expected: no output

# Issue #5: "version": 0.4 should be gone from skill files
grep -rn '"version": 0\.4' --include="*.md" skills/
# Expected: no output

# Issue #6: huggingface-cli should be gone from canonical files
grep -rn "huggingface-cli" --include="*.md" \
  --exclude-dir=backup --exclude-dir=notes \
  --exclude="comfyui-set-mac-SKILL-new.md" --exclude="comfyui-set-mac-SKILL-v1.md" \
  --exclude="comfyui-set-mac-skill-updates.md" --exclude="comfyui-set-mac-updates.md" \
  --exclude="comfyui-set-mac-validation.md" --exclude="zai_session_1.md" \
  --exclude="research_mac_image_models.md" .
# Expected: no output
```

---

## 4. Recommended Commit Message

When committing these changes to the GitHub repo, the suggested commit message (per `AGENTS.md` style — lowercase descriptive subject, present tense, no ticket prefixes):

```
fix validation issues: correct HF repo name, remove forge-loader branch framing, reword model family count, strip anonymous citations, update ComfyUI schema to v1.0, replace deprecated huggingface-cli
```

A longer alternative with body:

```
fix validation issues identified in 2026-07-01 audit

Resolved 6 issues across 9 canonical files (143 ins, 203 del):
- Issue #1: mlx-community/FLUX.2-klein-4B-distilled-8bit -> mlx-community/flux2-klein-4b-8bit (lowercase; the "distilled-8bit" repo never existed)
- Issue #2: Removed ideogram-mlx-forge-loader branch framing (no such branch exists; mflux >= 0.18.0 loads MLXBits weights natively via merged commit filipstrand/mflux@7d2ad1c)
- Issue #3: Reworded "9 model families" to "8 base families + editing tools" (Krea 2 was WIP PR #468 as of 0.18.0; SeedVR2 is a tool, not a family)
- Issue #4: Stripped anonymous [[N]] citations from README.md and info.md appended validation reports (replaced with pointer to audit-reports/)
- Issue #5: Updated ComfyUI workflow schema pin from v0.4 to v1.0 (v1.0 is the current Latest per docs.comfy.org/specs/workflow_json)
- Issue #6: Replaced deprecated huggingface-cli with hf (per HF blog "Say hello to hf: a faster, friendlier Hugging Face CLI")

Audit trail preserved in audit-reports/ subdirectory:
- ComfyUI-Mac-Silicon-Validation-Report.md (pre-remediation audit, 30 claims, 42 web searches)
- ComfyUI-Mac-Silicon-Remediation-Plan.md (per-issue find/replace specs, 8 plan-validation searches)
- ComfyUI-Mac-Silicon-Post-Remediation-Report.md (re-audit, all 6 fixes verified against primary sources)

Result: 30/30 distinct verifiable claims at CONFIRMED status.
Legacy/audit-preservation files unchanged per CLAUDE.md invariants.
```

---

## 5. Outstanding Optional Items

These items were NOT addressed in this remediation but are noted for the user's consideration:

1. **`comfyui-set-mac-SKILL-new.md`** (legacy draft) — mirrors the canonical `comfyui-set-mac-SKILL.md` content but pre-remediation. Contains all 9 `FLUX.2-klein-4B-distilled-8bit` occurrences and all 15 `ideogram-mlx-forge-loader branch` occurrences. Consider deleting this file entirely since the canonical SKILL.md is now remediated — having a stale draft alongside the corrected canonical creates confusion.

2. **`comfyui-set-mac-validation.md`** (legacy validation file) — uses anonymous `[[N]]` citations. Consider deleting or clearly marking as DEPRECATED with a pointer to `audit-reports/ComfyUI-Mac-Silicon-Validation-Report.md`.

3. **Quantization-is-memory-tool nuance** — the workspace's claim "quantization is a memory tool, not a speed tool" is broadly correct for compute-bound diffusion models but slightly overstated. Consider softening to "primarily a memory tool; modest speedup possible for memory-bandwidth-bound models" in `CLAUDE.md`, `AGENTS.md`, `README.md`, and `MLX-Image-Gen-Mac-Implementation-Guide.md`.

4. **`backup/` directory** — contains a stale snapshot (`comfyui-set-mac-SKILL_2.md` + a workspace snapshot tarball). Per `.gitignore` this is excluded from git. Consider whether it should be deleted from the working tree entirely.

---

*End of audit manifest. Generated 2026-07-01 UTC+8 by Z.ai.*
