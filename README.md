# OBSIA

**English** | [Français](README.fr.md)

OBSIA gives your AI assistant a team of specialised agents — one to tidy your
notes, one to run your servers, one to build applications, one to review — and
a memory that lasts from one conversation to the next.

Everything is written as plain text files (Markdown): no database, no closed
format. You can read and edit everything with any editor, or with Obsidian if
you use it.

OBSIA is installed inside a folder of notes, your **vault**. Your memory (your
notes, your projects, what the agents learn) stays there, next to the tool, and
never leaves with it.

> **Language note.** The vault itself — contract, agents, skills, scripts — is
> written in French, and agents answer in French by default. This page and
> [`GETTING-STARTED.md`](GETTING-STARTED.md) are the English entry points.
> Folder names, frontmatter keys and file names stay in French: the scripts
> read them literally.

## How it works

OBSIA rests on three kinds of files:

- an **agent** is a specialised conversation partner: its role, what it can
  do, what it is allowed to touch;
- a **skill** is a competence, a step-by-step procedure (diagnose a machine,
  file a note, prepare a delivery…);
- a **task** is an action launched on its own at a fixed time (for example
  tidying your notes every morning).

OBSIA does nothing on its own: it needs an AI tool that reads these files and
acts, called a **harness** (Claude Code, OpenCode, Codex, Goose…). OBSIA says
*what* to do, the harness provides *what with*. You can switch harness without
losing anything.

The AI does not read everything at once: it first sees the list of agents and
skills, then opens a skill only when it needs it. It stays fast, even with many
skills.

## Getting started

The step-by-step guide is in [`GETTING-STARTED.md`](GETTING-STARTED.md). In short:

```bash
mkdir -p ~/"Mon coffre" && cd ~/"Mon coffre"   # or your existing vault
git clone https://github.com/kevines-ods/OBSIA
cd OBSIA
python3 scripts/installer.py --sonder     # looks at your machine, writes nothing
python3 scripts/installer.py              # asks the questions, shows what will be done
python3 scripts/installer.py --appliquer  # installs
```

All you need is `git` and Python 3: nothing else to install.

Then start your harness **from the vault folder** (`~/Mon coffre`), not from
`OBSIA/`. The installer has placed an `AGENTS.md` file there, which most
harnesses read on their own. To plug yours in, follow its sheet in
`IA/system/adaptateurs-harness/`.

If your harness does not read `AGENTS.md`, you get the same text with
`python3 scripts/generer_prompt.py -o prompt-systeme.md --mcp` (from
`OBSIA/`), to give it as starting instructions. `--mcp` adds a configuration
template for the plugged-in tools (MCP) your agents use: without it, those
tools will not be available.

## Layout

```
OBSIA/                       the tool (your memory sits next to it, not here)
├── IA/
│   ├── agents/              the agents
│   ├── skills/              the skills
│   ├── MCP/                 plugged-in tools (GitHub, browser, mail…)
│   ├── tâches/              the scheduled tasks
│   └── system/              the rules (VAULT-CONTRACT.md), the indexes,
│                            the catalogue of installable modules,
│                            the sheets to plug in each harness
├── brouillon/               free drafts
├── scripts/                 install, check, publish (Python, no dependency)
├── HISTORIQUE.md            what was tried then dropped
├── LICENSE                  AGPL-3.0-or-later
└── README.md
```

OBSIA goes **directly into your vault**, next to your note folders, not in a
subfolder. If you use Obsidian, open it on the whole vault, not on `OBSIA/`
alone: that is what lets links between notes work everywhere.

Your memory (project summaries, work logs, knowledge, profile) lives in the
vault's `0-…` folders, with its own Git history. `OBSIA/` holds none of it: you
can update or reinstall the tool without ever touching your notes.

## Your vault — your memory

OBSIA is the tool; the vault around it holds your memory. It is organised in a
few fixed folders:

| Folder | What it holds |
| --- | --- |
| `0-EN-VRAC/` | what you drop in loose; the agents complete it, then file it |
| `0-SAVOIRS/` | your knowledge: reference notes |
| `0-PROJETS/` | your current projects, with their summaries and work logs |
| `0-MEMOIRES/` | what the agents have learnt, and finished projects |
| `0-DOCUMENTS/` | your documents |
| `0-PERSONNELS/` | what concerns you: your profile, your preferences |
| `_MAINTENANCE/` | the trace of what the agents did |

