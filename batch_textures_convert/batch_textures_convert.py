import os
import sys
import argparse
from PySide2 import QtWidgets

parser = argparse.ArgumentParser(description='Batch texture conversion.')
parser.add_argument("-p", "--path", help='Path pointing to folder with textures to be converted. Multiple paths are supported, they need to be separated with " /// " (without quotes)')
args = parser.parse_args()

# set up python path for modules
this_script = os.path.dirname(os.path.realpath(__file__))
path_to_modules = os.path.join(this_script, "scripts", "python")
sys.path.append(path_to_modules)

import batch_convert

if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = batch_convert.runGui(path=args.path)
    sys.exit(app.exec_())