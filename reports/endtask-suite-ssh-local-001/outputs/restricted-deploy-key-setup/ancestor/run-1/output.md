# 1. Generate a dedicated, passphrase-free Ed25519 key for the automation account
ssh-keygen -t ed25519 -f ~/.ssh/runner_backup_ed25519 -N "" -C "runner-backup-automation"

# 2. Build a restricted authorized_keys entry that forces backup.sh no matter what
#    the client requests, and strips pty/forwarding so an interactive session can't
#    be used to escape the forced command.
PUBKEY=$(cat ~/.ssh/runner_backup_ed25519.pub)
RESTRICTED_LINE="command=\"/usr/local/bin/backup.sh\",no-agent-forwarding,no-port-forwarding,no-pty,no-user-rc,no-X11-forwarding $PUBKEY"

# 3. Install that entry on the remote host for user "runner", using whatever
#    admin/existing access you already have (here: an existing admin key),
#    non-interactively per the ssh-local safety recipe.
ssh -o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new \
    -i ~/.ssh/id_ed25519 runner@203.0.113.99 \
    "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$RESTRICTED_LINE' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

# 4. Verify the new key works, non-interactively. The forced command overrides
#    whatever is requested, so the request itself can be trivial.
timeout 30 ssh -o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new \
    -i ~/.ssh/runner_backup_ed25519 runner@203.0.113.99 'true'; echo "exit: $?"