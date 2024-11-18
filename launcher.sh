#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /
cd home/lucienfradet/classification_de_feuille/
sudo python3 python_camera_with_runner.py modelfile_download.eim
cd /
