#!/usr/bin/env bash

# install the tethys repo to a conda environment
conda create -n tethys -c tethysplatform/label/dev -c tethysplatform -c conda-forge tethysplatform

# assign aliases to run the tethys environment
if [[ "$OSTYPE" == "darwin"* ]]; then
	BASHPROFILE=".bash_profile"
elif [[ "$OSTYPE" == "linux-gnu" ]]; then
	BASHPROFILE=".bashrc"
fi
echo "# Tethys Platform" >> ~/${BASHPROFILE}
echo "alias t='conda activate tethys'" >> ~/${BASHPROFILE}
echo "alias tms='tethys manage start'" >> ~/${BASHPROFILE}

# initialize tethys settings and databases
conda activate tethys
tethys gen settings
tethys db configure
conda deactivate tethys

# done
echo "Finished installing tethys."
echo "Use 'conda activate tethys' or the 't' alias to enter the tethys environment"