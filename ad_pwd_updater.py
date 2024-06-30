#
# Project Name: Обновление пароля доменного пользователя Linux
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program in the COPYING files.
# If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2024 Mister Funtikov
#

import os
import sys
import argparse
import subprocess
import configparser
# from Xlib import XK

from datetime import datetime, timedelta, timezone

from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox

from modules.keymap import QT_KEYMAP, ACCESS_KEYS, KEY_TO_ACCESS_KEY
from modules.logger import LOGGER
from modules.setups import SETUPS
from modules.domain import DOMAIN

""" --------------------------------------------------------------------- """

if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_forcefile = os.path.join(os.path.expanduser('~'), '.changepwd')
_PARAM_FILE = os.path.join(SCRIPT_DIR, 'settings.ini')
_ARGS = None
_LOGGER = LOGGER()
_PARAM = SETUPS()
_DOMAIN = DOMAIN()

""" --------------------------------------------------------------------- """


def fileread(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            p = f.read()
    except Exception as err:
        print(f'Не удалось прочитать файл {filename}. {err}')
        return None
    return p


def filewrite(filename, value):
    try:
        with open(filename, 'w+', encoding='utf-8') as f:
            f.write(str(value))
    except Exception as err:
        print(f'Не удалось записать в файл {filename}. {err}')
        return False
    return True


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class MainWindow(QMainWindow):

    _testcase = {
        'length': 0,
        'special': 0,
        'number': 0,
        'uppercase': 0,
        'lowercase': 0
    }
    _abort_key = None
    _window_pwdrules = None
    _window_notmatch = None
    _change_access = False
    _err_notmatch = False
    _err_pwdtip = False
    _focus_element = None

    def __init__(self):

        global _PARAM

        super().__init__()
        uic.loadUi(resource_path('design/main.ui'), self)

        if _PARAM.getParam('hidewindowbuttons'):
            self.setWindowFlags(
                Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        if _PARAM.getParam('aborthotkey'):
            if not _PARAM.getParam('fullscreen'):
                _LOGGER.log(
                    'aborthotkey был проигнорирован так как аргумент fullscreen = no')
            else:
                if not self.setAbortKey(_PARAM.getParam('aborthotkey')):
                    _LOGGER.log(
                        'aborthotkey не установлен, неверная настройка комбинации клавиш')

        logo = _PARAM.getParam('logo')
        if logo == None:
            self.logo.height = 0
            self.logoimage.height = 0
        else:
            img = QPixmap(logo)
            self.logoimage.setPixmap(img)
            self.logoimage.resize(img.width(), img.height())
            self.logoimage.setMinimumSize(img.width(), img.height())
            self.logoimage.setMaximumSize(img.width(), img.height())
            self.logo.setMinimumSize(0, img.height())

        if _PARAM.getParam('confirmpwd', 'password') == False:
            self.newpwd2Text.setMaximumHeight(0)
            self.newpwd2Edit.setMaximumHeight(0)

        age = str(_PARAM.getParam('age', 'password'))
        subt = self.subtitleText.text().replace('&lt;day&gt;', age)
        self.subtitleText.setText(subt)
        self.namemachine.setText(_PARAM.getParam('hostname'))

        self.newpwdEdit.textChanged.connect(self.checkNewPwd)
        self.newpwd2Edit.textChanged.connect(
            lambda: self.pwdEdit(self.newpwd2Edit))
        self.editBtn.clicked.connect(self.changePwd)

        for key in self._testcase:
            val = _PARAM.getParam(key, 'password')
            if val != None and type(val) == int and val > 0:
                self._testcase[key] = val
        pass

    def pwdEdit(self, obj):
        self.notMathErr(False)
        tedit = ''
        for char in obj.text():
            if not char in ACCESS_KEYS:
                if not char in KEY_TO_ACCESS_KEY:
                    continue
                tedit += KEY_TO_ACCESS_KEY[char]
                continue
            tedit += char
        obj.setText(tedit)
        pass

    def notMathErr(self, mode):
        self._err_notmatch = mode
        if mode:
            self._window_notmatch.show()
            css = 'background-color: rgb(255,193,193);'
            self.newpwdEdit.setStyleSheet(css)
            self.newpwd2Edit.setStyleSheet(css)
            self.posRequest()
            return
        self._window_notmatch.hide()
        self.newpwdEdit.setStyleSheet('')
        self.newpwd2Edit.setStyleSheet('')
        return

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._window_pwdrules.showing(False)
        pass

    def enterEvent(self, event):
        super().enterEvent(event)
        self._window_pwdrules.showing()
        pass

    def moveEvent(self, event):
        super().moveEvent(event)
        self.posRequest()
        pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.posRequest()
        pass

    def posRequest(self):

        if not self._window_pwdrules:
            self._window_pwdrules = PwdRulesWindow()
            self._window_pwdrules.show()
            self._window_pwdrules.showing(False)

        if not self._window_notmatch:
            self._window_notmatch = NotMatchWindow()

        # if self._err_pwdtip:
        place = self.newpwdEdit.mapToGlobal(QPoint(0, 0))
        geo = self.newpwdEdit.geometry()
        self._window_pwdrules.movePosition(place, geo)

        if self._err_notmatch:
            place1 = self.newpwdEdit.mapToGlobal(QPoint(0, 0))
            geo1 = self.newpwdEdit.geometry()
            place2 = self.newpwd2Edit.mapToGlobal(QPoint(0, 0))
            geo2 = self.newpwd2Edit.geometry()
            self._window_notmatch.movePosition(place1, geo1, place2, geo2)

        pass

    def checkNewPwd(self):

        self.pwdEdit(self.newpwdEdit)

        count = {
            'length': 0,
            'special': 0,
            'number': 0,
            'uppercase': 0,
            'lowercase': 0
        }

        for char in self.newpwdEdit.text():
            count['length'] += 1
            if char.isdigit():
                count['number'] += 1
                continue
            if char.isalpha():
                if char.isupper():
                    count['uppercase'] += 1
                else:
                    count['lowercase'] += 1
                continue
            count['special'] += 1

        result = set()
        for key in self._testcase:
            if count[key] < self._testcase[key]:
                result.add(key)

        self._window_pwdrules.setStyles(result)
        if len(result) == 0:
            self._change_access = True
        else:
            self._change_access = False
        pass

    def changePwd(self):

        def showMsg(self, title='', text='', icon=QMessageBox.Warning):
            msg = QMessageBox(self)
            msg.setIcon(icon)
            msg.setWindowTitle(title)
            msg.setText(text)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setWindowFlags(Qt.Tool | Qt.Window |
                               Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)
            # screen = QDesktopWidget().availableGeometry()
            # wgeo = msg.frameGeometry()
            # wgeo.moveCenter(screen.center())
            # msg.move(wgeo.topLeft())
            # msg.move(self.geometry().center())
            msg.exec_()
            return

        if self._change_access == False:
            self._window_pwdrules.showing(False)
            m = 'Новый пароль не удовлетворяет необходимым требованиям'
            _LOGGER.log(m)
            showMsg(self, 'Ошибка', m, QMessageBox.Warning)
            self._window_pwdrules.showing()
            return False

        if _PARAM.getParam('confirmpwd', 'password'):
            if self.newpwdEdit.text() != self.newpwd2Edit.text():
                self.notMathErr(True)
                return False

        try:
            result = subprocess.run(['expect', 'expect_kpasswd.sh', self.curpwdEdit.text(), self.newpwdEdit.text()],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode()
        except subprocess.CalledProcessError as e:
            _LOGGER.log(str(e), 'error')
            #
            return False

        if output.find('Password changed') != -1:
            m = 'Ваш пароль изменен, входите в корпоративные ресурсы с помощью нового пароля.'
            _LOGGER.log(m)
            showMsg(self, 'Успех', m, QMessageBox.Information)
            filewrite(_forcefile, 'False')
            self.closeApp()
            return True

        if output.find('Try a more complex password') != -1:
            m = 'Ваш пароль слишком простой, придумайте более сложный пароль.'
            _LOGGER.log(m)
            showMsg(self, 'Ошибка', m, QMessageBox.Information)
            return False

        if output.find('failed getting initial ticket') != -1:
            m = 'Неверный пароль в поле "текущий пароль".'
            _LOGGER.log(m)
            showMsg(self, 'Ошибка', m, QMessageBox.Information)
            return False

        if output.find('Password change rejected') != -1:
            h = _PARAM.getParam('history', 'password')
            m = f'Ваш новый пароль не должен повторять предыдущие {h} паролей.'
            _LOGGER.log(m)
            showMsg(self, 'Ошибка', m, QMessageBox.Information)
            return False

        m = f'Неизвестный статус: {output}. Обратитесь к вашему администратору. Программа будет закрыта.'
        _LOGGER.log(m, 'WARNING')
        showMsg(self, 'Ошибка', m, QMessageBox.Warning)
        self.closeApp()
        return False

    def setAbortKey(self, keys):
        spec = {
            'ctrl': Qt.ControlModifier,
            'alt': Qt.AltModifier,
            'shift': Qt.ShiftModifier
        }
        abkey = None
        speclist = list()

        for key in keys.lower().split('_'):
            if key in QT_KEYMAP:
                if abkey != None:
                    return False
                abkey = QT_KEYMAP[key]
            elif key in spec:
                speclist.append(spec[key])
                del spec[key]
            else:
                return False
        sp = {
            3: lambda x: (x[0] | x[1] | x[2]),
            2: lambda x: (x[0] | x[1]),
            1: lambda x: (x[0])
        }
        self._abort_key = [abkey, sp[len(speclist)](speclist)]
        return True

    def keyPressEvent(self, event):
        if self._abort_key == None:
            return
        if event.key() == self._abort_key[0] and event.modifiers() == self._abort_key[1]:
            self.closeApp()
        pass

    def closeApp(self):
        QApplication.quit()
        pass

    def closeEvent(self, event):
        if self._abort_key != None:
            event.ignore()
            return
        QApplication.quit()
        return


class PwdRulesWindow(QWidget):

    _element = {
        'length': lambda x: x.len,
        'special': lambda x: x.symb,
        'number': lambda x: x.num,
        'uppercase': lambda x: x.upper,
        'lowercase': lambda x: x.lower
    }
    _mouseon = False
    _onerr = False

    def __init__(self):

        global _PARAM

        super().__init__()
        uic.loadUi(resource_path('design/pwdtip.ui'), self)
        self.setWindowFlags(Qt.Tool | Qt.Window |
                            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)

        for key in self._element:
            val = _PARAM.getParam(key, 'password')
            if val != None and type(val) == int and val > 0:
                obj = self._element[key](self)
                obj.setText(obj.text().replace('&lt;num&gt;', str(val)))
                continue
            self._element[key](self).hide()
        pass

    def movePosition(self, place, geo):
        left = place.x() + geo.width() + 5
        top = place.y() + int(geo.height()/2) - int(self.geometry().height()/2)
        self.setGeometry(
            QRect(left, top, self.geometry().width(), self.geometry().height()))
        pass

    def setStyles(self, red_elem):
        style = {
            'red': 'color: rgb(148, 22, 22);',
            'green': 'color: rgb(18, 114, 64);'
        }
        if len(red_elem) == 0:
            self._onerr = False
        else:
            self._onerr = True
            for key in self._element:
                if key in red_elem:
                    self._element[key](self).setStyleSheet(style['red'])
                else:
                    self._element[key](self).setStyleSheet(style['green'])
        self.showing()
        pass

    def enterEvent(self, event):
        super().enterEvent(event)
        self._mouseon = True
        pass

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._mouseon = False
        pass

    def showing(self, mode=True):
        if self._onerr:
            if mode == False and self._mouseon == False:
                self.setWindowOpacity(0)
                return
            self.setWindowOpacity(1)
            return
        self.setWindowOpacity(0)
        return

    def closeEvent(self, event):
        event.ignore()
        return


class NotMatchWindow(QWidget):

    def __init__(self):
        super().__init__()
        uic.loadUi(resource_path('design/notmatch.ui'), self)
        self.setWindowFlags(Qt.Tool | Qt.Window |
                            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        pass

    def movePosition(self, startplace, startgeo, endplace, endgeo):
        left = startplace.x() + startgeo.width() + 10
        top = startplace.y() + int(startgeo.height()/2)
        bottom = endplace.y() + int(endgeo.height()/2) - top
        self.setGeometry(QRect(left, top, self.geometry().width(), bottom))
        pass

    def showEvent(self, event):
        super().showEvent(event)
        pass

    def hideEvent(self, event):
        super().hideEvent(event)
        pass

    def closeEvent(self, event):
        event.ignore()
        pass


def checkPwdAge():

    global _PARAM

    userpwd = _DOMAIN.getUserPwdInfo()
    serverpwd = _DOMAIN.getTreePwdInfo()
    hostname = _DOMAIN.getHostName(_PARAM.getParam('hostname'))
    _PARAM.setParam('hostname', hostname)

    g = 'password'

    if userpwd == None:
        userpwd = {}
    if serverpwd == None:
        serverpwd = {}

    if _PARAM.getParam('length', g) == 'minPwdLength' and 'minPwdLength' in serverpwd:
        _PARAM.setParam('length', serverpwd['minPwdLength'][0], group=g)

    if _PARAM.getParam('history', g) == 'pwdHistoryLength' and 'pwdHistoryLength' in serverpwd:
        _PARAM.setParam('history', serverpwd['pwdHistoryLength'][0], group=g)

    if not 'pwdLastSet' in userpwd:
        _LOGGER.log('Не найден параметр pwdLastSet пользователя.', 'error')
        return True

    pwdparam = _PARAM.getParam('age', g)
    if pwdparam == 'maxPwdAge' or pwdparam < 0:
        if not 'maxPwdAge' in serverpwd:
            _LOGGER.log('Не найден параметр maxPwdAge сервера.', 'error')
            return True
        maxpwdage = abs(int(serverpwd['maxPwdAge'][0]))
        maxpwdage_time = timedelta(seconds=maxpwdage / 10**7)
        if type(pwdparam) == int and pwdparam < 0:
            maxpwdage_time += timedelta(days=pwdparam)
    else:
        maxpwdage_time = timedelta(days=pwdparam)

    if maxpwdage_time < timedelta(seconds=0):
        _PARAM.setParam('age', 0, group=g)
        _LOGGER.log(
            f'Максимальное время жизни для пароля отрицательно ({maxpwdage_time})', 'info')
        return False
    _PARAM.setParam('age', maxpwdage_time.days, group=g)

    tz = timezone(timedelta())
    curdate = datetime.now(tz)

    pwdlastset = int(userpwd['pwdLastSet'][0])
    pwdlastset_time = datetime(1601, 1, 1, tzinfo=tz) + \
        timedelta(seconds=pwdlastset / 10**7)

    ttime = curdate - maxpwdage_time - pwdlastset_time
    if ttime >= timedelta(seconds=0):
        _LOGGER.log(f'Пароль просрочен на {ttime}', 'info')
        return False
    _LOGGER.log(f'До смены пароля {abs(ttime)}', 'info')
    return True


def loadParams():
    global _PARAM_FILE
    global _PARAM
    config = configparser.ConfigParser()
    config.read(_PARAM_FILE, encoding='UTF-8')
    for sect in config.sections():
        for key in config[sect]:
            lsect = sect.lower()
            status = _PARAM.setParam(key, config[sect][key], group=lsect)
            if status == None:
                msg = f'Неизвестный {key} в {lsect}'
            elif status == False:
                msg = f'Неверный {key} в {lsect}, значение установлено по умолчанию.'
            elif status == 'lock':
                msg = f'{key} в {lsect} не изменен так как был заблокирован глобальным аргументом.'
            else:
                msg = f'Прочитан {key} в {lsect}'
            _LOGGER.log(msg, level='debug')
    pass


def setDefParams():

    global _PARAM

    g = 'main'
    # _PARAM.setDefault(param='logs', group=g, default=None, typesupport=['dir'])
    _PARAM.setDefault(param='fullscreen', group=g,
                      default=True, typesupport=[bool])
    _PARAM.setDefault(param='maximized', group=g,
                      default=True, typesupport=[bool])
    _PARAM.setDefault(param='hidewindowbuttons', group=g,
                      default=True, typesupport=[bool])
    _PARAM.setDefault(param='aborthotkey', group=g,
                      default=None, typesupport=[str])
    _PARAM.setDefault(param='logo', group=g,
                      default=None, typesupport=['file'])
    _PARAM.setDefault(param='hostname', group=g,
                      default=None, typesupport=[str])

    g = 'password'
    _PARAM.setDefault(param='length', group=g, valuesupport=[
                      'minPwdLength'], default='minPwdLength', typesupport=[int])
    _PARAM.setDefault(
        param='history', group=g, valuesupport=['pwdHistoryLength'],
        default='pwdHistoryLength', typesupport=[int])
    _PARAM.setDefault(param='age', group=g, valuesupport=[
                      'maxPwdAge'], default='maxPwdAge', typesupport=[int])
    _PARAM.setDefault(param='special', group=g, default=2, typesupport=[int])
    _PARAM.setDefault(param='number', group=g, default=2, typesupport=[int])
    _PARAM.setDefault(param='uppercase', group=g, default=2, typesupport=[int])
    _PARAM.setDefault(param='lowercase', group=g, default=0, typesupport=[int])
    _PARAM.setDefault(param='confirmpwd', group=g,
                      default=True, typesupport=[bool])
    pass


if __name__ == '__main__':

    if _DOMAIN.getConn() == False:
        _LOGGER.log('Нет соединения с сервером', 'CRITICAL')
        sys.exit(1)

    setDefParams()

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--forced', action='store_true',
                        help='Принудительная смена пароля')
    parser.add_argument('-w', '--window', action='store_true',
                        help='Запуск в оконном режиме')
    _ARGS = parser.parse_args()

    if os.path.isfile(_forcefile):
        print(f'Найден файл {_forcefile}')
        p = fileread(_forcefile).lower().split('\n')
        if len(p) > 0:
            p = p[0]
        else:
            p = ''
        if p == 'true' or p == 'yes':
            _ARGS.forced = True
        print(f'Файл {_forcefile} прочитан')

    if _ARGS.window == True:
        g = 'main'
        _PARAM.setParam('fullscreen', False, group=g, lock=True)
        _PARAM.setParam('maximized', False, group=g, lock=True)
        _PARAM.setParam('hidewindowbuttons', False, group=g, lock=True)
        _PARAM.setParam('aborthotkey', False, group=g, lock=True)

    loadParams()

    status = checkPwdAge()
    if _ARGS.forced == False and status == True:
        _LOGGER.log('Пароль не будет изменен.', 'info')
        sys.exit(0)
    _LOGGER.log('Пароль будет изменен.', 'info')

    app = QApplication(sys.argv)
    window = MainWindow()
    if _PARAM.getParam('fullscreen'):
        window.showFullScreen()
    elif _PARAM.getParam('maximized'):
        window.showMaximized()
    else:
        window.show()
    window.posRequest()
    sys.exit(app.exec_())
