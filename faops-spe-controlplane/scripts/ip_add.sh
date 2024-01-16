#
# Script to add secondary private ip address to desired interface
#
if [ "$#" -ne 5 ]; then
  echo "Usage: $0 <phys_dev> <seq_num> <private_ip> <subnet_cidr> <subnet_netmask>"
  exit 1
fi

device=${1}
seq_num=${2}
ip=${3}
subnet=${4}
netmask=${5}

before=$(ip addr show)
echo "Before IP ADD"
echo "########################################################"
echo "${before}"
echo "########################################################"
subnet_len=$(echo $subnet | cut -f2 -d/)
echo "Executing :ip addr add ${ip}/${subnet_len} dev ${device} label ${device}:${seq_num}"

ip addr add ${ip}/${subnet_len} dev ${device} label ${device}:${seq_num}

cat > /etc/sysconfig/network-scripts/ifcfg-${device}:${seq_num}<<- EOM
DEVICE="${device}:${seq_num}"
BOOTPROTO=static
IPADDR=${ip}
NETMASK=${netmask}
ONBOOT=yes
EOM
chmod 644 /etc/sysconfig/network-scripts/ifcfg-${device}:${seq_num}

after=$(ip addr show)
echo "After IP ADD"
echo "########################################################"
echo "${after}"
echo "########################################################"


