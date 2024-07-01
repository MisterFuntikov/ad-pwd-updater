# ad-pwd-updater

Обновление пароля доменного пользователя GUI Linux.<br>
Разработано для X Window System (X11),<br>
получение сведений через ldap3 с GSSAPI,<br>
обновление пароля через expect при помощи kpasswd.<br>
Протестировано на Centos7.<br>

## Требуемые пакеты
```
yum install expect
yum install krb5-workstation krb5-libs krb5-devel
yum install qt5-qtbase qt5-qtbase-gui qt5-qtsvg qt5-qtx11extras
yum install libxkbcommon-x11 xcb-util xcb-util-image xcb-util-keysyms xcb-util-renderutil xcb-util-wm xcb-util-cursor
```

## Принцип работы
При запуске программа проверяет через ldap протокол атрибут pwdLastSet пользователя в домене с настройкой maxPwdAge. Если текущий пароль устарел, то будет открыто окно для обновления пароля.

![image](https://github.com/MisterFuntikov/ad-pwd-updater/assets/69751509/c6764175-24c3-45e6-a95f-599976157860)

<br>

## Настройки программы

### Параметры запуска

```
-f, --forced  Принудительная смена пароля
-w, --window  Запуск в оконном режиме
```

Возможно переопределить поведение программы через файл `settings.ini`, расположенный в одной директории с запускаемой программой. <br>
Возможные настройки:<br>

### секция [MAIN]

| Опция | Описание | По умолчанию | Допустимые значения |
|-|-|-|-|
| maximized | Запскать программу в развернутом состоянии | yes | yes, no | 
| fullscreen | Запускать программу на полный экран | yes | yes, no |
| hidewindowbuttons | Скрывать кнопки управления окном (свернуть, развернуть, закрыть) | yes | yes, no |
| aborthotkey | Сочетание клавиш для закрытия окна | Стандартное сочетание клавиш закрытия окна (Alt+F4) | Группа модификаторов + клавиша разделенные нижним подчеркиванием (например ctrl_alt_c) |
| logo | Путь к изображению, которое используется в шапке формы программы | | Любой путь к файлу изображения |
| hostname | Отображение имени компьютера или ip адреса в вверхней левой части программы | | dnsdomainname, domainname, ip, ipaddress |

### секция [PASSWORD]

| Опция | Описание | По умолчанию | Допустимые значения |
|-|-|-|-|
| length | Минимальная длина пароля | minPwdLength | minPwdLength (будет брать значение из домена), положительные числа | 
| history | Количество старых паролей, которых не должен повторять новый пароль | pwdHistoryLength | pwdHistoryLength (будет брать значение из домена), положительные числа |
| age | Срок действия пароля | maxPwdAge | maxPwdAge (будет брать значение из домена), положительные числа (будет установлен собственный срок действия пароля), отрицательные числа (будет отнимать maxPwdAge от текущего значения) |
| special | Минимальное количество специальных символов в пароле | 2 | положительные числа |
| number | Минимальное количество цифр в пароле | 2 | положительные числа |
| uppercase | Минимальное количество заглавных букв в пароле | 2 | положительные числа |
| lowercase | Минимальное количество строчных букв в пароле | 0 | положительные числа |
| confirmpwd | Требовать пользователя подтвержать свой новый пароль | yes | yes, no |
<br>

