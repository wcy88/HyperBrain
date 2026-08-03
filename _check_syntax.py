import ast
import sys
try:
    with open(r'e:\超脑\超脑002\hyperbrain\ui\main_window.py', 'r', encoding='utf-8') as f:
        src = f.read()
    ast.parse(src)
    print('syntax OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    sys.exit(1)
