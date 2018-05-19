import os
import abc
import hou
import time
import platform
import subprocess
import multiprocessing
import distutils.spawn
from Queue import Queue
from threading import Thread

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

def runGui():
    """
    displays the gui
    """
    dialog = Gui()
    dialog.show()

class GenericCommand(object):
    """
    abstract class that should be used as a base for classes implementing conversion for various renderers
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def name(self):
        """
        should return str name of output format, it will be shown in UI for user to choose
        """
        pass

    @abc.abstractmethod
    def executable(self):
        """
        should return an executable performing the conversion
        """
        pass

    @abc.abstractmethod
    def generateCommand(self):
        """
        should return a list containing command and arguments
        """
        pass
    
    @classmethod
    def getValidChildCommands(cls):
        """
        finds implemented child classes and checks if their executable is present on the system
        """
        command_classes = cls.__subclasses__()
        command_classes_dict = {}

        for cmd_class in command_classes:
            found = distutils.spawn.find_executable( cmd_class.executable() )
            if found:
                command_classes_dict[ cmd_class.name() ] = cmd_class.generateCommand
            else:
                print( 'Warning: "{executable}" executable was not found, hiding "{format}" option.'.format( executable=cmd_class.executable(), format=cmd_class.name() ) )
        
        return command_classes_dict


class Rat(GenericCommand):
    """
    converts textures to Mantra RAT format    
    """
    @staticmethod
    def name():
        return "RAT (Mantra)"

    @staticmethod
    def executable():
        return "iconvert"

    @staticmethod
    def generateCommand(texture_in):
        texture_out = texture_in.split(".")
        texture_out[-1] = "rat"
        texture_out = ".".join(texture_out)
        
        return [Rat.executable(), texture_in, texture_out]

class Tx(GenericCommand):
    """
    converts textures for Arnold/PRMan TX format  
    """
    @staticmethod
    def name():
        return "TX (Arnold/PRMan)"

    @staticmethod
    def executable():
        return "maketx"

    @staticmethod
    def generateCommand(texture_in):
        texture_out = texture_in.split(".")
        texture_out[-1] = "tx"
        texture_out = ".".join(texture_out)

        return [Tx.executable(), "-u", "--oiio", "--checknan", "--filter", "lanczos3", texture_in, "-o", texture_out]

class Rs(GenericCommand):
    """
    converts textures for Redshift RS format  
    """
    @staticmethod
    def name():
        return "RS (Redshift)"

    @staticmethod
    def executable():
        return "TextureProcessor"

    @staticmethod
    def generateCommand(texture_in):

        return [Rs.executable(), texture_in]

def workerConvert(q, convert_command):
    """
    a worker function, which is executed in parallel
    """
    while True:
        texture_in = q.get()
        
        cmd = convert_command(texture_in)

        if platform.system() == "Linux":
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            print " ".join(cmd)
            print p.communicate()[0]
        elif platform.system() == "Windows":
            pass
        
        q.task_done()

def batchConvert():
    """
    finds and converts textures in a specified folder
    """

    # ask user for formats to convert
    img_options = [".jpg", ".jpeg", ".tga", ".exr", ".tif", ".tiff", ".png", ".bmp", ".gif", ".ppm", ".hdr"]
    img = hou.ui.selectFromList(choices=img_options, default_choices=range( len(img_options) ), message="Select input texture formats to be converted", title="Choose input texture formats", clear_on_cancel=True, column_header="Formats")    
    if len(img) == 0:
        return

    img = [ img_options[i] for i in img ]

    # ask user for output format
    command_classes_dict = GenericCommand.getValidChildCommands()

    command = hou.ui.selectFromList(choices=command_classes_dict.keys(), exclusive=True, default_choices=[0], message="Select output texture format", title="Choose output format", clear_on_cancel=True, column_header="Formats" )
    if len(command) == 0:
        return
    command = command_classes_dict.keys()[ command[0] ]
    command = command_classes_dict[ command ]

    # ask user for root path of textures
    root = hou.getenv("JOB")
    root = os.path.normpath(root)

    path = hou.ui.selectFile(start_directory=root, title="Select a folder with textures for conversion", collapse_sequences=True, file_type=hou.fileType.Directory, chooser_mode=hou.fileChooserMode.Read)
    if path == "":
        return

    path = hou.expandString(path)

    # find matching textures
    textures = []

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower().endswith( tuple(img) ):
                textures.append(os.path.join(root, file))

    proceed = not hou.ui.displayMessage("{} textures found, proceed?".format( str(len(textures)) ), buttons=("Yes", "No"), title="Proceed?" )

    if proceed:
        start_time = time.time()
        threads = multiprocessing.cpu_count() - 1

        # convert list to a queue
        texturesQ = Queue(maxsize=0)
        for x in xrange(len(textures)):
            texturesQ.put(textures[x])

        # spawn threads with convert function
        for i in range(threads):
            worker = Thread(target=workerConvert, args=(texturesQ, command))
            worker.setDaemon(True)
            worker.start()

        # wait until all threads are done
        texturesQ.join()
        msg = "Texture conversion done in {0:.3f} seconds.".format( time.time() - start_time )
        print msg
        hou.ui.displayMessage(msg, title="Done")