# crontab
@reboot /bin/bash /home/byuhi/scripts/reboot_workflow.sh

#!/bin/bash

# mount all the fileshares and change permissions

sudo chown byuhi:byuhi /mnt

sudo mount -t cifs //globalfloodsdiag360.file.core.windows.net/output /home/byuhi/rapid-io/output -o vers=3.0,username=globalfloodsdiag360,password=+c7Ecmc7QVJxnuFUshZJg9YZZfBl8CBa8Qi6dMmTGPQgDh9K0ptGtZ69CkeU1rbnBFzXzWNJa+RVqwHUIc9XQg==,dir_mode=0777,file_mode=0777,sec=ntlmssp

sudo mount -t cifs //globalfloodsdiag360.file.core.windows.net/era-interim /home/byuhi/era_interim -o vers=3.0,username=globalfloodsdiag360,password=+c7Ecmc7QVJxnuFUshZJg9YZZfBl8CBa8Qi6dMmTGPQgDh9K0ptGtZ69CkeU1rbnBFzXzWNJa+RVqwHUIc9XQg==,dir_mode=0777,file_mode=0777,sec=ntlmssp

sudo mount -t cifs //globalfloodsdiag360.file.core.windows.net/shared-output /home/byuhi/shared-output -o vers=3.0,username=globalfloodsdiag360,password=+c7Ecmc7QVJxnuFUshZJg9YZZfBl8CBa8Qi6dMmTGPQgDh9K0ptGtZ69CkeU1rbnBFzXzWNJa+RVqwHUIc9XQg==,dir_mode=0777,file_mode=0777,sec=ntlmssp

sudo mount -t cifs //globalfloodsdiag360.file.core.windows.net/forecast-records /home/byuhi/forecast-records -o vers=3.0,username=globalfloodsdiag360,password=+c7Ecmc7QVJxnuFUshZJg9YZZfBl8CBa8Qi6dMmTGPQgDh9K0ptGtZ69CkeU1rbnBFzXzWNJa+RVqwHUIc9XQg==,dir_mode=0777,file_mode=0777,sec=ntlmssp

sudo mount -t cifs //globalfloodsdiag360.file.core.windows.net/era-5 /home/byuhi/era_5 -o vers=3.0,username=globalfloodsdiag360,password=+c7Ecmc7QVJxnuFUshZJg9YZZfBl8CBa8Qi6dMmTGPQgDh9K0ptGtZ69CkeU1rbnBFzXzWNJa+RVqwHUIc9XQg==,dir_mode=0777,file_mode=0777,sec=ntlmssp

# wait 5 minutes before running the forecasts workflow
sleep 300 && /bin/bash /home/byuhi/scripts/export_forecast_workflow.sh