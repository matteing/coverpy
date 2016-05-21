.PHONY: test install

publish:
	python3 setup.py sdist bdist_wheel upload

wheel:
	python3 setup.py bdist_wheel

install:
	pip install -r requirements.txt

test:
	green --run-coverage -vv
