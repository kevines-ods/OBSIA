# OBSIA

**English** | [Français](README.fr.md)

A repository that describes your AI agents — roles, skills, rules — and the tasks
they run, to be cloned at the root of a note vault.

Agents, their skills and their tasks are Markdown files. No database, no
proprietary format: the repository can be read and edited by hand, in Obsidian or
in any text editor. The **memory**, however, lives in the parent vault, not here
(§6, §7.1).

> **Language note.** The vault itself — contract, agents, skills, scripts — is
> written in French, and agents answer in French by default. This page and
> [`GETTING-STARTED.md`](GETTING-STARTED.md) are the English entry points.
> Folder names, frontmatter keys and file names stay in French: the scripts
> read them literally.

## Principle

An **agent** is a file describing a conversational partner: its role, the
skills it uses, the MCP servers it depends on.

A **skill** is a file describing a way of doing something: a procedure,
commands, pitfalls to avoid.

A **task** (`tâche`) is a file describing a scheduled action: when to trigger
it, for which agent, with which instruction.

A **harness** — Claude Code, OpenCode, Codex, Goose, or the interface of your
choice — reads these files and executes. The vault describes *what* to do; the
harness provides *what with*.

Loading is lazy: the system prompt only contains the index of agents, skills
and scheduled tasks. A skill's content is read only when it becomes necessary.

## Layout

```
OBSIA/                       the repository — the tool, not the memory
├── IA/
│   ├── agents/              agent definitions
│   ├── skills/              reusable skills
│   ├── MCP/                 structured tools
│   ├── tâches/              scheduled task registry
│   └── system/              VAULT-CONTRACT.md (the rules), indexes,
│                            modules/ (the installable catalogue),
│                            prompt-fondateur.md (original intent),
│                            adaptateurs-harness/ (integration templates)
├── brouillon/               free scratch area
├── scripts/
│   ├── installer.py         probes the machine, keeps the useful modules
│   ├── publier.py           derives the public mirror from this repository
│   ├── generer_prompt.py    system prompt from the frontmatters
│   ├── regenerate_index.py  the four indexes and IA/README.md
│   ├── regenerate_sommaire.py  the sommaire.md files of the parent vault
│   └── verifier_coffre.py   vault consistency checks — run in CI
├── HISTORIQUE.md            what was decided, then dropped
├── LICENSE                  AGPL-3.0-or-later
├── README.md
└── .gitignore
```

There is no "vault" subfolder: `OBSIA/` is installed **at the root** of your
Obsidian vault, next to your knowledge folders, and Obsidian opens that whole
vault (not `OBSIA/` alone): that is what makes backlinks resolve across the vault
(§7). The memory — summaries, logs, knowledge, profile — lives in the `0-…`
folders of that parent vault, under its own Git repository (§6, §7.1); `OBSIA/`
holds none of it.

The vault knows no interface and names none. It describes *what* to do; the
harness of your choice provides *what with*. Nothing here depends on a
particular program — that is what keeps OBSIA free to move.

## The parent vault — your knowledge base

OBSIA is the tool; the vault around it carries your memory. It is written
`Mon coffre/` throughout the repository, and `OBSIA/` is installed at its root,
next to `_MAINTENANCE/`, `0-PROJETS/` (projects),
`0-MEMOIRES/` (agent memory, and closed work), `0-DOCUMENTS/`,
`0-PERSONNELS/` (personal), `0-SAVOIRS/` (knowledge) and
`0-EN-VRAC/` (inbox). Every top-level memory folder starts with `0-` (§7.1).

The parent vault is **its own Git repository**: memory is versioned there, on a
single writer, and pushed to one remote (bare, on the NAS). `OBSIA/`,
`brouillon/`, `.obsidian/` and the rest of the tool are excluded by a
whitelist `.gitignore`; `**/.git` stays out of Syncthing (§7). Nothing private
leaves the tool: `OBSIA/brouillon/` and `OBSIA/IA/system/session-log/` are never
published (§8).

The top-level structure is fixed (only you change it). Agents read the whole
parent vault, fill in the notes of `0-EN-VRAC/` (body, tags, backlinks) and then
file them, complete the notes dropped into `0-SAVOIRS/`, and log previews and
actions in `_MAINTENANCE/`. `0-EN-VRAC/` is a **buffer**: a tidying session
empties it entirely. The full rules are in §7 of
`IA/system/VAULT-CONTRACT.md`.

For agents to reach the parent vault, the harness needs access to its root —
not just to `OBSIA/`: a working directory opened on the vault, or a "files" MCP
server (card `IA/MCP/coffre-parent.md`, template `IA/MCP/mcp.example.json`).
The actual configuration lives outside the repository.

**Per-harness integration templates** — Claude Code, OpenCode, OpenClaw,
DeepSeek Harness, AionUi/ObsiaUi, LibreChat — live in
`IA/system/adaptateurs-harness/`.

## Scheduled tasks

A recurring task is declared in `IA/tâches/<name>.md`: when, for which agent,
and the exact instruction to send it. That file is the source of truth.

The systemd timer, the harness scheduler or the machine's cron are only
**instances** of that declaration: named `obsia-<name>`, disposable, rebuilt
from the registry. Changing harness or machine therefore loses nothing — read
the registry again and re-instantiate.

```yaml
---
schema: 1
kind: tâche
name: revue-hebdomadaire-du-coffre
description: One line — what, and how often.
mode: agent              # agent | commande
quand: "0 9 * * 1"       # 5-field cron, quoted
fuseau: Europe/Paris     # time zone
exécutant: local         # local | harness — who is allowed to trigger it
agent: assistant
actif: true
---
```

The body carries the instruction — self-contained, since there is no
conversation left at trigger time. Rules in §12 of `VAULT-CONTRACT.md`,
procedure in the `cron` skill.

