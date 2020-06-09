#!/bin/bash
################################################################
#
# File: export_forecast_workflow.sh
# Author: Michael Souffront
# Purpose: Generate forecasts, convert to csv, transfer data
#
################################################################

# delete previous transfer logs
rm /home/byuhi/scripts/transfer_workflow/logs/*

# delete previous output
/bin/bash /home/byuhi/scripts/transfer_workflow/cut_date.sh

# generate forecast and move to spt app servers
/bin/bash /home/byuhi/scripts/transfer_workflow/workflow.sh

# clear shared directory
rm /home/byuhi/shared-output/*

/home/byuhi/miniconda2/bin/python /home/byuhi/scripts/spt_export_forecast_stats/spt_extract_plain_table.py

# copy tables into shared directory
cp /home/byuhi/rapid-io/output/*/*/summary_table* /home/byuhi/shared-output/

# delete nces files after tables created and copied
rm /home/byuhi/rapid-io/output/*/*/nces*
rm /home/byuhi/rapid-io/output/*/*/summary_table*
touch /home/byuhi/shared-output/all_regions_completed.txt

# post process a csv of the return period level flows in each region and save the median flows to forecast records
source /home/byuhi/miniconda2/etc/profile.d/conda.sh; conda activate postprocessing
python /home/byuhi/scripts/postprocess_flow_forecasts.py ~/rapid-io ~/era_5 ~/forecast-records ~/postprocess-logs