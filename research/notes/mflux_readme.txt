# GitHub - filipstrand/mflux: MLX native implementations of state-of-the-art generative image models
# URL: https://github.com/filipstrand/mflux
# Published: 

GitHub - filipstrand/mflux: MLX native implementations of state-of-the-art generative image models · GitHub 

 Skip to content 

 Navigation Menu

 Toggle navigation 

 Sign in

 Appearance settings 

 Platform AI CODE CREATION GitHub Copilot Write better code with AI 
 GitHub Copilot app Direct agents from issue to merge 
 MCP Registry New Integrate external tools 
 
 DEVELOPER WORKFLOWS Actions Automate any workflow 
 Codespaces Instant dev environments 
 Issues Plan and track work 
 Code Review Manage code changes 
 
 APPLICATION SECURITY GitHub Advanced Security Find and fix vulnerabilities 
 Code security Secure your code as you build 
 Secret protection Stop leaks before they start 
 
 EXPLORE Why GitHub 
 Documentation 
 Blog 
 Changelog 
 Marketplace 
 
 View all features 
 Solutions BY COMPANY SIZE Enterprises 
 Small and medium teams 
 Startups 
 Nonprofits 
 
 BY USE CASE App Modernization 
 DevSecOps 
 DevOps 
 CI/CD 
 View all use cases 
 
 BY INDUSTRY Healthcare 
 Financial services 
 Manufacturing 
 Government 
 View all industries 
 
 View all solutions 
 Resources EXPLORE BY TOPIC AI 
 Software Development 
 DevOps 
 Security 
 View all topics 
 
 EXPLORE BY TYPE Customer stories 
 Events & webinars 
 Ebooks & reports 
 Business insights 
 GitHub Skills 
 
 SUPPORT & SERVICES Documentation 
 Customer support 
 Community forum 
 Trust center 
 Partners 
 
 View all resources 
 Open Source COMMUNITY GitHub Sponsors Fund open source developers 
 
 PROGRAMS Security Lab 
 Maintainer Community 
 Accelerator 
 GitHub Stars 
 Archive Program 
 
 REPOSITORIES Topics 
 Trending 
 Collections 

 Enterprise ENTERPRISE SOLUTIONS Enterprise platform AI-powered developer platform 
 
 AVAILABLE ADD-ONS GitHub Advanced Security Enterprise-grade security features 
 Copilot for Business Enterprise-grade AI features 
 Premium Support Enterprise-grade 24/7 support 

 Pricing 

 Search or jump to... 

 Search code, repositories, users, issues, pull requests...

 --> 

 Search

 Clear 

 Search syntax tips 

 Provide feedback

 --> 
 We read every piece of feedback, and take your input very seriously.

 Include my email address so I can be contacted 

 Cancel
 
 Submit feedback

 Saved searches

 Use saved searches to filter your results more quickly

 --> 

 Name 

 Query 

 To see all available qualifiers, see our documentation .

 Cancel
 
 Create saved search

 Sign in

 Sign up

 Appearance settings 

 Resetting focus 

 You signed in with another tab or window. Reload to refresh your session. 
 You signed out in another tab or window. Reload to refresh your session. 
 You switched accounts on another tab or window. Reload to refresh your session. 

 Dismiss alert 

 {{ message }} 

 filipstrand
 
 / 
 
 mflux 

 Public 

 Notifications
 You must be signed in to change notification settings 

 Fork
 155 

 Star
 2.2k 

 Code 

 Issues 
 82 

 Pull requests 
 24 

 Actions 

 Projects 

 Security and quality 
 0 

 Insights 

 Additional navigation options 

 Code

 Issues

 Pull requests

 Actions

 Projects

 Security and quality

 Insights

 filipstrand/mflux

 main 89 Branches 55 Tags Go to file Code Open more actions menu Folders and files

 Name Name Last commit message Last commit date Latest commit

 anthonywu and claude Add atomic --lora and --image flags ( #438 ) Open commit details success Jun 24, 2026 32de875 · Jun 24, 2026 History

 549 Commits Open commit details 549 Commits .cursor .cursor docs(porting): add canonical package layout to model-porting skill Jun 6, 2026 .github/ workflows .github/ workflows Add support for Z-image Turbo & major improvements for weight loading… Dec 3, 2025 src/ mflux src/ mflux Add atomic --lora and --image flags ( #438 ) Jun 24, 2026 tests tests Add atomic --lora and --image flags ( #438 ) Jun 24, 2026 .gitignore .gitignore feat: port ERNIE-Image and ERNIE-Image-Turbo (Baidu) to mflux ( #417 ) Jun 6, 2026 .pre-commit-config.yaml .pre-commit-config.yaml 🧹 Cleanup/bump pre-commits; intro mypy config, quick type ignores/fix… Jul 3, 2025 AGENTS.md AGENTS.md Flux2 Klein support ( #323 ) Jan 18, 2026 CHANGELOG.md CHANGELOG.md Add atomic --lora and --image flags ( #438 ) Jun 24, 2026 LICENSE LICENSE Improved metadata handling ( #318 ) Jan 10, 2026 Makefile Makefile Linux support on DGX hardware using mlx[cuda] >= 0.30.3 ( #321 ) Jan 18, 2026 README.md README.md Add mlx-taef and mlx-teacache to Related projects ( #428 ) Jun 6, 2026 _typos.toml _typos.toml feat: port ERNIE-Image and ERNIE-Image-Turbo (Baidu) to mflux ( #417 ) Jun 6, 2026 pyproject.toml pyproject.toml Release 0.18.0 ( #435 ) Jun 7, 2026 uv.lock uv.lock Release 0.18.0 ( #435 ) Jun 7, 2026 View all files Repository files navigation

 README 
 MIT license 
 More items 

 About

 Run the latest state-of-the-art generative image models locally on your Mac in native MLX!

 Table of contents

 💡 Philosophy 

 💿 Installation 

 🎨 Models 

 ✨ Features 

 🌱 Related projects 

 🙏 Acknowledgements 

 ⚖️ License 

 💡 Philosophy

 MFLUX is a line-by-line MLX port of several state-of-the-art generative image models from the Huggingface Diffusers and Huggingface Transformers libraries. All models are implemented from scratch in MLX, using only tokenizers from the Huggingface Transformers library. MFLUX is purposefully kept minimal and explicit, @karpathy style.

 💿 Installation

 If you haven't already, install uv , then run:

 uv tool install --upgrade mflux 

 After installation, the following command shows all available MFLUX CLI commands:

 uv tool list 

 To generate your first image using, for example, the z-image-turbo model, run

 mflux-generate-z-image-turbo \
 --prompt "A puffin standing on a cliff" \
 --width 1280 \
 --height 500 \
 --seed 42 \
 --steps 9 \
 -q 8

 The first time you run this, the model will automatically download which can take some time. See the model section for the different options and features, and the common README for shared CLI patterns and examples.

 Python API 
 Create a standalone generate.py script with inline uv dependencies:

 #!/usr/bin/env -S uv run --script 
 # /// script 
 # requires-python = ">=3.10" 
 # dependencies = [ 
 # "mflux", 
 # ] 
 # /// 
 from mflux . models . z_image import ZImageTurbo 

 model = ZImageTurbo ( quantize = 8 )
 image = model . generate_image (
 prompt = "A puffin standing on a cliff" ,
 seed = 42 ,
 num_inference_steps = 9 ,
 width = 1280 ,
 height = 500 ,
)
 image . save ( "puffin.png" ) 

 Run it with:

 uv run generate.py 

 For more Python API inspiration, look at the CLI entry points for the respective models.

 ⚠️ Troubleshooting: hf_transfer error 
 If you encounter a ValueError: Fast download using 'hf_transfer' is enabled (HF_HUB_ENABLE_HF_TRANSFER=1) but 'hf_transfer' package is not available , you can install MFLUX with the hf_transfer package included:

 uv tool install --upgrade mflux --with hf_transfer 

 This will enable faster model downloads from Hugging Face.

 DGX / NVIDIA (uv tool install) 
 uv tool install --python 3.13 mflux 

 🎨 Models

 MFLUX supports the following model families. They have different strengths and weaknesses; see each model’s README for full usage details.

 Model 
 Release date 
 Size 
 Type 
 Training 
 Description 

 Z-Image 
 Nov 2025 
 6B 
 Distilled & Base 
 Yes 
 Fast, small, very good quality and realism. 

 FLUX.2 
 Jan 2026 
 4B & 9B 
 Distilled & Base 
 Yes 
 Fastest + smallest with very good qaility and edit capabilities. 

 Ideogram 4 
 Jun 2026 
 9B 
 Base 
 No 
 JSON-caption-native, typography-focused text-to-image generation. 

 ERNIE-Image 
 Apr 2026 
 8B 
 Distilled & Base 
 No 
 Single-stream DiT from Baidu. Vivid, high-contrast output. 

 FIBO 
 Oct 2025+ 
 8B 
 Distilled & Base 
 No 
 Very good JSON-based prompt understanding. Has edit capabilities. 

 SeedVR2 
 Jun 2025 
 3B & 7B 
 — 
 No 
 Best upscaling model. 

 Qwen Image 
 Aug 2025+ 
 20B 
 Base 
 No 
 Large model (slower); strong prompt understanding and world knowledge. Has edit capabilities 

 Depth Pro 
 Oct 2024 
 — 
 — 
 No 
 Very fast and accurate depth estimation model from Apple. 

 FLUX.1 
 Aug 2024 
 12B 
 Distilled & Base 
 No (legacy) 
 Legacy option with decent quality. Has edit capabilities with 'Kontext' model and upscaling support via ControlNet 

 ✨ Features

 General 

 Quantization and local model loading

 LoRA support (multi-LoRA, scales, library lookup)

 Metadata export + reuse, plus prompt file support

 Model-specific highlights 

 Text-to-image and image-to-image generation.

 LoRA finetuning

 In-context editing, multi-image editing, and virtual try-on

 ControlNet (Canny), depth conditioning, fill/inpainting, and Redux

 Upscaling (SeedVR2 and Flux ControlNet)

 Depth map extraction and FIBO prompt tooling (VLM inspire/refine)

 See the common README for detailed usage and examples, and use the model section above to browse specific models and capabilities.

 Note

 As MFLUX supports a wide variety of CLI tools and options, the easiest way to navigate the CLI in 2026 is to use a coding agent (like Cursor , Claude Code , or similar). Ask questions like: “Can you help me generate an image using z-image?”

 🌱 Related projects

 MindCraft Studio — macOS app built on mflux by @shaoju 

 Mflux-ComfyUI by @raysers 

 MFLUX-WEBUI by @CharafChnioune 

 mflux-fasthtml by @anthonywu 

 mflux-streamlit by @elitexp 

 mlx-taef — TAESD/TAEF tiny-autoencoder live previews and low-memory FLUX decode for mflux, by @IonDen 

 mlx-teacache — TeaCache step-skipping to speed up FLUX generation in mflux, by @IonDen 

 🙏 Acknowledgements

 MFLUX would not be possible without the great work of:

 The MLX Team for MLX and MLX examples 

 Black Forest Labs for the FLUX project 

 Bria for the FIBO project 

 Tongyi Lab for the Z-Image project 

 Baidu for the ERNIE-Image project 

 Ideogram for the Ideogram 4 project 

 Qwen Team for the Qwen Image project 

 ByteDance, @numz and @adrientoupet for the SeedVR2 project 

 Hugging Face for the Diffusers library implementations 

 Depth Pro authors for the Depth Pro model 

 The MLX community and all contributors and testers 

 ⚖️ License

 This project is licensed under the MIT License .

 About

 MLX native implementations of state-of-the-art generative image models

 Topics

 flux

 ai

 ml

 transformers

 mlx

 fibo

 huggingface

 apple-silicon

 diffusers

 qwen

 qwen-image

 seedvr2

 z-image

 Resources

 Readme

 License

 MIT license

 Uh oh!

 There was an error while loading. Please reload this page .

 Activity 

 Stars

 2.2k 
 stars 

 Watchers

 21 
 watching 

 Forks

 155 
 forks 

 Report repository

 Releases
 55 

 Release 0.18.0 
 
 Latest
 
 Jun 7, 2026 

 + 54 releases 

 Packages
 0 

 No packages published 

 Uh oh!

 There was an error while loading. Please reload this page .

 Contributors
 30 

 + 16 contributors 

 Languages

 Python 
 99.8% 

 Makefile 
 0.2% 

 Footer

 © 2026 GitHub, Inc.

 Footer navigation

 Terms 

 Privacy 

 Security 

 Status 

 Community 

 Docs 

 Contact 

 Manage cookies

 Do not share my personal information

 You can’t perform that action at this time.
