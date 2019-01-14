#!/bin/bash
yum update -y
yum install python3 -y
# env
cat <<EOT >>/etc/environment
LANG=ko_KR.utf-8
LC_ALL=ko_KR.utf-8
EOT
# aws credentials
mkdir -p /root/.aws
cat <<EOT >>/root/.aws/credentials
[default]
aws_access_key_id = $AWS_KEY
aws_secret_access_key = $AWS_SECRET/
EOT
# Install agent package
APP_HOME=/opt/futuremaker
mkdir -p $APP_HOME
cd $APP_HOME
aws s3 cp s3://futuremaker-release/futuremaker.tar.gz ./
tar -xzf $APP_HOME/futuremaker.tar.gz
pip3 install -r requirements.txt

