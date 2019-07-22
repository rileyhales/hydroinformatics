#!/usr/bin/env bash
conda create -n tethys -c tethysplatform/label/dev -c tethysplatform -c conda-forge tethysplatform
cd
if [[ "$OSTYPE" == "darwin"* ]]; then
	. .bash_profile
elif [[ "$OSTYPE" == "linux-gnu" ]]; then
	. .bashrc
fi
conda activate tethys
tethys gen settings
tethys db configure