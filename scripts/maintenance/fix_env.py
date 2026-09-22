import pathlib

lines = pathlib.Path('.env').read_text(encoding='utf-8', errors='ignore').splitlines()
new_lines = [l for l in lines if 'CORS_ALLOWED_ORIGINS' not in l]
new_lines.append('CORS_ALLOWED_ORIGINS="http://192.168.1.6:3000,http://localhost:3000,http://127.0.0.1:3000"')

pathlib.Path('.env').write_text('\n'.join(new_lines), encoding='utf-8')
print("Successfully fixed .env!")