Only you create or rename these folders. The agents read the whole vault, but
write only in specific places, and they show you what they are about to change
before doing it.

The vault has **its own Git history**, separate from OBSIA's: every change an
agent makes is recorded, and you can always go back. You can push it to the
server of your choice to back it up.

For the agents to reach your notes, your harness must be started **from the
root of the vault**, not from `OBSIA/`. The sheets in
`IA/system/adaptateurs-harness/` explain how to plug in each harness (Claude
Code, OpenCode, AionUi…).

## Scheduled tasks

A task is an action the agents launch on their own at a fixed time: tidy your
notes every morning, check the vault every Monday… Each one is described in a
file of `IA/tâches/`: when to launch it, for which agent, and what to ask.

Tasks are **not** activated by installation: you decide which ones run on your
machine. To activate them (systemd timers):

```bash
mkdir -p ~/.config/obsia
python3 IA/skills/cron/scripts/appliquer_taches.py --config > ~/.config/obsia/appliquer.conf
$EDITOR ~/.config/obsia/appliquer.conf                          # set the command that starts your harness
python3 IA/skills/cron/scripts/appliquer_taches.py              # shows what will change, writes nothing
python3 IA/skills/cron/scripts/appliquer_taches.py --appliquer  # activates
```

If you change machine or harness, nothing is lost: run these commands again and
the tasks are recreated from their files. The details (task format, rules,
special cases) are in the `cron` skill.

---

# Going further

## Choosing what you install

OBSIA is a **catalogue**: you keep only what serves you. No point loading the
Docker skills if you have no containers: they would take up room and offer
themselves at the wrong moment.

Skills are grouped in **modules** (`IA/system/modules/`), for example
"conteneurs", "documents" or "construction". At installation:

1. the installer **looks at your machine** (is Docker there? Proxmox?
   CachyOS?) and derives a default answer;
2. it **asks one question per module**, and your answer decides;
3. it records your choices in an `obsia.local.yml` file, specific to your
   machine and never shared.

It runs no program and makes no network access to look at your machine: it
only checks whether certain programs or files are present.

```bash
python3 scripts/installer.py --sonder             # what was detected
python3 scripts/installer.py                      # the questions, and what will be done
python3 scripts/installer.py --appliquer          # applies your choices
python3 scripts/installer.py --tout --appliquer   # back to the full catalogue
```

Change your mind later: run the installer again, it asks the questions again.
Details (copy mode, probes, what is reduced or not) are in
`IA/system/installation-et-publication.md`.

## Contributing: check before a commit

Before committing:

```bash
python3 -m unittest discover -s tests
python3 scripts/regenerate_sommaire.py
python3 scripts/regenerate_index.py
python3 scripts/verifier_coffre.py
```

The first command runs the `tests/` suite — scripts, installer, publishing,
command line. It needs no dependency either: `unittest` from the standard
library, never `pytest`.

`verifier_coffre.py` rejects an invalid frontmatter, a `name` that does not
match the file name, a list written as a string, a description folded over
several lines, an agent declaring a missing skill or MCP, a task without an
instruction or with an unquoted `quand`, a duplicate note name, or a stale
generated file. It writes nothing and exits with code 1. It warns without
rejecting as soon as the written `AGENTS.md` nears Codex's total instruction
ceiling (28 KiB), and rejects beyond 32 KiB: the global file and the project
files count together, and past the ceiling the surplus is left aside.

The same checks run in continuous integration on every push. No dependency:
Python standard library only.

To run them automatically before each commit, once per clone — `installer.py
--appliquer` arms it for you (§11):

```bash
git config core.hooksPath .githooks
```

## Format

A skill is a file `IA/skills/<name>.md`. When it grows — beyond roughly 500
lines — it becomes a folder `IA/skills/<name>/` whose entry point is called
`<name>.md`, not `SKILL.md`, alongside `references/`, `scripts/` and
`assets/`. Rule in `VAULT-CONTRACT.md` §5, details in
`IA/system/contrat/contrat-frontmatter.md`.

Every agent or skill file starts with a strict YAML frontmatter.

