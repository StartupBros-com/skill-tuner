sshpass -e ssh -o BatchMode=no -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -o PreferredAuthentications=password -o PubkeyAuthentication=no -e OPS_PW scp -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -o PreferredAuthentications=password -o PubkeyAuthentication=no ./report.csv ops@198.51.100.9:/home/ops/incoming/

Corrected, minimal form (scp only, no ssh wrapper needed):

SSHPASS="$OPS_PW" sshpass -e scp -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -o PreferredAuthentications=password -o PubkeyAuthentication=no ./report.csv ops@198.51.100.9:/home/ops/incoming/