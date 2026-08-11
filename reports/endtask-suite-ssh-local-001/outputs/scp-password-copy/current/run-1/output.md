sshpass -e scp -o BatchMode=no -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -o PreferredAuthentications=password -o PubkeyAuthentication=no ./report.csv ops@198.51.100.9:/home/ops/incoming/

(Run with `SSHPASS="$OPS_PW"` already set in the environment; `sshpass -e` reads the password from `SSHPASS`, never pass it via `-p` since that leaks in `ps`.)