##
## Makefile for kakoune-qt
## by lenormf
##

UI = ui/MainWindow.ui
RC = resources.qrc

PY_UI = $(UI:.ui=.py)
PY_RC = $(RC:.qrc=_rc.py)

%.py: %.ui
	python2-pyuic5 -o $@ $<

%_rc.py: %.qrc
	pyrcc5 -o $@ $<

all: $(PY_UI) $(PY_RC)

clean:
	rm -rf $(PY_UI) $(PY_RC) $(PY_UI:.py=.pyc) $(PY_RC:.py=.pyc)
