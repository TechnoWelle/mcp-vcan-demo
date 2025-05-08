#!/bin/bash
# This script sets up a virtual CAN interface (vcan) on Linux.

sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0