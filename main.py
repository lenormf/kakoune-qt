#! /usr/bin/env python2
##
## main.py for kakoune-qt
## by lenormf
##

import sys
import logging
from PyQt5.QtWidgets import QApplication

from kakoune_qt import KakouneQt

def main(av):
    logging.basicConfig(format="[%(asctime)s][%(levelname)s]: %(msg)s", level=logging.DEBUG)

    app = QApplication(av)
    kakoune_qt = KakouneQt(av[1:])

    kakoune_qt.show()

    app.exec_()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
