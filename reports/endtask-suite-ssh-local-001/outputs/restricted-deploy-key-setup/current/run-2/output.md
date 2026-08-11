1. Generate a brand-new, dedicated, passphrase-free Ed25519 key:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/runner_backup_ed25519 -N "" -C "runner-automation-backup"
chmod 600 ~/.ssh/runner_backup_ed25519
chmod 644 ~/.ssh/runner_backup_ed25519.pub
```

2. Install the public key on 203.0.113.99 for user `runner`, locked to *only* run `/usr/local/bin/backup.sh` — using `command=` to force that program and `restrict` to strip pty/port-forward/agent-forward/X11/user-rc, so an interactive session can't be used to run anything else. Bootstrap the connection non-interactively with the existing password (kept out of the command line / history via the `SSHPASS` env var, per the ssh-local skill's password-auth recipe):

```bash
SSHPASS="$BOOTSTRAP_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=accept-new \
    -o ConnectTimeout=10 -o PreferredAuthentications=password -o PubkeyAuthentication=no \
    runner@203.0.113.99 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && umask 077 && \
    printf '%s\n' 'command=\"/usr/local/bin/backup.sh\",restrict $(cat ~/.ssh/runner_backup_ed25519.pub)' >> ~/.ssh/authorized_keys && \
    chmod 600 ~/.ssh/authorized_keys"
```

3. Verify the key works, non-interactively (the forced `command=` runs `backup.sh` regardless of what's passed, so this both confirms the key authenticates and confirms the restriction is enforced):

```bash
ssh -o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new \
    -i ~/.ssh/runner_backup_ed25519 runner@203.0.113.99 'true'
```