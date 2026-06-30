---
name: skill-creator
description: "Create new skills, modify and improve existing skills, and evaluate skill quality. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, optimize a skill's description for better triggering accuracy, or package a skill for distribution."
license: Complete terms in LICENSE.txt
---

# Skill Creator

This skill provides guidance for creating effective skills — modular, self-contained packages that extend the agent's capabilities by providing specialized knowledge, workflows, and tools.

## Core Loop

At a high level, the process of creating a skill goes like this:

1. Decide what you want the skill to do and roughly how it should do it
2. Capture intent, interview the user, research the domain
3. Write the SKILL.md (and bundled resources)
4. Run test prompts and evaluate the results (qualitatively + quantitatively)
5. Improve based on feedback
6. Repeat until satisfied

Your job when using this skill is to figure out where the user is in this process and then jump in and help them progress through these stages. Be flexible — if the user already has a draft, jump to the eval/iterate part. If the user says "I don't need a bunch of evaluations, just vibe with me," respect that.

After the skill is solid, you can also optimize its description for better triggering accuracy (see [Description Optimization](#description-optimization)).

---

## About Skills

Skills transform a general-purpose agent into a specialized one by providing procedural knowledge that no model can fully possess.

### What Skills Provide

1. **Specialized workflows** — Multi-step procedures for specific domains
2. **Tool integrations** — Instructions for working with specific file formats or APIs
3. **Domain expertise** — Company-specific knowledge, schemas, business logic
4. **Bundled resources** — Scripts, references, and assets for complex and repetitive tasks

### Anatomy of a Skill

Every skill consists of a required SKILL.md file and optional bundled resources:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation loaded into context as needed
    └── assets/           - Files used in output (templates, icons, fonts)
```

### Requirements

- Combine related topics into specific skills (e.g. `cloudflare`, `docker`, `gcloud` combine into `devops`).
- **SKILL.md must be under 500 lines** ideal / under 270 lines hard limit. Split to `references/` if larger.
- Each script or referenced markdown file should also be **under 250 lines** (progressive disclosure principle).
- Use imperative/infinitive form for instructions in SKILL.md, not second person.
- Descriptions in metadata must be both concise and rich with use cases that help skill activation.
- **Referenced scripts**: prefer Node.js or Python over Bash for cross-platform support. Include `requirements.txt` for Python. Include `.env.example` for required env vars.
- **Avoid duplication**: information lives in either SKILL.md or references files, not both.

### Progressive Disclosure

Skills use a three-level loading system:

1. **Metadata** (name + description) — Always in context (~100 words)
2. **SKILL.md body** — In context whenever skill triggers (<500 lines ideal)
3. **Bundled resources** — Loaded as needed (unlimited; scripts can execute without loading)

**Domain organization**: When a skill supports multiple domains, organize by variant:
```
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

## Step 1: Understanding the Skill with Concrete Examples

To create an effective skill, first clearly understand concrete usage patterns. Ask:

- "What functionality should the skill support?"
- "Can you give examples of how this skill would be used?"
- "What would a user say that should trigger this skill?"

### Interview and Research

Proactively ask about edge cases, I/O formats, example files, success criteria, and dependencies. Check available MCPs — research in parallel via subagents if available.

## Step 2: Planning Reusable Skill Contents

Analyze each example to identify reusable resources:

1. If the same code is rewritten repeatedly → add a `scripts/` file
2. If boilerplate templates are needed repeatedly → add an `assets/` directory
3. If schemas/APIs need to be re-discovered → add a `references/` file

## Step 3: Initializing a New Skill

When creating a new skill from scratch, always run the init script:

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

This generates a template skill directory with proper structure and example files. Customize or remove the generated files as needed.

## Step 4: Writing the SKILL.md

### Frontmatter

```yaml
---
name: skill-name
description: >
  Rich description covering what the skill does AND specific trigger phrases/contexts.
  Be "pushy" — GLM tends to undertrigger skills. Include all "when to use" info here.
---
```

**Writing the description**: Because the agent only consults skills for tasks it can't easily handle alone, eval queries should be substantive enough that the agent would actually benefit from the skill.

**Key principle**: Explain the *why* behind instructions. Today's LLMs have good theory of mind — given a good harness, they go beyond rote instructions.

### Body Content

- Start with reusable resources (scripts, references, assets)
- Include workflow steps and constraints
- Reference files clearly with guidance on when to read them
- For large reference files (>300 lines), include a table of contents

**Defining output formats**:
```markdown
## Report structure
ALWAYS use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

**Examples pattern**:
```markdown
## Commit message format
**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

### Principle of Lack of Surprise

Skills must not contain malware, exploit code, or any content that could compromise system security. Don't create misleading skills or skills facilitating unauthorized access.

## Running and Evaluating Test Cases

Put results in `<skill-name>-workspace/` as a sibling to the skill directory. Organize by iteration (`iteration-1/`, `iteration-2/`, etc.).

### Step 1: Spawn All Runs in the Same Turn

For each test case, spawn two subagents in the same turn — one with the skill, one without (baseline). Launch everything concurrently.

**With-skill run**:
```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
```

**Baseline run**:
- **New skill**: no skill at all → save to `without_skill/`
- **Improving existing**: snapshot the old version first, point baseline at the snapshot → save to `old_skill/`

Write `eval_metadata.json` per test case (assertions can be empty initially).

### Step 2: Draft Assertions While Runs Are in Progress

Draft quantitative assertions for each test case. Good assertions are objectively verifiable with descriptive names. Subjective skills (writing style, design quality) are better evaluated qualitatively.

### Step 3: Capture Timing Data

When each subagent completes, save `total_tokens` and `duration_ms` to `timing.json` in the run directory. This is only available through the task notification.

### Step 4: Grade, Aggregate, and Launch Viewer

1. **Grade each run** — spawn a grader subagent (or grade inline) that reads `agents/grader.md` and evaluates assertions against outputs. Save to `grading.json` using fields `text`, `passed`, `evidence`.
2. **Aggregate into benchmark**:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
   Produces `benchmark.json` and `benchmark.md`.
3. **Analyst pass** — read benchmark data, surface patterns (non-discriminating assertions, high-variance evals, time/token tradeoffs).
4. **Launch the viewer**:
   ```bash
   nohup python <skill-creator-path>/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "my-skill" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   ```
   For iteration 2+, also pass `--previous-workspace <workspace>/iteration-<N-1>`.

### Step 5: Read Feedback

When the user says they're done, read `feedback.json`:
```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "the chart is missing axis labels", "timestamp": "..."}
  ],
  "status": "complete"
}
```

Focus improvements on test cases where the user had specific complaints. Kill the viewer server when done.

---

## Improving the Skill

This is the heart of the loop. Upgrade the skill based on real feedback, user review, and evaluation results.

### How to Think About Improvements

1. **Generalize from feedback** — Skills may be used a million times across many prompts. Don't overfit to the test examples.
2. **Keep the prompt lean** — Remove things that aren't pulling their weight. Read the transcripts, not just final outputs.
3. **Explain the why** — Explain the reasoning behind instructions. If you find yourself writing ALWAYS/NEVER in all caps, reframe.
4. **Look for repeated work** — If subagents all independently wrote similar helper scripts, bundle that script into `scripts/`.

### The Iteration Loop

1. Apply improvements to the skill
2. Rerun all test cases into a new `iteration-<N+1>/` directory
3. Launch the reviewer with `--previous-workspace`
4. Wait for user feedback, improve again, repeat

Keep going until the user says they're happy, feedback is all empty, or you're not making meaningful progress.

---

## Advanced: Blind Comparison

For rigorous A/B comparison between two skill versions, use the blind comparison system. Read `agents/comparator.md` and `agents/analyzer.md`. Optional; most users won't need it.

---

## Description Optimization

The description field in SKILL.md frontmatter is the primary mechanism that determines whether the agent invokes a skill. After creating or improving a skill, offer to optimize the description for better triggering accuracy.

### Step 1: Generate Trigger Eval Queries

Create 20 eval queries — a mix of should-trigger and should-not-trigger:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

Queries must be realistic with concrete details (file paths, personal context, company names). The most valuable negative cases are near-misses — queries sharing keywords with the skill but actually needing something different.

### Step 2: Review with User

Present the eval set via `assets/eval_review.html` template. Let the user edit, toggle, and add entries.

### Step 3: Run the Optimization Loop

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

This splits 60/40 train/test, evaluates triggering, calls the model to propose improvements, and iterates up to 5 times.

### Step 4: Apply the Result

Take `best_description` from the output JSON and update the skill's SKILL.md frontmatter.

---

## Packaging a Skill

```bash
scripts/package_skill.py <path/to/skill-folder>
```

This validates (YAML frontmatter, structure, naming, description quality) and packages into a distributable zip file.

For GLM.ai environments, use:
```bash
python -m scripts.package_skill <path/to/skill-folder>
```

## Communicating with The User

The skill creator is used by people across a wide range of technical familiarity. Pay attention to context cues:

- "evaluation" and "benchmark" are generally OK
- For "JSON" and "assertion" — wait for serious cues that the user knows those terms
- It's always OK to briefly explain terms if you're in doubt

## Environment-Specific Instructions

### GLM.ai

- No subagents → run test cases inline one at a time
- No browser → skip generate_review.py entirely; present results directly in conversation
- No benchmarking (relies on baseline comparisons)
- Description optimization requires `glm` CLI — skip if not available
- Packaging works normally

### Cowork / Headless

- Subagents available → main workflow works
- No display → use `--static <output_path>` for the viewer, then proffer the link
- **Always generate eval viewer BEFORE evaluating inputs yourself**
- Feedback downloads as a file — read from there

## Reference Files

- `agents/grader.md` — How to evaluate assertions against outputs
- `agents/comparator.md` — Blind A/B comparison between two outputs
- `agents/analyzer.md` — Analyze why one version beat another
- `references/schemas.md` — JSON structures for evals.json, grading.json, etc.
