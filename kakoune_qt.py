##
## kakoune_qt.py for kakoune-qt
## by lenormf
##

import os
import cgi
import logging

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QProcess, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QTextCursor, QIcon, QPixmap, QResizeEvent, QCloseEvent, QKeyEvent

import ui

from kakoune_process import KakouneProcess
from json_rpc import JsonRpc, Method

class TextArea:
    DEFAULT_COLOR_BG = "white"
    DEFAULT_COLOR_FG = "black"

    def __init__(self, widget):
        self.widget = widget
        self.lines = []

    def __del__(self):
        pass

    def UpdateLines(self, lines, default_face):
        default_or_bw = lambda color, color_default: color if color != "default" else color_default

        self.lines[:] = []

        css = """
            body {{
                background-color: {0};
                color: {1};
            }}
        """.format(
            default_or_bw(default_face["bg"], self.DEFAULT_COLOR_BG),
            default_or_bw(default_face["fg"], self.DEFAULT_COLOR_FG)
        )
        self.widget.setStyleSheet(css)

        for line in lines:
            atoms_html = []

            for atom in line:
                text_decoded = atom["contents"].encode("utf-8")
                text_escaped = cgi.escape(text_decoded).replace("\n", "<br>")
                html = text_escaped

                for attr in atom["face"]["attributes"]:
                    if attr == "exclusive":
                        ## FIXME: implement
                        pass
                    elif attr == "underline":
                        html = "<u>{0}</u>".format(html)
                    elif attr == "reverse":
                        ## FIXME: implement in the font if
                        pass
                    elif attr == "blink":
                        ## FIXME: implement
                        pass
                    elif attr == "bold":
                        html = "<b>{0}</b>".format(html)
                    elif attr == "dim":
                        ## FIXME: not handled by Qt ?
                        html = "<tt>{0}</tt>".format(html)
                    elif attr == "italic":
                        html = "<i>{0}</i>".format(html)

                if atom["face"]["fg"] != "default":
                    html = "<font color='{0}'>{1}</font>".format(
                        atom["face"]["fg"],
                        html
                    )

                ## FIXME: handle background
                if atom["face"]["bg"] != "default":
                    html = "<span bgcolor='{0}'>{1}</span>".format(
                        atom["face"]["bg"],
                        html
                    )

                html = html.decode("utf-8")

                atoms_html += [ html ]

            self.lines += [ ''.join(atoms_html) ]

    def Refresh(self):
        self.widget.setHtml(u"<body>{0}</body>".format("".join(self.lines)))

class KakouneQt(QtWidgets.QMainWindow):
    signalReceiveErrorMessage = pyqtSignal(str)
    signalReceiveDrawStatusPacket = pyqtSignal(list, list, dict)
    signalReceiveDrawPacket = pyqtSignal(list, dict, dict)
    signalReceiveRefreshPacket = pyqtSignal()

    def __init__(self, argv, parent=None):
        super(KakouneQt, self).__init__(parent)

        self.mainwindow = ui.MainWindow.Ui_MainWindow()
        self.mainwindow.setupUi(self)
        self.textarea = TextArea(self.mainwindow.textEdit)
        self.statusline = TextArea(self.mainwindow.lineEdit)
        ## FIXME: use QFontMetrics to set the statusline height to font height
        ## FIXME: doesn't work
        #self.mainwindow.lineEdit.setAlignment(Qt.AlignRight)

        self.signalReceiveDrawStatusPacket.connect(self.onReceiveDrawStatusPacket)
        self.signalReceiveDrawPacket.connect(self.onReceiveDrawPacket)
        self.signalReceiveRefreshPacket.connect(self.onReceiveRefreshPacket)

        self.mainwindow.actionQuit.triggered.connect(self.onQuit)

        self.resizeEvent = self.onResize
        self.closeEvent = self.onQuitEvent
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.mainwindow.textEdit.keyReleaseEvent = self.onKeyReleasedTextEdit
        self.mainwindow.textEdit.setFocus()

        self.process_client = KakouneProcess(self, argv)

    def __del__(self):
        self.onQuit(None)

    @pyqtSlot(bool)
    def onQuit(self, _):
        logging.debug("Quit signal received, killing the server")
        if self.process_client.state() == QProcess.Running:
            self.process_client.writeData(JsonRpc.Pack(Method.KEYS, [ ":kill!<ret>" ]))
            self.process_client.close()

        if not _ is None:
            self.close()

    @pyqtSlot(QCloseEvent)
    def onQuitEvent(self, ev):
        self.onQuit(None)
        ev.accept()

    @pyqtSlot(QResizeEvent)
    def onResize(self, ev):
        self.process_client.writeData(JsonRpc.Pack(Method.RESIZE, [
            self.mainwindow.textEdit.width(),
            self.mainwindow.textEdit.height()
        ]))

    @pyqtSlot(str)
    def onReceiveErrorMessage(self, msg):
        logging.error("{0}".format(msg))

        msgbox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, "Error", msg, QtWidgets.QMessageBox.Ok)
        msgbox.setIconPixmap(QPixmap(":/tango_icons/tango-icon-theme-0.8.90/32x32/actions/process-stop.png"))
        msgbox.exec_()

    @pyqtSlot(list, list, dict)
    def onReceiveDrawStatusPacket(self, status_line, mode_line, default_face):
        self.statusline.UpdateLines([ mode_line ], default_face)

    @pyqtSlot(list, dict, dict)
    def onReceiveDrawPacket(self, lines, default_face, padding_face):
        self.textarea.UpdateLines(lines, default_face)

    @pyqtSlot()
    def onReceiveRefreshPacket(self):
        self.textarea.Refresh()
        self.statusline.Refresh()

    @pyqtSlot(QKeyEvent)
    def onKeyReleasedTextEdit(self, ev):
        has_alt = ev.modifiers() == Qt.AltModifier
        has_shift = ev.modifiers() == Qt.ShiftModifier
        s = ev.text()

        if not s:
            key_ref = {
                Qt.Key_Return: "ret",
                Qt.Key_Enter: "ret",
                Qt.Key_Space: "space",
                Qt.Key_Tab: "tab",
                Qt.Key_BracketLeft: "lt",
                Qt.Key_BracketRight: "gt",
                Qt.Key_Backspace: "backspace",
                Qt.Key_Escape: "esc",
                Qt.Key_Up: "up",
                Qt.Key_Down: "down",
                Qt.Key_Left: "left",
                Qt.Key_Right: "right",
                Qt.Key_PageUp: "pageup",
                Qt.Key_PageDown: "pagedown",
                Qt.Key_Home: "home",
                Qt.Key_End: "end",
                Qt.Key_Backtab: "backtab",
                Qt.Key_Delete: "del",
            }

            if not ev.key() in key_ref:
                logging.warning("unable to convert key: {0}".format(ev.key()))
                return

            s = key_ref[ev.key()]
        elif has_shift:
            s = s.upper()

        if has_alt:
            s = u"a-{0}".format(s)

        s = u"<{0}>".format(s)

        self.process_client.writeData(JsonRpc.Pack(Method.KEYS, [ s ]))
