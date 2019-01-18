#! /bin/bash

# remove
rm -rf dist
rm -rf build
rm -rf futuremaker.egg-info
#sleep 1

# wheel
python setup.py bdist_wheel
sleep 1

# upload
twine upload dist/futuremaker-*.whl

echo "successful."

