from PyInstaller.utils.hooks import collect_submodules, get_module_attribute, is_module_satisfies

# Keep the standard PyInstaller behavior, but skip pydantic.experimental because
# importing it during analysis emits a warning and the app does not use it.
hiddenimports = collect_submodules(
    'pydantic',
    filter=lambda name: not name.startswith('pydantic.experimental'),
    on_error='ignore',
)

if not is_module_satisfies('pydantic >= 2.0.0'):
    is_compiled = get_module_attribute('pydantic', 'compiled') in {'True', True}
    if is_compiled:
        hiddenimports += [
            'colorsys',
            'dataclasses',
            'decimal',
            'json',
            'ipaddress',
            'pathlib',
            'uuid',
            'dotenv',
            'email_validator',
        ]
        if not is_module_satisfies('pydantic >= 1.4'):
            hiddenimports += ['distutils.version']
        if is_module_satisfies('pydantic >= 1.8'):
            hiddenimports += ['typing_extensions']
