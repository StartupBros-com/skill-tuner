# 1. Generate a dedicated, passphrase-free Ed25519 key for the automation account
ssh-keygen -t ed25519 -f ~/.ssh/runner_backup -N "" -C "runner-automation-backup"
chmod 600 ~/.ssh/runner_backup
chmod 644 ~/.ssh/runner_backup.pub

# 2. Install the public key on 203.0.113.99 for user "runner", restricted to ONLY
#    ever execute /usr/local/bin/backup.sh (forced command + "restrict" strips pty,
#    port/X11/agent forwarding, and user-rc, so no other action is possible even
#    interactively). Run via existing admin access to the host, non-interactively:
ssh -o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new \
    runner@203.0.113.99 \
    "umask 077; mkdir -p ~/.ssh && printf 'restrict,command=\"/usr/local/bin/backup.sh\" %s\n' \"$(cat ~/.ssh/runner_backup.pub)\" >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"

# 3. Verify the key works and is locked to backup.sh (any requested command is
#    ignored/overridden by the forced command, so this both confirms auth works
#    and confirms the restriction is enforced):
ssh -o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new \
    -i ~/.ssh/runner_backup runner@203.0.113.99 'echo this-should-be-ignored'