One task = **at most one live instance**, across all executors. That is what
`exécutant` is for: scheduling the same thing on the harness side *and* on the
machine would trigger it twice, with no error to tell you.

Turning the registry into systemd timers is tooled. The full sequence, once
per machine:

```bash
mkdir -p ~/.config/obsia
python3 IA/skills/cron/scripts/appliquer_taches.py --config > ~/.config/obsia/appliquer.conf
$EDITOR ~/.config/obsia/appliquer.conf                          # fill in commande_agent
python3 IA/skills/cron/scripts/appliquer_taches.py              # preview, writes nothing
python3 IA/skills/cron/scripts/appliquer_taches.py --appliquer  # apply
```

`--config` **writes nothing**: it prints a template that you redirect
yourself. That file is not versioned, on purpose — it names the harness that
launches an agent, which the vault never does (§3 of `VAULT-CONTRACT.md`). As
long as `commande_agent` is empty, a `mode: agent` task is **refused** rather
than instantiated inert. A `mode: commande` task needs neither of the first
two lines.

The script then compares the registry with the `obsia-*` units present, shows
the table of differences, and only writes with `--appliquer`. It is the only
script in the repository that depends on an executor — so it lives in the
skill that uses it, not in `scripts/`, which stays usable with nothing
installed.

`IA/system/taches-index.md`, generated like the other indexes, keeps the
registry permanently in context: a fresh harness knows these tasks exist. It
does not create them on the machine — instantiation remains an explicit step.

## Getting started

The step-by-step guide is in [`GETTING-STARTED.md`](GETTING-STARTED.md): clone
into your vault, install, launch a harness, check that the brain is loaded. In
short:

```bash
cd "/path/to/your vault"
git clone https://github.com/kevines-ods/OBSIA
cd OBSIA
python3 scripts/installer.py --sonder     # what the machine has, writes nothing
python3 scripts/installer.py --appliquer  # keeps the modules, writes ../AGENTS.md
```

Then launch the harness **from the vault root**, where the installer put
`AGENTS.md`. For a harness that does not read that file, the same text is
produced, from `OBSIA/`, by
`python3 scripts/generer_prompt.py -o prompt-systeme.md --mcp`, to be given as
the system prompt; `--mcp` adds a skeleton MCP server configuration.

## Modular installation

The vault is a **catalogue**, not a delivery. Everything is declared; nothing
forces you to keep it all. A machine without Docker has no use for the skills
that drive containers: they would take up context, offer themselves at the
wrong moment, and fail where they should have stayed silent.

A **module** (`IA/system/modules/<name>.md`) groups what only makes sense
together, and every agent, skill, MCP and task declares its own. The generated
index `IA/system/modules-index.md` lists them all — including the ones you did
not keep, because a catalogue that hides its missing entries is no longer a
catalogue.

```bash
python3 scripts/installer.py --sonder              # detection, probe verdicts
python3 scripts/installer.py                       # preview, writes nothing
python3 scripts/installer.py --appliquer           # writes the profile, in place
python3 scripts/installer.py --installer ~/vault/OBSIA --appliquer
python3 scripts/installer.py --tout --appliquer    # back to the full catalogue
```

The installer **probes, then asks**: it sees that `docker` is installed, it
does not know whether you want to manage containers. The probe suggests a
default, the question decides. Only four probe forms — `commande:`,
`fichier:`, `distribution:`, `parent:` — and none that runs an arbitrary
command or opens the network.

Two modes:

- **in place** — nothing is moved or deleted, only the **non-versioned** files
  are reduced to the profile (the system prompt and `AGENTS.md`). The indexes
  are versioned and stay at the full catalogue;
- **copy** (`--installer TARGET`) — only the kept files land in the target, and
  agent declarations are trimmed there to stay consistent.

Back from a profile to the full catalogue: `python3 scripts/installer.py --tout
--appliquer`.

The profile lives in `obsia.local.yml`, at the root, **not versioned**: it
describes this machine, not the vault. Without a profile, the whole catalogue
is active — that is the state of the distribution repository and the one CI
checks against. It only reduces what is not versioned (system prompt,
`AGENTS.md`): versioned indexes always show the whole catalogue, otherwise CI
would see a stale index. Full rules in §13 of `IA/system/VAULT-CONTRACT.md`.

## Checking the vault

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
--appliquer` arms it for you (§13):

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
kind: skill              # agent | skill | mcp | tâche | contract
name: skill-name         # lowercase, hyphens, same as the file name
description: One line — what and when.
type: core               # skills only: core | outil
read_only: true
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
---
```

Lists are written with hyphens, one entry per line. `skills: a, b` is a
string, not a list.

This frontmatter is the boundary between the tool and any program reading it.
`schema` lets it evolve without breaking existing consumers.

## Rules

They live in `IA/system/VAULT-CONTRACT.md`, which is authoritative. In short:

- The vault is read-only for agents. Changes go through Git patches submitted
  for review.
- No deletion without prior archiving — and archiving is the memory repository's
  Git history (§2).
- A preview is mandatory before any action touching several files.
- Generated files — `sommaire.md` (in the parent vault), `agents-index.md`,
  `skills-index.md`, `taches-index.md`, `IA/README.md` — are regenerated by
  script, never edited by hand. If an index contradicts a frontmatter, the
  frontmatter wins.
- An agent and a skill are two distinct things. An agent decides; a skill
  describes a way of doing.

## Secrets

The repository is public. Never let in: keys, tokens, passwords, private IP
addresses, internal host names.

Real inventories (machines, LLM instances) live outside the repository. Only
`*.example.yml` templates are versioned.

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
parent vault, pushed to the NAS (§7.1). It is not published.

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
