✅ Summary of Changes to comfyui-set-mac-SKILL.md 
 
### 🔴 Critical Fixes 
 
┌───┬───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐ 
│ # │ Issue                                                                                                             │ Fix Applied                                                                                                    │ 
├───┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ 1 │ LoRA Architecture Mismatch — Section 8 instructed users to apply Ideogram 4 TurboTime LoRA to Z-Image model       │ Replaced Section 8 with a ⚠ LoRA Compatibility Warning explaining architecture-specific LoRAs, compatibility  │ 
│   │ (incompatible, causes tensor crash)                                                                               │ table, and safe usage guidance                                                                                 │ 
├───┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ 2 │ macOS Version Error — "Sequoia 26.x" (Sequoia is v15)                                                             │ Changed to "macOS Tahoe 26.x" throughout                                                                       │ 
├───┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ 3 │ Directory Path Inconsistency — ~/ComfyUI vs ~/ComfyUI-Mac-Silicon mixed randomly                                  │ Unified all paths to ~/ComfyUI consistently                                                                    │ 
└───┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘ 
 
### 🟡 Recommended Improvements 
 
┌────┬──────────────────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────┐ 
│ #  │ Issue                                                                │ Fix Applied                                                                    │ 
├────┼──────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤ 
│ 4  │ Python 3.13 as primary recommendation — many custom nodes lag behind │ Changed primary recommendation to Python 3.12, demoted 3.13 to "bleeding edge" │ 
├────┼──────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤ 
│ 5  │ Pitfall 11 didn't mention LoRA mismatch as a cause                   │ Added LoRA architecture mismatch to the cause description                      │ 
├────┼──────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤ 
│ 6  │ Pitfall 8 missing PYTORCH_MPS_HIGH_WATERMARK_RATIO tip               │ Added environment variable tip for MPS memory                                  │ 
├────┼──────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤ 
│ 7  │ Step 5.4 LoRA download lacked warning                                │ Added explicit ⚠ warning that the LoRA is for Ideogram 4 ONLY                 │ 
├────┼──────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤ 
│ 8  │ Appendix B diagram showed LoRA as universally optional               │ Updated to show architecture compatibility warning                             │ 
├────┼──────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤ 
│ 9  │ Appendix A script used hardcoded paths                               │ Added $COMFYUI_DIR variable for consistency                                    │ 
├────┼──────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤ 
│ 10 │ Changelog not updated                                                │ Added v1.3 entry documenting all fixes                                         │ 
└────┴──────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────┘  

✅ Integration Complete: info.md → comfyui-set-mac-SKILL.md 
 
### What Was Added (v1.4) 
 
┌───────────────────────────────────────┬───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐ 
│ New Section                           │ Content from info.md                                                                                                                  │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ Model Landscape (June 2026)           │ Ideogram 4.0 (9.3B DiT, Qwen3-VL-8B, JSON training), Krea 2 (RAW vs Turbo, CFG-free), Z-Image Turbo architecture overviews            │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ Licensing Warning                     │ Ideogram 4 Non-Commercial Model Agreement — explicit warning about commercial use                                                     │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ Hardware Recommendations by Chip      │ M4 Base (16GB→q4), M4 Pro (24GB→q8), M4 Max (36GB→fp8)                                                                                │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ Three Methods Comparison Table        │ MLX/mflux vs ComfyUI vs Draw Things with performance ratings                                                                          │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ Method 1: Native MLX via mflux        │ Full CLI workflow: install, download (MLXBits, SceneWorks repos), generate commands for both Ideogram 4 and Krea 2 Turbo              │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ Method 3: Draw Things                 │ GUI app workflow: Mac App Store, Model Manager, auto MPS optimization                                                                 │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ JSON Prompting (Ideogram 4)           │ Full JSON schema with high_level_description, style_description, compositional_deconstruction, bounding-box elements, generation tips │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ Krea 2 Model Variants                 │ RAW (training) vs Turbo (inference) explanation added to Section 5                                                                    │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ Ideogram 4 ComfyUI Nodes              │ Day-0 native support note, Ideogram V4 Loader node, Qwen3-VL-8B encoder requirement                                                   │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ Qwen3-VL-8B Encoder Download          │ Added Step 5.2 with correct HuggingFace path                                                                                          │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ Pitfall 13: Krea 2 CFG Must Be 0      │ Explicit warning about CFG=0 requirement, noisy/burnt images symptom                                                                  │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ Pitfall 14: M4 Air Thermal Throttling │ Fanless chassis, 3-5 generation throttle, cooling solutions                                                                           │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ Pitfall 15: MPS vs MLX Performance    │ 2-3× speed difference, recommendation to use mflux for batch work                                                                     │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ Quick Reference MLX Commands          │ Added mflux generate commands to the cheat sheet                                                                                      │ 
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ 
│ Document Information                  │ Updated to v1.4, added Covered Models and Covered Methods lists                                                                       │ 
└───────────────────────────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘ 
 
### What Was Preserved 
 
- All existing ComfyUI installation steps (Sections 1-7) 
- LoRA Compatibility Warning (Section 8, from v1.3) 
- All 12 original pitfalls (expanded to 15) 
- Appendix A (installation script with $COMFYUI_DIR) 
- Appendix B (workflow diagram) 
- Appendix C (verification checklist)

