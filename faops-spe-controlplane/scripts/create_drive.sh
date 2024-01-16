#!/bin/bash

#echo $PRIVATE_KEY   is PRIVATE_KEY
#echo $REMOTE_HOST   is REMOTE_HOST
#echo $IQN           is IQN
#echo $IPV4          is IPV4
#echo $PORT          is PORT
#echo $MOUNT         is MOUNT

echo "Waiting for remote host to be up..."
sleep 300
chmod 600 ${PRIVATE_KEY}
ssh -i "${PRIVATE_KEY}" -o "StrictHostKeyChecking=no" -o User=opc -o ProxyCommand="ssh -i ${BASTION_PRIVATE_KEY} -o StrictHostKeyChecking=no ${BASTION_USER}@${BASTION_HOST} -W %h:%p %r" "${REMOTE_HOST}" "bash

sudo -s bash -c 'iscsiadm -m node -o new -T ${IQN} -p ${IPV4}:${PORT}'
sudo -s bash -c 'iscsiadm -m node -o update -T ${IQN} -n node.startup -v automatic '
sudo -s bash -c 'iscsiadm -m node -T ${IQN} -p ${IPV4}:${PORT} -l '
sudo -s bash -c 'mkfs.ext4 -F /dev/sdb'
sudo -s bash -c 'mkdir -p ${MOUNT}'
sudo -s bash -c 'mount -t ext4 /dev/sdb ${MOUNT}'
echo '/dev/sdb  ${MOUNT} ext4 defaults,noatime,_netdev,nofail    0   2' | sudo tee --append /etc/fstab > /dev/null"

