from PyInstaller.utils.hooks import can_import_module

hiddenimports = ['scipy.special._ufuncs_cxx']

if can_import_module('scipy.special._cdflib'):
    hiddenimports += ['scipy.special._cdflib']

if can_import_module('scipy.special._special_ufuncs'):
    hiddenimports += ['scipy.special._special_ufuncs']
