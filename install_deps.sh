#!/bin/bash

set -eEuxo pipefail

apt-get update
apt-get install -y \
    python3-usb
