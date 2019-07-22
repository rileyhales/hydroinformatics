#!/usr/bin/env bash
conda deactivate tethys
conda env remove -n tethys
cd
rm -r .tethys