#!/bin/bash

script="/home/water/DailyAggregating/hydroinformatics/era5/optimized_aggregate.py"
log="/home/water/DailyAggregating/"
rapidoutput="/home/water/mount_to_container/rapid-io/output"

source /home/water/miniconda3/etc/profile.d/conda.sh; conda activate era5aggregate

python $script $rapidoutput/australia-geoglows/Qout_era5_t640_1hr_19790101to20181231.nc $log/aus.log
python $script $rapidoutput/central_america-geoglows/Qout_era5_t640_1hr_19790101to20181231.nc $log/cen_am.log
python $script $rapidoutput/central_asia-geoglows/Qout_era5_t640_1hr_19790101to20181231.nc $log/cen_as.log
python $script $rapidoutput/east_asia-geoglows/Qout_era5_t640_1hr_19790101to20181231.nc $log/e_as.log
python $script $rapidoutput/europe-geoglows/Qout_era5_t640_1hr_19790101to20181231.nc $log/eu.log
python $script $rapidoutput/islands-geoglows/Qout_era5_t640_1hr_19790101to20181231.nc $log/isl.log
python $script $rapidoutput/japan-geoglows/Qout_era5_t640_1hr_19790101to20181231.nc $log/jap.log
python $script $rapidoutput/middle_east-geoglows/Qout_era5_t640_1hr_19790101to20181231.nc $log/mid_eas.log
python $script $rapidoutput/north_america-geoglows/Qout_era5_t640_1hr_19790101to20181231.nc $log/nor_am.log
python $script $rapidoutput/south_america-geoglows/Qout_era5_t640_1hr_19790101to20181231.nc $log/s_am.log
python $script $rapidoutput/south_asia-geoglows/Qout_era5_t640_1hr_19790101to20181231.nc $log/s_as.log
python $script $rapidoutput/west_asia-geoglows/Qout_era5_t640_1hr_19790101to20181231.nc $log/w_as.log
