#!/bin/sh
# Assuming this file is always run on a system that contains curl
# Adapted from script written by Rohit Khattar

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [ "$1" == "" ]; then
    echo "Specify A Data Directory"
fi

echo "Downloading data files...."

cd ~
touch .urs_cookies

chmod -R 0755 $1
mkdir -p $1/raw/
cd $1/raw/

cat gldas2urls.txt | tr -d '\r' | xargs -n 1 -P 4 curl -LJO -n -c ~/.urs_cookies -b ~/.urs_cookies

echo "......Download Done"

# Move NCML Files into thredds data directory
cp $DIR/tethysapp/gldas/ncml/* $1