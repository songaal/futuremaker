#! /bin/bash

# remove
rm -rf build dist futuremaker.egg-info
#sleep 1

# wheel
python setup.py bdist_wheel
sleep 1

# upload
twine upload dist/futuremaker-*.whl
sleep 1
rm -rf build dist futuremaker.egg-info
echo "successful."

