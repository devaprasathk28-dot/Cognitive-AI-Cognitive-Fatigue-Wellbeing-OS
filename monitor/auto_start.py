import os
import winreg


def enable_auto_start(app_name, exe_path):
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE
    )

    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
    winreg.CloseKey(key)


def disable_auto_start(app_name):
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, app_name)
        winreg.CloseKey(key)
    except:
        pass