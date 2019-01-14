#!/bin/bash
rm -f futuremaker.tar.gz
sleep 0.1
tar czvf futuremaker.tar.gz --exclude='*.pyc' futuremaker/ bots/ requirements.txt start.sh.template update.sh
sleep 0.3
aws s3 cp futuremaker.tar.gz s3://futuremaker-release/
