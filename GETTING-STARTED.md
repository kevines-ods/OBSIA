# Getting started

**English** | [Français](DEMARRAGE.md)

From zero to a first exchange with an OBSIA agent, in five steps. The details
of each rule live in `IA/system/VAULT-CONTRACT.md` (the core) and its
annexes in `IA/system/contrat/` (in French); this guide only
gives the order of the steps.

**Requirements**: `git` and Python 3 — standard library only, nothing to
install. Obsidian is recommended, not required.

## 1. Clone into your vault

OBSIA is cloned **at the root** of your Obsidian vault, next to your notes —
nowhere else, and not in a subfolder:

```bash
cd "/path/to/your vault"   # replace with yours
git clone https://github.com/kevines-ods/OBSIA
```

You get `<vault>/OBSIA/` — the repository writes `Mon coffre/` for the root of
your vault, whatever its real name. Then open Obsidian on **the whole vault**,
not on `OBSIA/` alone: backlinks resolve at that level.

No vault yet? An empty folder will do; the knowledge folders (`0-SAVOIRS/`,
`0-EN-VRAC/`…) are created when you need them (§7.1 of the contract).

## 2. See what the machine has

```bash
cd OBSIA
python3 scripts/installer.py --sonder
```

Nothing is written. The installer detects what is installed (`docker`,
`systemctl`, Proxmox…) and infers the modules it will offer.

## 3. Install

```bash
python3 scripts/installer.py              # preview and questions, writes nothing
python3 scripts/installer.py --appliquer  # apply
```

The installer asks, module by module, what you want to keep. At the end:

- `OBSIA/obsia.local.yml` — your profile, not versioned;
- the versioned indexes in `IA/system/` and `IA/README.md` — untouched, at the
  full catalogue: they do not depend on the machine;
- **`Mon coffre/AGENTS.md`** — OBSIA's brain, at the vault root, where
  harnesses look for it. Do not edit it: it is regenerated;
- **`Mon coffre/0-MEMOIRES/`** and **`Mon coffre/0-PERSONNELS/profil-utilisateur.md`**
  — the vault's memory, created if missing (§6, §7.1). Never overwritten
  afterwards: whatever is already there stays.

Changed your mind: run the same command again. Start over:
`python3 scripts/installer.py --tout --appliquer` — which deletes the profile:
without a profile, the whole catalogue is active.

## 4. Launch a harness from the vault root

**Always from `Mon coffre/`**, never from `OBSIA/`: that is where `AGENTS.md`
is, and where the agent reaches your notes from.

```bash
cd ..                          # from OBSIA/, go up to the vault root
```

| Harness | What it reads on its own | Worth knowing |
| --- | --- | --- |
| Claude Code | `CLAUDE.md` if it finds one, in the folder or **above**; otherwise `AGENTS.md` | one **or** the other, never both. To load the full contract, create `Mon coffre/CLAUDE.md` containing the line `@OBSIA/CLAUDE.md`: it will read that file **instead of** `AGENTS.md` |
| OpenCode | `AGENTS.md` | add the contract under `instructions` — see its card |
| Codex | `AGENTS.md` | 32 KiB cap: a full vault uses three quarters of it |
| Goose | `AGENTS.md` | the `developer` extension must stay enabled |
| DeepSeek Harness | `AGENTS.md` and `CLAUDE.md`, from `~/.dsh/` then from each folder down to the working directory | the `@` lines of `CLAUDE.md` arrive raw, with no effect |
| AionUi (Aion CLI engine) | `AGENTS.md`, not `CLAUDE.md` | the assistant's rule must make it read the contract — see its card |

Each harness has its card in `IA/system/adaptateurs-harness/`: it says where
to write the configuration — MCP servers, secrets, per-agent restrictions.
That configuration lives **outside the repository**: no key ever enters
`OBSIA/`.

## 5. Check that the brain is loaded

Ask the agent:

> Which agents do you know, and where do the knowledge notes live?

It should name the agents of `IA/system/agents-index.md` and the `0-SAVOIRS/`
folder. If it answers generically, its instructions were not read: check that
`AGENTS.md` exists at the vault root and that the harness was launched from
there. With Claude Code, also look for a `CLAUDE.md` above the vault (up to
your home folder): it would take precedence over `AGENTS.md`.

The agents answer in French by default; ask them to switch language if you
prefer.

## Next

The repository scripts are run **from `OBSIA/`** (`cd OBSIA`); only the
harness is launched from the root.

- **After adding or changing a skill**: rerun the installer to regenerate
  `AGENTS.md` — `python3 scripts/installer.py --rejouer --appliquer` reuses
  your profile without asking the questions again.
- **Before proposing a change to the repository**:
  `python3 scripts/verifier_coffre.py`. The tool (`OBSIA/`) and the memory (the
  vault root) are **two distinct Git repositories** (§7.1) — one ships by pull
  request, the other is committed in place.
- **Going further**: [`README.md`](README.md) for the architecture, the
  contract for the rules, `IA/system/agents-index.md` to know which agent to
  talk to.
