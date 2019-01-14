# seoul 리전
aws ec2 run-instances --image-id ami-0b4fdb56a00adb616 \
--count 1 --instance-type t3.nano \
--key-name gncloud-io --security-group-ids sg-0c6e6629bfae81391 \
--user-data file://user-data.sh \
--region ap-northeast-2 \
--profile default \
#--tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=marketmaker}]'
