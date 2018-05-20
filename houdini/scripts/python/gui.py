import hou

from PySide2 import QtCore
from PySide2 import QtWidgets

class Gui(QtWidgets.QWidget):
    """
    A class specifying graphical user interface of the tool
    """
    def __init__(self, parent=None):
        super(Gui, self).__init__(parent)
        
        self.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Window)
        self.setProperty("houdiniStyle", True)
        
        self.setWindowTitle("Test Gui")
        self.setMinimumSize(400, 500)

        self.input_formats_list = ["jpg", "png", "tga", "exr"]
        self.output_formats_list = ["rat", "tx", "rs"]

        # create layouts
        main_layout = QtWidgets.QVBoxLayout()
        folder_layout = QtWidgets.QHBoxLayout()
        form_layout = QtWidgets.QFormLayout()
        bottom_buttons = QtWidgets.QHBoxLayout()

        # Create widgets
        file_label = QtWidgets.QLabel("Select a folder with textures for conversion")

        self.folder_path = QtWidgets.QLineEdit()
        folder_button = hou.qt.createFileChooserButton() # this is H specific
        folder_button.setFileChooserFilter(hou.fileType.Directory)
        folder_button.setFileChooserMode(hou.fileChooserMode.Read)
        folder_button.setFileChooserTitle("Select a folder with textures for conversion")
        folder_button.setFileChooserStartDirectory( hou.expandString("$JOB") )

        self.input_formats = QtWidgets.QListWidget()
        self.input_formats.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.input_formats.addItems(self.input_formats_list)
        self.input_formats.setFixedHeight( self.input_formats.sizeHintForRow(0) * (self.input_formats.count()+2) )
        
        #self.output_format = QtWidgets.QComboBox()
        self.output_format = hou.qt.createComboBox() # this is H specific
        self.output_format.addItems(self.output_formats_list)
        
        button_convert = QtWidgets.QPushButton("Convert")
        button_cancel = QtWidgets.QPushButton("Cancel")
        
        # Create assign widgets and layouts
        main_layout.addWidget(file_label)
        
        folder_layout.addWidget(self.folder_path)
        folder_layout.addWidget(folder_button)
        
        form_layout.addRow("Input Formats", self.input_formats)
        form_layout.addRow("Output Format", self.output_format)
        
        bottom_buttons.addStretch(1)
        bottom_buttons.addWidget(button_cancel)
        bottom_buttons.addWidget(button_convert)

        main_layout.addLayout(folder_layout)
        main_layout.addLayout(form_layout)
        main_layout.addStretch(1)
        main_layout.addLayout(bottom_buttons)

        # Set dialog main_layout
        self.setLayout(main_layout)
        
        # center the window
        my_dimensions = self.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        my_dimensions.moveCenter(centerPoint)
        self.move(my_dimensions.topLeft())

        # Add button signals
        folder_button.fileSelected.connect(self.applyFolderPath)
        button_convert.clicked.connect(self.convert)
        button_cancel.clicked.connect(self.cancel)  

    @QtCore.Slot(str)
    def applyFolderPath(self, path):
        path = hou.expandString(path)
        self.folder_path.setText(path)

    def convert(self):
        """
        Greets the user
        """
        print "convert"
    
    def cancel(self):
        """
        Cancel button
        """
        self.close()