#!/bin/bash
set -eou pipefail

# Remove unneeded programs
systemctl stop wpa_supplicant
systemctl disable wpa_supplicant

# Replace configs
install files/config.txt -D "${ROOTFS_DIR}/boot/config.txt"
install files/keyboard -D "${ROOTFS_DIR}/etc/default/keyboard"

