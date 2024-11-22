.PHONY: all install

all: install static/css/pygments.css
	@echo 'Build finished'

install: dev-requirements.txt requirements.txt
	pip-sync requirements.txt dev-requirements.txt

dev-requirements.txt: dev-requirements.in requirements.txt
	pip-compile dev-requirements.in

requirements.txt: requirements.in
	pip-compile requirements.in

static/css/pygments.css:
	pygmentize -S default -f html -a .codehilite > static/css/pygments.css
