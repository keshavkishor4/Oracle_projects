#!/bin/bash
cp -r fapod ./intel
prefix=$(date +'%d.%m.%y.%H.%M')
postfix=$(cat image_version.txt)
version=$prefix\_$postfix
echo $version