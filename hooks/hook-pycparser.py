"""
Local override for pycparser hook.

The contrib hook unconditionally requests `pycparser.lextab`/`yacctab`, which are
runtime-generated and often absent at build-time, creating noisy warnings.
For this app we do not rely on those pre-generated tables at bundle time.
"""

hiddenimports = []
