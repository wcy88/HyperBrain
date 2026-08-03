import sys
sys.path.insert(0, r'e:\超脑\超脑002')
try:
    from hyperbrain.ui.main_window import MainWindow, BrainWorker
    print('import OK')
except Exception as e:
    print(f'IMPORT ERROR: {e}')
    import traceback
    traceback.print_exc()
