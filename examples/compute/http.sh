#!/bin/bash
set -eou pipefail
sudo apt-get update -y
sudo apt-get install -y python3
mkdir ~/dir
cd ~/dir
echo foo > bar.txt
echo healthy > health
(nohup python3 -m http.server 8080 &> server.log </dev/null &)
