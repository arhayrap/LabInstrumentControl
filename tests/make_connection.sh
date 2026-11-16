# 192.168.0.174

sudo nmcli con add \
  type ethernet \
  con-name Scope1 \
  ifname enp6s0 \
  ipv4.method manual \
  ipv4.addresses 192.168.10.1/24 \
  ipv4.never-default yes \
  ipv6.method disabled

# 192.168.0.1

sudo nmcli con add \
  type ethernet \
  con-name Scope2 \
  ifname enp0s25 \
  ipv4.method manual \
  ipv4.addresses 192.168.20.1/24 \
  ipv4.never-default yes \
  ipv6.method disabled
