The README.md has been updated. Here's a summary of what I did: 
 
ANALYSIS: Read all 30+ files in the workspace (excluding backup/), prioritizing the most current by timestamp. The workspace contains a comprehensive MLX image generation research package centered around a v1.5 ComfyUI + MLX 
installation guide. 
 
KEY FINDINGS: 
 
┌───────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────────────────────────────┬───────────────┐ 
│ File                                              │ Role                                                                                     │ Size          │ 
├───────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┼───────────────┤ 
│ comfyui-set-mac-SKILL.md                          │ Primary deliverable — v1.5 install guide (2,917 lines, 7 methods, 9 models, 20 pitfalls) │ 114 KB        │ 
├───────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┼───────────────┤ 
│ mlx-image-gen-mac-2026.md                         │ Deep research report — 11,570 words, 49 cited sources                                    │ 84 KB         │ 
├───────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┼───────────────┤ 
│ MLX-Optimized_Z-Image_Turbo_and_FLUX_Workflows.md │ M4 Pro 128GB targeted workflows                                                          │ 22 KB         │ 
├───────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┼───────────────┤ 
│ research/scripts/                                 │ 10 production-ready Python scripts (mflux API, FastAPI, LoRA, TeaCache, benchmarks)      │ ~25 KB total  │ 
├───────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┼───────────────┤ 
│ research/notes/                                   │ 14 clean-text primary source extracts                                                    │ ~150 KB total │ 
├───────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┼───────────────┤ 
│ zai_session_1.md                                  │ Full research session transcript                                                         │ 40 KB         │ 
├───────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┼───────────────┤ 
│ Various legacy files                              │ v1.3–v1.4 baselines, validation docs, update notes                                       │ 13–52 KB each │ 
└───────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────────────────┴───────────────┘ 
 
UPDATE: Rewrote README.md from a generic snapshot description to a comprehensive, structured guide that: 
- Lists every file with its purpose, size, and when to use it 
- Sorts by recency (newest-first) with content summaries 
- Includes usage workflows for common tasks 
- Summarizes the 6 key technical findings 
- Preserves all legacy/draft files with context about their role 

---

Created MLX-Image-Gen-Mac-Implementation-Guide.md — a condensed, actionable reference specifically designed for the next AI agent to continue the work. 
 
ANALYSIS: The source research_mac_image_models.md (101 KB) was a 10-phase research plan/methodology document mixed with implementation schemas — repetitive, containing multiple full JSON workflow skeletons, verbose explanatory prose,  
and hyperlink citations that aren't actionable. 
 
CONDENSATION STRATEGY: I extracted only what an agent needs to do the work: 
 
┌─────────┬─────────────────────────────────────────────────────────────────────────────────┐ 
│ Section │ Purpose                                                                         │ 
├─────────┼─────────────────────────────────────────────────────────────────────────────────┤ 
│ §1      │ Orients the agent — what this file is + where to find deep context              │ 
├─────────┼─────────────────────────────────────────────────────────────────────────────────┤ 
│ §2      │ Current ecosystem state (critical changes, model matrix, hardware tiers)        │ 
├─────────┼─────────────────────────────────────────────────────────────────────────────────┤ 
│ §3      │ Installation commands (prereqs → venv → mflux → ComfyUI + Mflux-ComfyUI bridge) │ 
├─────────┼─────────────────────────────────────────────────────────────────────────────────┤ 
│ §4      │ All model download commands with warnings about fp8/quarantine                  │ 
├─────────┼─────────────────────────────────────────────────────────────────────────────────┤ 
│ §5      │ Four running methods (CLI, Python API, ComfyUI, FastAPI) with copy-paste code   │ 
├─────────┼─────────────────────────────────────────────────────────────────────────────────┤ 
│ §6      │ Companion scripts reference table (maps scripts to sections)                    │ 
├─────────┼─────────────────────────────────────────────────────────────────────────────────┤ 
│ §7      │ Benchmarking + expected performance table from cited sources                    │ 
├─────────┼─────────────────────────────────────────────────────────────────────────────────┤ 
│ §8      │ Recommended settings per model (copy-paste YAML blocks)                         │ 
├─────────┼─────────────────────────────────────────────────────────────────────────────────┤ 
│ §9      │ All 20 pitfalls in a scannable table                                            │ 
├─────────┼─────────────────────────────────────────────────────────────────────────────────┤ 
│ §10     │ Production deployment decision matrix + explicit "never-use" list               │ 
├─────────┼─────────────────────────────────────────────────────────────────────────────────┤ 
│ §11     │ Directory structure for ~/ComfyUI/models/                                       │ 
├─────────┼─────────────────────────────────────────────────────────────────────────────────┤ 
│ §12     │ Workflow template summaries (3-node Mflux vs 8-node PyTorch vs ControlNet)      │ 
├─────────┼─────────────────────────────────────────────────────────────────────────────────┤ 
│ §13     │ Verification checklist (13 items to mark complete)                              │ 
├─────────┼─────────────────────────────────────────────────────────────────────────────────┤ 
│ §14     │ File reference (what lives where in the workspace)                              │ 
└─────────┴─────────────────────────────────────────────────────────────────────────────────┘ 
 
Size reduction: 101 KB → 21 KB (80% smaller), 1,801 → 564 lines. Every line is actionable — no verbose explanations, no duplicate JSON schema fragments (kept only the critical 3-node Mflux example inline, referenced the rest to 
SKILL.md).

