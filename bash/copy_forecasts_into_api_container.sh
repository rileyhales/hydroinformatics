#!/bin/bash

date=$(date -d '1 day ago' +'%Y%m%d.0')
host_forecasts_dir=/home/tethys/spt_files/ecmwf
api_forecasts_dir=/mnt/output/ecmwf
container_name=gsprestapi_gsp_api_1

for region in $(ls $host_forecasts_dir)
do
  echo "removing $region"
  docker exec $container_name rm -rf $api_forecasts_dir/$region
  echo "creating $region"
  docker exec $container_name mkdir $api_forecasts_dir/$region/
  echo "copying $region"
  docker cp $host_forecasts_dir/$region/$date $container_name:$api_forecasts_dir/$region/
done
