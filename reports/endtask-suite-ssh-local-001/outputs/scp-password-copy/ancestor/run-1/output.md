sshpass -e ssh -o BatchMode=no -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -o PreferredAuthentications=password -o PubkeyAuthentication=no ops@198.51.100.9 true

SSHPASS="$OPS_PW" sshpass -e scp -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -o PreferredAuthentications=password -o PubkeyAuthentication=no ./report.csv ops@198.51.100.9:/home/ops/incoming/