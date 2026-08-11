# 1. Generate a dedicated, passphrase-free Ed25519 key for the automation account
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519_runner_backup -C "runner@automation-backup"

# 2. Build a restricted authorized_keys entry: command= forces every session opened
#    with this key to run ONLY /usr/local/bin/backup.sh (whatever command the client
#    requests is ignored/replaced); restrict disables pty, port/agent/X11 forwarding
#    and ~/.ssh/rc, so an interactive login or tunnel attempt can't be used for anything else.
echo "command=\"/usr/local/bin/backup.sh\",restrict $(cat ~/.ssh/id_ed25519_runner_backup.pub)" > /tmp/runner_backup_key.pub

# 3. Install it on the remote host (one-time interactive step, using whatever access
#    you currently have to the runner account — password or an existing admin key)
ssh runner@203.0.113.99 'umask 077; mkdir -p ~/.ssh; touch ~/.ssh/authorized_keys; chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys; cat >> ~/.ssh/authorized_keys' < /tmp/runner_backup_key.pub

# 4. Remove the local staging file
rm /tmp/runner_backup_key.pub

# 5. Non-interactive verification: connect with the new key and request an arbitrary
#    command ("true") — if the restriction is working, the server ignores it and runs
#    backup.sh instead, and the call still returns without hanging or prompting.
ssh -o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new -i ~/.ssh/id_ed25519_runner_backup runner@203.0.113.99 true