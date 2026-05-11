#!/bin/bash
echo 'KERNEL=="hidraw*", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="0ce6", MODE="0666"' | sudo tee /etc/udev/rules.d/99-dualsense.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
