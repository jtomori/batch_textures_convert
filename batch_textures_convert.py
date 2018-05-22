import sys
from PySide2 import QtWidgets
from scripts.python.batch_convert import *

if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    runGui()
    sys.exit(app.exec_())