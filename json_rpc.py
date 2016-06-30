##
## json_rpc.py for kakoune-qt
## by lenormf
##

import json
import logging

class Method:
    KEYS = 0
    RESIZE = 1

class JsonRpcException(Exception): pass

class JsonRpc:
    VERSION = "2.0"
    METHOD_REF = {
        Method.KEYS: "keys",
        Method.RESIZE: "resize",
    }

    @staticmethod
    def Unpack(packet):
        try:
            base = json.loads(packet)
            if not "jsonrpc" in base or not "method" in base:
                raise JsonRpcException("garbage received in input: {0}".format(packet))

            return base
        except Exception as e:
            logging.debug("{0}".format(packet))
            raise JsonRpcException(e)

    @staticmethod
    def Pack(method, params):
        assert(method in JsonRpc.METHOD_REF.keys())
        assert(isinstance(params, list))

        try:
            base = {
                "jsonrpc": JsonRpc.VERSION,
                "method": JsonRpc.METHOD_REF[method],
                "params": params,
            }

            return u"{0}\n".format(json.dumps(base))
        except Exception as e:
            raise JsonRpcException(e)
