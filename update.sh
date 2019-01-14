#!/bin/bash
#must be root

rm -f futuremaker.tar.gz
aws s3 cp s3://futuremaker-release/futuremaker.tar.gz ./

rm -rf futuremaker/
sleep 0.2
tar -xzf futuremaker.tar.gz
