import sys, os, traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
os.chdir(os.path.join(os.path.dirname(__file__), 'app'))
try:
    import main
    print("IMPORT OK")
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    traceback.print_exc()
