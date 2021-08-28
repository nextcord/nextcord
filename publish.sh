rm -rf build
python3 setup.py sdist
twine upload build/*
