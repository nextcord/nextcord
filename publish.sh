rm -rf build
mkdir build
mkdir -p dist

python setup.py sdist --formats=gztar
twine upload dist/*