```yaml
---
schema: 1
kind: skill              # agent | skill | mcp | tâche | module | contract
name: skill-name         # lowercase, hyphens, same as the file name
description: One line — what and when.
type: core               # skills only: core | outil
read_only: true
module: noyau            # required: the catalogue module (IA/system/modules/)
---
```

For an agent:

```yaml
---
schema: 1
kind: agent
name: agent-name
description: One line.
skills:
  - first-skill
  - second-skill
mcp:
  - server-name
read_only: false
module: noyau
---
```

Lists are written with hyphens, one entry per line. `skills: a, b` is a
string, not a list.

This frontmatter is the boundary between the tool and any program reading it.
`schema` lets it evolve without breaking existing consumers.

## Rules

They live in `IA/system/VAULT-CONTRACT.md` — the core, always loaded — and its
annexes in `IA/system/contrat/`; the core is authoritative. In short:

- The agents write directly into your memory, but only in the places provided,
  and showing you first what they are about to do. Any change to the tool
  itself (agents, rules) goes through a Git proposal that you review.
- Nothing is lost: the vault's Git history keeps every version.
- A preview is mandatory before any action touching several files.
- Generated files — `sommaire.md` (in the parent vault), `agents-index.md`,
  `skills-index.md`, `taches-index.md`, `modules-index.md`, `IA/README.md` — are regenerated by
  script, never edited by hand. If an index contradicts a frontmatter, the
  frontmatter wins.
- An agent and a skill are two distinct things. An agent decides; a skill
  describes a way of doing.

## Secrets

Everything that enters here ends up in the public distribution. Never let in: keys, tokens, passwords, private IP
addresses, internal host names.

Real inventories (machines, LLM instances) live outside the repository. Only
templates are versioned, such as `IA/MCP/mcp.example.json`.

Check before pushing:

```bash
git diff --cached | grep -iE "password|token|api[_-]key|BEGIN.*PRIVATE KEY"
```

A secret pushed and then deleted stays in the Git history. If it happens:
revoke the secret first, clean the history second.

## Public and private

The working repository is **private**: it carries the tool, its session logs and
its `brouillon/`. This public repository is its **distribution**: the same tool,
minus whatever describes a person or a machine.

The **memory** is in neither: it has its own repository, at the root of the
vault, which you can back up wherever you like. It is not published.

The private one is authoritative, and `scripts/publier.py` derives the public
one from it. One-way flow is not just a precaution: it is what creates the
**validation window**. The private repository is the workshop — a feature is
born there, is tested on real sessions, and only crosses the border on the day
the command is run. Nothing leaves on its own.

Worth knowing before switching an existing repository to private: **it does
not unpublish its past**, which stays with whoever cloned it. The public
repository, on the other hand, starts clean — `publier.py` writes into a fresh
clone, without pouring in the private history.

```bash
git clone https://github.com/kevines-ods/OBSIA ~/OBSIA-public     # once
python3 scripts/publier.py --cible ~/OBSIA-public              # preview
python3 scripts/publier.py --cible ~/OBSIA-public --appliquer
python3 scripts/publier.py --cible ~/OBSIA-public --appliquer \
        --depot-public my-account/OBSIA --commit
```

`--depot-public` rewrites the `git clone https://github.com/…` commands in the
documentation: the private README announces the private address, which would
give a public reader a 404 without telling them why.

It exports the tree tracked by Git at `HEAD` — never the working directory,
because what is not tracked has not been reviewed —, empties
`IA/system/session-log/`, `brouillon/` and `.archive/` of everything but their
`README.md` (during the switch-over, the old `mémoire/` too), runs a leak check,
regenerates the indexes, checks the resulting vault, then writes into the
target. It never pushes.

The leak check looks for **values**, not the words that name them: an email
address, a private IP, a private key block, a known token prefix, a secret
assigned to a variable. It blocks publication; `--forcer` overrides it, and
using it without reading the finding means giving up the last safety net.

## License

**GNU AGPL-3.0-or-later** — full text in [`LICENSE`](LICENSE).

The copyleft is deliberate: a derivative of OBSIA stays free, even if it is
never distributed but only exposed over a network (§13 of the license).

Free software only. Check the license of any skill imported from another
source before integrating it: some catalogues publish under restrictive
licenses, and a license incompatible with the AGPL cannot come in here.
