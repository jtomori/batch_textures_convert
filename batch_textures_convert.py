import os
import sys
from PySide2 import QtWidgets

# set up python path for modules
this_script = os.path.dirname(os.path.realpath(__file__))
path_to_modules = os.path.join(this_script, "scripts", "python")
sys.path.append(path_to_modules)

import batch_convert

if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = batch_convert.runGui()
    sys.exit(app.exec_())