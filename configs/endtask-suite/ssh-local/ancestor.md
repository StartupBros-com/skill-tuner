---
name: ssh-local
description: >-
  SSH remote access - connections, tunnels, keys, file transfers, plus agent-safe
  NON-INTERACTIVE patterns (never hang on a prompt) and this machine's own host
  inventory (mac-mini). Use when connecting to servers, ssh/scp/rsync, port
  forwarding, tunnels, or an agent needs to run a remote command headless.
---

<!--
  LOCAL FORK: not managed by jsm; do not expect `jsm install-all` to preserve it.
  Origin: forked 2026-07-06 from jsm upstream `ssh` (Jeffrey Emanuel v1).
  The base name `ssh` is in retired-skills.txt so skills-localize.sh keeps the pristine
  upstream uninstalled and deploys THIS fork instead (name `ssh-local` avoids the
  retire-then-deploy collision). Localization adds the two things upstream lacked for an
  agent caller: (1) the non-interactive safety-flag recipe so agent-driven ssh never hangs
  on a password/host-key prompt, and (2) a known-hosts section for this machine's own boxes.
  Everything else (jump hosts, port forwards, config, multiplexing, agent) is upstream v1.
-->

<!-- TOC: Non-Interactive (agents) | Known Hosts | Quick Start | Common Workflows | Essential Commands | Config | AGENTS.md Blurb | References -->

# SSH: Secure Remote Access (local fork)

> **Core Capability:** Secure shell connections, key management, tunneling, and file transfers.

---

## Non-Interactive ssh (agents: never hang)

When an **agent** drives ssh with no human at the terminal, a bare `ssh` can hang forever on a
password prompt, a host-key confirmation, or a stalled connection. Always pin these flags:

```bash
# Key auth, non-interactive: fail fast instead of prompting
ssh -o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=accept-new -i ~/.ssh/id_ed25519 user@host 'cmd'

# Password auth, non-interactive (needs `sshpass`; keep the secret OUT of scripts/history):
SSHPASS="$secret" sshpass -e ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 \
    -o PreferredAuthentications=password -o PubkeyAuthentication=no user@host 'cmd'
#   pass the password via the SSHPASS env var (-e), never `-p 'secret'` (it leaks in `ps`).
```

- `BatchMode=yes`: never prompt, error out instead, so the agent can detect the failure and retry.
- `IdentitiesOnly=yes`: use only the `-i` key, don't cycle every loaded agent identity.
- `ConnectTimeout=10`: bounded wait, no infinite hang on an unreachable host.
- `StrictHostKeyChecking=accept-new`: trust a NEW host automatically, still refuse a CHANGED key.
- Wrap the whole call in a `timeout` at the call site too (`timeout 30 ssh ...`).

## Known Hosts (this machine)

Boxes reachable from this WSL2 install. **Secrets are NOT stored here**, auth method only.

| Host | Reach it | User | Auth | Notes |
|------|----------|------|------|-------|
| **mac-mini** | `ssh mac-mini` (Tailscale MagicDNS), or `100.94.108.13` | `mac-mini` | password (in the secret store, not inline) | Headless macOS 15, auto-login GUI console, Screen Sharing + ARD on. Chrome/Brave present. |

```bash
# mac-mini, non-interactive (password supplied via SSHPASS env, never inline):
SSHPASS="$secret" sshpass -e ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 \
    -o PreferredAuthentications=password -o PubkeyAuthentication=no mac-mini 'hostname'
```

---

## Quick Start

```bash
# Connect to server
ssh user@hostname

# Connect with specific key
ssh -i ~/.ssh/my_key user@hostname

# Run remote command
ssh user@host "cd /app && git status"

# Copy file to remote
scp local.txt user@host:/remote/path/

# Sync directory (preferred over scp)
rsync -avzP ./local/ user@host:/remote/
```

---

## Common Workflows

### Connect Through Jump Host

```bash
# Single jump (bastion)
ssh -J jumphost user@internal-server

# Multiple jumps
ssh -J jump1,jump2 user@internal-server
```

### Local Port Forward (access remote service locally)

```bash
# Access remote:80 via localhost:8080
ssh -L 8080:localhost:80 user@host

# Access db-server:5432 via localhost:5432 through jumphost
ssh -L 5432:db-server:5432 user@jumphost
```

### Generate and Deploy Key

```bash
# Generate Ed25519 key (recommended)
ssh-keygen -t ed25519 -C "you@example.com"

# Copy public key to server
ssh-copy-id user@host
```

---

## Essential Commands

| Task | Command |
|------|---------|
| Connect | `ssh user@host` |
| Connect on port | `ssh -p 2222 user@host` |
| Connect with key | `ssh -i ~/.ssh/key user@host` |
| Run remote command | `ssh user@host "command"` |
| Interactive remote | `ssh -t user@host "htop"` |
| Copy to remote | `scp file.txt user@host:/path/` |
| Copy from remote | `scp user@host:/path/file.txt ./` |
| Sync to remote | `rsync -avzP ./local/ user@host:/remote/` |
| Local forward | `ssh -L local:remote:port user@host` |
| Remote forward | `ssh -R remote:local:port user@host` |
| SOCKS proxy | `ssh -D 1080 user@host` |
| Jump host | `ssh -J bastion user@internal` |
| Generate key | `ssh-keygen -t ed25519` |
| Copy key to server | `ssh-copy-id user@host` |
| Debug connection | `ssh -vvv user@host` |

---

## SSH Config

Location: `~/.ssh/config`

```
Host myserver
    HostName 192.168.1.100
    User deploy
    Port 22
    IdentityFile ~/.ssh/myserver_key
    ForwardAgent yes

Host internal
    HostName 10.0.0.50
    User deploy
    ProxyJump bastion
```

Then connect with just: `ssh myserver`

### Connection Multiplexing (faster reconnects)

```
Host *
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600
```

```bash
mkdir -p ~/.ssh/sockets
```

---

## SSH Agent

```bash
# Start agent
eval "$(ssh-agent -s)"

# Add key
ssh-add ~/.ssh/id_ed25519

# Add with macOS keychain
ssh-add --apple-use-keychain ~/.ssh/id_ed25519

# List loaded keys
ssh-add -l
```

---

## Security Tips

- Use Ed25519 keys (faster, more secure than RSA)
- Set `PasswordAuthentication no` on servers
- Keep keys encrypted with passphrases
- Use `ssh-agent` to avoid typing passphrase repeatedly
- Restrict key usage with `command=` in authorized_keys

---

## AGENTS.md Blurb

Copy this to your project's AGENTS.md:

```markdown
### SSH Access

SSH is configured for these servers:

- **Production:** `ssh prod` (via ~/.ssh/config)
- **Staging:** `ssh staging`

Common operations:

\`\`\`bash
ssh prod "cd /app && git status"      # Check deploy status
rsync -avzP ./dist/ prod:/app/dist/   # Sync files
ssh -L 5432:localhost:5432 prod       # DB tunnel
\`\`\`

Keys: `~/.ssh/id_ed25519` (add with `ssh-add`)
```

---

## References

| Topic | Reference |
|-------|-----------|
| Full command reference | [COMMANDS.md](references/COMMANDS.md) |
| Port forwarding details | [TUNNELS.md](references/TUNNELS.md) |
| Key management | [KEYS.md](references/KEYS.md) |
