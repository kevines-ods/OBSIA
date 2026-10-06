# Getting started

**English** | [Français](DEMARRAGE.md)

From zero to a first conversation with an OBSIA agent, in five steps. All you
need is `git` and Python 3: nothing else to install. Obsidian is handy, but not
required.

## 1. Create your vault and put OBSIA in it

Your **vault** is the folder that will hold your notes and your memory. OBSIA
goes **directly inside it**, not in a subfolder.

No vault yet? Create it, then put OBSIA inside:

```bash
mkdir -p ~/"Mon coffre" && cd ~/"Mon coffre"
git clone https://github.com/kevines-ods/OBSIA
```

Already have a vault (an Obsidian vault, for instance)? Go into it, then clone:

```bash
cd "/path/to/your vault"
git clone https://github.com/kevines-ods/OBSIA
```

Do not clone OBSIA directly into your home folder: the installer will
refuse, without writing anything.

The rest of this guide calls this folder `Mon coffre/`, whatever its real name.
If you use Obsidian, open it on the whole vault, not on `OBSIA/` alone. The note
folders (`0-SAVOIRS/`, `0-EN-VRAC/`…) are created as you go.

## 2. See what your machine already has

```bash
cd OBSIA
python3 scripts/installer.py --sonder
```

This command writes nothing. The installer looks at what is already installed
(Docker, systemd, Proxmox…) to offer you the right choices at the next step.

## 3. Install

```bash
python3 scripts/installer.py              # asks the questions, shows what will be done, writes nothing
python3 scripts/installer.py --appliquer  # installs
```

The installer asks one question per module ("Veux-tu que les agents
sachent… ?" — the questions are in French). Answer according to what you want
the agents to be able to do, even if the tool is not installed on your machine
yet. At the end, it has created:

- **`Mon coffre/AGENTS.md`**: the instructions a harness reads at start-up, at
  the root of the vault. Do not edit it by hand: it is rebuilt at every
  installation;
- **`Mon coffre/0-PERSONNELS/profil-utilisateur.md`** and
  **`Mon coffre/0-MEMOIRES/`**: the start of your memory. Whatever is already
  there is never overwritten;
- **`OBSIA/obsia.local.yml`**: your answers, specific to your machine.

Changed your mind? Run the same command again. To go back to the full
catalogue: `python3 scripts/installer.py --tout --appliquer`.

## 4. Start your harness from the vault

Always start it **from `Mon coffre/`**, never from `OBSIA/`: that is where
`AGENTS.md` sits, and from there the agents reach your notes.

```bash
cd ..        # from OBSIA/, go back up into the vault
```

| Harness | What else to do |
| --- | --- |
| Claude Code | create `Mon coffre/CLAUDE.md` containing the single line `@OBSIA/CLAUDE.md` (Claude Code reads this file instead of `AGENTS.md`) |
| OpenCode | create `opencode.json`: copy-paste block in its sheet |
| Codex | nothing. It reads `AGENTS.md` (size limit: a full catalogue uses a little over three quarters of it) |
| Goose | keep the `developer` extension active |
| DeepSeek Harness | nothing. It reads `AGENTS.md` |
| AionUi | make the assistant's rule load the contract (see its sheet) |

Each harness has its sheet in `IA/system/adaptateurs-harness/` (in French). It
also explains how to plug in the tools (MCP) and where to put your keys:
**never in `OBSIA/`**.

## 5. Check that OBSIA is loaded

Ask the agent these two questions:

1. "Which agents do you know, and where do the knowledge notes live?"
   It must name OBSIA's agents (assistant, administrateur, batisseur…) and the
   `0-SAVOIRS/` folder.
2. "What do you do if a skill you need cannot be found?"
   It must answer that it tells you, not that it improvises. That is the
   contract's rule "Un échec se dit" (a failure is said).

If it answers vaguely, it has not read its instructions. Check that
`AGENTS.md` exists in `Mon coffre/` and that you started the harness from that
folder. With Claude Code, also check that no other `CLAUDE.md` sits in a folder
above the vault: it would take priority.

## Next

- **Talk to the `assistant` agent** to begin: it files your notes, keeps your
  memory and points you to the right agent. The list of agents and their roles
  is in `IA/system/agents-index.md`.
- **After adding or changing a skill**, rebuild `AGENTS.md` without answering
  the questions again: `python3 scripts/installer.py --rejouer --appliquer`
  (from `OBSIA/`).
- **To contribute to OBSIA**: `python3 scripts/verifier_coffre.py` (from
  `OBSIA/`) before proposing a change. OBSIA and your vault each have their own Git history: a
  change to OBSIA is proposed by pull request, your memory is committed
  directly.
- **To understand how it all works**: `README.md`, then the contract
  (`IA/system/VAULT-CONTRACT.md`, in French).
