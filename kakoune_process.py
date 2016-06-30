##
## kakoune_process.py for kakoune-qt
## by lenormf
##

import logging
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from json_rpc import JsonRpc, JsonRpcException

class KakouneProcess(QtCore.QProcess):
    COMMAND_LINE = "kak -ui json"

    def __init__(self, window_kak, argv, parent=None):
        super(KakouneProcess, self).__init__(parent)

        assert(window_kak != None)

        self.window_kak = window_kak

        self.readyReadStandardOutput.connect(self.onReadyReadStandardOutput)
        self.readyReadStandardError.connect(self.onReadyReadStandardError)

        argv = [ '"{0}"'.format(a) for a in argv ]
        cmdline = "{0} {1}".format(self.COMMAND_LINE, ' '.join(argv))
        logging.debug("starting process: {0}".format(cmdline))
        self.start(cmdline)

    def writeData(self, packet):
        logging.debug("sending data: [{0}]".format(packet))

        super(KakouneProcess, self).writeData(packet)

    @pyqtSlot()
    def onReadyReadStandardOutput(self):
        data_bytearr = self.readAllStandardOutput()
        if data_bytearr.isEmpty():
            return 0

        for data in data_bytearr.split('\n'):
            data = data.data()
            if not len(data):
                continue

            try:
                data_json = JsonRpc.Unpack(data)
                logging.debug("{0}".format(data_json))
            except JsonRpcException as e:
                ## FIXME: error in the UI
                logging.error("unable to decode data: {0}".format(e))
                continue

            ## FIXME: factorize
            if data_json["method"] == "draw_status":
                if len(data_json["params"]) < 3:
                    logging.error("invalid number of arguments for method {0}: {1}".format(data_json["method"], len(data_json["params"])))
                else:
                    self.window_kak.signalReceiveDrawStatusPacket.emit(*data_json["params"][0:3])
            elif data_json["method"] == "draw":
                if len(data_json["params"]) < 3:
                    logging.error("invalid number of arguments for method {0}: {1}".format(data_json["method"], len(data_json["params"])))
                else:
                    self.window_kak.signalReceiveDrawPacket.emit(*data_json["params"][0:3])
            elif data_json["method"] == "refresh":
                self.window_kak.signalReceiveRefreshPacket.emit()

    @pyqtSlot()
    def onReadyReadStandardError(self):
        data_bytearr = self.readAllStandardError()
        if data_bytearr.isEmpty():
            return 0

        self.window_kak.signalReceiveErrorMessage.emit(data_bytearr.data())
