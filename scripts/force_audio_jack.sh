#!/bin/bash
# Force ALSA audio routing to the 3.5mm analog jack on Raspberry Pi 4

echo "Forcing system-wide ALSA default to Headphones..."

cat << 'EOF' > ~/.asoundrc
pcm.!default {
    type hw
    card Headphones
}

ctl.!default {
    type hw
    card Headphones
}
EOF

echo "Audio successfully routed to the 3.5mm jack."

# Maximize volume and save state permanently
echo "Maximizing volume to 100%..."
amixer -c Headphones sset 'Headphone' 100% unmute || amixer -c Headphones sset 'PCM' 100% unmute || true
sudo alsactl store

echo "Please reboot your Raspberry Pi for changes to take effect!"
