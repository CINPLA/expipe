pip install pytest pytest-cov pytest-pep8 coveralls pyrebase
py.test expipe/io/tests --doctest-modules --doctest-glob='*.rst' --pep8 expipe -v --cov expipe --cov-report term-missing
