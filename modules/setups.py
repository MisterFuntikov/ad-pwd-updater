import os
import types


class SETUPS():

    _SET = dict()
    _DEF = dict()
    _convert_status = True

    def __init__(self):
        pass

    def convertType(self, value, vtype):

        def tBool(x):
            t = ['yes', 1, 'true', 'True', True]
            if x in t:
                return True
            return False

        def tFile(x):
            if os.path.isfile(x):
                return str(x)
            return None

        def tDir(x):
            if os.path.isdir(x):
                return str(x)
            return None

        oper = {
            bool: tBool,
            'file': tFile,
            'dir': tDir,
            int: lambda x: int(x),
            float: lambda x: float(x),
            str: lambda x: str(x),
            list: lambda x: list(x),
            dict: lambda x: dict(x),
            tuple: lambda x: tuple(x),
        }
        try:
            result = oper[vtype](value)
        except Exception as err:
            self._convert_status = False
            return
        self._convert_status = True
        return result

    def setDefault(
            self, param: str, default: any = None, valuesupport: list = list(),
            typesupport: list = list(),
            group: str = None):

        if not group or group == 'main' or group == 'default':
            ch = self._DEF
        else:
            if not group in self._DEF:
                self._DEF[group] = dict()
            ch = self._DEF[group]

        ch[param] = dict()
        ch[param]['default'] = default
        ch[param]['value'] = valuesupport
        ch[param]['type'] = typesupport
        ch[param]['lock'] = False
        return

    def setParam(self, param: str, value: any, group: str = None, lock: bool = False) -> bool:

        if not group or group == 'main' or group == 'default':
            tch = self._DEF
            ch = self._SET
        else:
            if not group in self._DEF:
                return None
            tch = self._DEF[group]
            if not group in self._SET:
                self._SET[group] = dict()
            ch = self._SET[group]

        if not param in tch:
            return None

        if tch[param]['lock'] == True:
            return 'lock'

        if value in tch[param]['value']:
            ch[param] = value
            tch[param]['lock'] = lock
            return True

        if type(value) in tch[param]['type']:
            ch[param] = value
            tch[param]['lock'] = lock
            return True

        for ttype in tch[param]['type']:
            v = self.convertType(value=value, vtype=ttype)
            if self._convert_status == True:
                ch[param] = v
                tch[param]['lock'] = lock
                return True

        ch[param] = tch[param]['default']
        tch[param]['lock'] = lock
        return False

    def getParam(self, param: str, group: str = None):

        ch = dict()
        cht = dict()

        if not group or group == 'main' or group == 'default':
            ch = self._SET
            cht = self._DEF
        else:
            if group in self._SET:
                ch = self._SET[group]
            if group in self._DEF:
                cht = self._DEF[group]

        if param in ch:
            return ch[param]
        if param in cht:
            return cht[param]['default']

        return None
