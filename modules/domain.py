import os
import subprocess
from ldap3 import Server, Connection


class DOMAIN():

    _conn = None
    _server_name = None
    _server_bind = None

    def __init__(self):
        pass

    def getAdsInfo(self):
        try:
            result = subprocess.run(['net', 'ads', 'info'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f'Ошибка выполнения команды: {e}')
            return False
        except Exception as e:
            print(f'Ошибка: {e}')
            return False

        output = result.stdout.decode()
        info = {}
        for line in output.splitlines():
            if ': ' in line:
                key, value = line.split(': ', 1)
                info[key] = value
        if not 'LDAP server name' in info or not 'Bind Path' in info:
            print('Не удалось получить требуемую информацию от сервера.')
            return False
        self._server_name = info['LDAP server name']
        self._server_bind = info['Bind Path']
        return True

    def getConn(self):
        if not self._server_bind or not self._server_name:
            if not self.getAdsInfo():
                return False
        try:
            server = Server(host=self._server_name, get_info='NO_INFO')
            conn = Connection(
                server,
                authentication='SASL',
                sasl_mechanism='GSSAPI',
                # sasl_credentials=("",""),
                auto_bind='DEFAULT',
                read_only=True
            )
            if conn.bind():
                self._conn = conn
                return True
        except Exception as e:
            print(f'Ошибка: {e}')
        return False

    def getTreePwdInfo(self):
        if not self._server_bind \
                or not self._server_name \
                or not self._conn:
            if not self.getConn():
                return None
        try:
            self._conn.search(search_base=self._server_bind,
                              search_filter=f'(&(objectClass=*))',
                              search_scope='BASE',
                              size_limit=1,
                              attributes=['maxPwdAge',
                                          'minPwdLength',
                                          'pwdHistoryLength']
                              )
        except Exception as e:
            print(f'Ошибка: {e}')
            return None
        if len(self._conn.response) == 0 or not 'attributes' in self._conn.response[0]:
            return None
        return self._conn.response[0]['attributes']

    def getUserPwdInfo(self):
        if not self._server_bind \
                or not self._server_name \
                or not self._conn:
            if not self.getConn():
                return None
        try:
            self._conn.search(
                search_base=self._server_bind,
                search_filter=f'(&(objectCategory=person)(objectClass=user)(sAMAccountName={os.getlogin()}))',
                search_scope='SUBTREE', size_limit=1, attributes=['pwdLastSet'])
        except Exception as e:
            print(f'Ошибка: {e}')
            return None
        if len(self._conn.response) == 0 or not 'attributes' in self._conn.response[0]:
            return None
        return self._conn.response[0]['attributes']

    def getHostName(self, viewtype='dnsdomainname'):
        tps = {
            'dns': ['hostname', '-s'],
            'domain': ['hostname', '-s'],
            'domainname': ['hostname', '-s'],
            'dnsdomainname': ['hostname', '-s'],
            'ip': ['hostname', '-I'],
            'ipaddress': ['hostname', '-I'],
        }
        if not viewtype in tps:
            return
        try:
            result = subprocess.run(
                tps[viewtype], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f'Ошибка выполнения команды: {e}')
            return False
        except Exception as e:
            print(f'Ошибка: {e}')
            return False
        return result.stdout.decode()
