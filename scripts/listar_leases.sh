
#!/bin/bash

LEASE_FILE="/var/lib/dhcp/dhcpd.leases"

echo -e "IP\t\tMAC Address\t\tHostname\tExpiração"
echo "-----------------------------------------------------------------------------------------"

awk '
/^lease/ { ip=$2; mac="N/A"; hostname="N/A"; ends="N/A"; inside=1 }
/hardware ethernet/ { mac=$3; gsub(/;/, "", mac) }
/client-hostname/ { hostname=$2; gsub(/[";]/, "", hostname) }
/ends/ { ends=$3" "$4; gsub(/;/, "", ends) }
/}/ {
    if (inside) {
        printf "%-20s %-20s %-20s %-20s\n", ip, mac, hostname, ends
        inside=0
    }
}
' "$LEASE_FILE"
