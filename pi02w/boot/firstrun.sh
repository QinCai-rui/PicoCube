#!/bin/bash

set +e

CURRENT_HOSTNAME=`cat /etc/hostname | tr -d " \t\n\r"`
if [ -f /usr/lib/raspberrypi-sys-mods/imager_custom ]; then
   /usr/lib/raspberrypi-sys-mods/imager_custom set_hostname pi02w-cube
else
   echo pi02w-cube >/etc/hostname
   sed -i "s/127.0.1.1.*$CURRENT_HOSTNAME/127.0.1.1\tpi02w-cube/g" /etc/hosts
fi
FIRSTUSER=`getent passwd 1000 | cut -d: -f1`
FIRSTUSERHOME=`getent passwd 1000 | cut -d: -f6`
if [ -f /usr/lib/raspberrypi-sys-mods/imager_custom ]; then
   /usr/lib/raspberrypi-sys-mods/imager_custom enable_ssh
else
   systemctl enable ssh
fi
if [ -f /usr/lib/userconf-pi/userconf ]; then
   /usr/lib/userconf-pi/userconf 'qincai' '$5$ttiLk7CFp5$RvZrLbzrE8A3cttMI6wVC7QD9nr36IgoToVgd5O7dE3'
else
   echo "$FIRSTUSER:"'$5$ttiLk7CFp5$RvZrLbzrE8A3cttMI6wVC7QD9nr36IgoToVgd5O7dE3' | chpasswd -e
   if [ "$FIRSTUSER" != "qincai" ]; then
      usermod -l "qincai" "$FIRSTUSER"
      usermod -m -d "/home/qincai" "qincai"
      groupmod -n "qincai" "$FIRSTUSER"
      if grep -q "^autologin-user=" /etc/lightdm/lightdm.conf ; then
         sed /etc/lightdm/lightdm.conf -i -e "s/^autologin-user=.*/autologin-user=qincai/"
      fi
      if [ -f /etc/systemd/system/getty@tty1.service.d/autologin.conf ]; then
         sed /etc/systemd/system/getty@tty1.service.d/autologin.conf -i -e "s/$FIRSTUSER/qincai/"
      fi
      if [ -f /etc/sudoers.d/010_pi-nopasswd ]; then
         sed -i "s/^$FIRSTUSER /qincai /" /etc/sudoers.d/010_pi-nopasswd
      fi
   fi
fi
if [ -f /usr/lib/raspberrypi-sys-mods/imager_custom ]; then
   /usr/lib/raspberrypi-sys-mods/imager_custom set_wlan 'ORBI76-Guest' '673b98f6360f4e6c015d12ed4dc35928f9f34fcbc7f1850b2634540807417ac3' 'NZ'
else
cat >/etc/wpa_supplicant/wpa_supplicant.conf <<'WPAEOF'
country=NZ
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
ap_scan=1

update_config=1
network={
	ssid="ORBI76-Guest"
	psk=673b98f6360f4e6c015d12ed4dc35928f9f34fcbc7f1850b2634540807417ac3
}

WPAEOF
   chmod 600 /etc/wpa_supplicant/wpa_supplicant.conf
   rfkill unblock wifi
   for filename in /var/lib/systemd/rfkill/*:wlan ; do
       echo 0 > $filename
   done
fi
if [ -f /usr/lib/raspberrypi-sys-mods/imager_custom ]; then
   /usr/lib/raspberrypi-sys-mods/imager_custom set_keymap 'us'
   /usr/lib/raspberrypi-sys-mods/imager_custom set_timezone 'Pacific/Auckland'
else
   rm -f /etc/localtime
   echo "Pacific/Auckland" >/etc/timezone
   dpkg-reconfigure -f noninteractive tzdata
cat >/etc/default/keyboard <<'KBEOF'
XKBMODEL="pc105"
XKBLAYOUT="us"
XKBVARIANT=""
XKBOPTIONS=""

KBEOF
   dpkg-reconfigure -f noninteractive keyboard-configuration
fi

# Remove the rule setting gadget devices to be unmanaged
cp /usr/lib/udev/rules.d/85-nm-unmanaged.rules /etc/udev/rules.d/85-nm-unmanaged.rules
sed 's/^[^#]*gadget/#\ &/' -i /etc/udev/rules.d/85-nm-unmanaged.rules

# Create a NetworkManager connection file with a static IP
CONNFILE=/etc/NetworkManager/system-connections/usb0-static.nmconnection
UUID=$(uuid -v4)
cat <<- EOF >${CONNFILE}
	[connection]
	id=usb0-static
	uuid=${UUID}
	type=ethernet
	interface-name=usb0
	autoconnect-priority=100
	[ethernet]
	[ipv4]
	addresses=192.168.155.1/24
	gateway=192.168.155.1
	method=manual
	[ipv6]
	addr-gen-mode=default
	method=ignore
	[proxy]
	EOF

# Set correct permissions for the connection file
chmod 600 ${CONNFILE}

# Restart NetworkManager to apply the new connection
systemctl restart NetworkManager

# Enable the rc.local service
if [ -f /usr/lib/systemd/system/rc-local.service ]; then
   systemctl enable rc-local.service
   systemctl start rc-local.service
else
   echo "rc-local.service not found, skipping rc.local enablement."
fi

# Add shebang to /etc/rc.local file if it doesn't exist
if [ ! -f /etc/rc.local ]; then
   echo -e "#!/bin/sh\nexit 0" > /etc/rc.local
   chmod +x /etc/rc.local
else
   if ! grep -q "^#!/bin/sh" /etc/rc.local; then
      sed -i '1i#!/bin/sh' /etc/rc.local
   fi
fi

#rm -f /boot/firstrun.sh
sed -i 's| systemd.run.*||g' /boot/cmdline.txt

exit 0
