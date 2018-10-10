import os
import time
import converters
import batch_convert
import multiprocessing
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

try:
    import hou
    in_hou = True
except ImportError:
    in_hou = False

class MainGui(QtWidgets.QWidget):
    """
    A class specifying graphical user interface of the tool
    """
    def __init__(self, parent=None, path=None):
        super(MainGui, self).__init__(parent)
        
        if in_hou:
            self.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Window)
            self.setProperty("houdiniStyle", True)

        self.setWindowTitle("Batch texture conversion")
        self.setMinimumSize(400, 550)

        self.input_formats_list = batch_convert.input_formats
        self.output_formats_list = sorted(batch_convert.output_formats_dict.keys())
        self.paths_separator = batch_convert.paths_separator
        self.default_selected_formats = batch_convert.default_selected_formats
        self.default_output_format = batch_convert.default_output_format

        # create layouts
        main_layout = QtWidgets.QVBoxLayout()
        folder_layout = QtWidgets.QHBoxLayout()
        form_layout = QtWidgets.QFormLayout()
        bottom_buttons = QtWidgets.QHBoxLayout()

        # Create widgets
        file_label = QtWidgets.QLabel("Select folders with textures for conversion")

        self.folder_path = QtWidgets.QLineEdit()

        if path:
            self.folder_path.setText(path)
        
        if in_hou:
            self.folder_button = hou.qt.createFileChooserButton() # this is H specific
            self.folder_button.setFileChooserFilter(hou.fileType.Directory)
            self.folder_button.setFileChooserMode(hou.fileChooserMode.Read)
            self.folder_button.setFileChooserTitle("Select a folder with textures for conversion")
            self.folder_button.setFileChooserMultipleSelect(True)
            if path:
                self.folder_button.setFileChooserStartDirectory( path )
            else:
                self.folder_button.setFileChooserStartDirectory( hou.expandString("$JOB") )
        else:
            self.folder_button = QtWidgets.QPushButton("...")

        self.input_formats = QtWidgets.QListWidget()
        self.input_formats.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.input_formats.addItems(self.input_formats_list)
        self.input_formats.setFixedHeight( self.input_formats.sizeHintForRow(0) * (self.input_formats.count()+4) )
        for i in range( self.input_formats.count() ):
            selected_options = self.default_selected_formats
            current_item = self.input_formats.item(i).text()
            if current_item in selected_options:
                self.input_formats.setCurrentRow(i, QtCore.QItemSelectionModel.SelectionFlag.Select)
        
        if in_hou:
            self.output_format = hou.qt.createComboBox() # this is H specific
        else:
            self.output_format = QtWidgets.QComboBox()
        self.output_format.addItems(self.output_formats_list)
        try:
            default_idx = self.output_formats_list.index(self.default_output_format)
            self.output_format.setCurrentIndex(default_idx)
        except ValueError:
            print "Default output format option is not available, skipping default selection"
            pass
        
        cpu_threads_max = multiprocessing.cpu_count()
        cpu_threads_default = cpu_threads_max / 3
        self.threads_info = QtWidgets.QLabel("Number of parallel processes: {}".format(str(cpu_threads_default)))
        self.threads_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.threads_slider.setRange(1, cpu_threads_max)
        self.threads_slider.setValue(cpu_threads_default)
        self.threads_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.threads_slider.setTickInterval(1)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setFormat("%p % done (%v / %m textures)")
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximum(0)
        self.progress_bar.hide()

        self.progress_text = QtWidgets.QLabel()
        self.progress_text.setAlignment( QtCore.Qt.AlignCenter )
        self.progress_text.setText( self.progress_bar.text() )
        self.progress_text.hide()

        self.button_convert = QtWidgets.QPushButton("Convert")
        self.button_stop = QtWidgets.QPushButton("Stop")
        self.button_stop.setEnabled(False)
        button_cancel = QtWidgets.QPushButton("Close")
        
        # Create assign widgets and layouts
        main_layout.addWidget(file_label)
        
        folder_layout.addWidget(self.folder_path)
        folder_layout.addWidget(self.folder_button)
        
        form_layout.addRow("Input Formats", self.input_formats)
        form_layout.addRow("Output Format", self.output_format)
        
        bottom_buttons.addStretch(1)
        bottom_buttons.addWidget(self.button_convert)
        bottom_buttons.addWidget(self.button_stop)        
        bottom_buttons.addWidget(button_cancel)

        main_layout.addLayout(folder_layout)
        main_layout.addLayout(form_layout)
        main_layout.addStretch(1)        
        main_layout.addWidget(self.threads_info)
        main_layout.addWidget(self.threads_slider)
        main_layout.addStretch(1)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.progress_text)        
        main_layout.addStretch(2)
        main_layout.addLayout(bottom_buttons)

        # Set dialog main_layout
        self.setLayout(main_layout)
        
        # center the window
        my_dimensions = self.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        my_dimensions.moveCenter(centerPoint)
        self.move(my_dimensions.topLeft())

        # Add signals
        if in_hou:
            self.folder_button.fileSelected.connect(self.applyFolderPathHou)
        else:
            self.folder_button.clicked.connect(self.folderPathDialog)
        self.progress_bar.valueChanged.connect(self.updateProgressText)
        self.button_convert.clicked.connect(self.convert)
        self.button_stop.clicked.connect(self.stopConversion)
        button_cancel.clicked.connect(self.cancel)
        self.threads_slider.valueChanged.connect(self.updateThreadsCount)

    def folderPathDialog(self):
        """
        updates folder_path label when called from pyside native button

        link to explanation on how to enable multiple directories selection:
            https://stackoverflow.com/questions/38252419/qt-get-qfiledialog-to-select-and-return-multiple-folders
        """
        if self.folder_path.text() == "":
            default_path = os.getenv("HOME")
        else:
            default_path = self.folder_path.text().split(self.paths_separator)[0]
        
        dialog = QtWidgets.QFileDialog(self, "Select a folder with textures for conversion:", default_path)
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)

        # don't use native dialog, enable multiple dir selection
        dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
        file_view = dialog.findChild(QtWidgets.QListView, 'listView')
        f_tree_view = dialog.findChild(QtWidgets.QTreeView)

        if file_view:
            file_view.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        if f_tree_view:
            f_tree_view.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        # exec dialog
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            path = str( self.paths_separator.join( dialog.selectedFiles() ) )
            self.folder_path.setText(path)

    @QtCore.Slot(str)
    def applyFolderPathHou(self, path):
        """
        updates folder_path label when called from houdini button
        """
        if in_hou:
            path = hou.expandString(path)
            if path != "":
                self.folder_path.setText(path.replace(" ; ", self.paths_separator))
                self.folder_button.setFileChooserStartDirectory(path.split(self.paths_separator)[0])

    @QtCore.Slot()
    def incProgressBar(self):
        """
        gets signals from running threads and increments status, after finished, calls finishedConversion()
        """
        val_max = self.progress_bar.maximum()
        val = self.progress_bar.value()
        val = val + 1
        self.progress_bar.setValue(val)

        if val == val_max:
            self.finishedConversion()

    @QtCore.Slot(int)
    def updateThreadsCount(self, threads):
        """
        updates threads_info label
        """
        self.threads_info.setText("Number of parallel processes: {}".format(str(threads)))

    @QtCore.Slot()
    def updateProgressText(self):
        """
        updates progress_text label
        """
        self.progress_text.setText( self.progress_bar.text() )

    def finishedConversion(self):
        """
        this method is called after conversion is finished and shows elapsed time, disables some not-needed-anymore buttons
        """
        self.progress_text.setText( self.progress_bar.text() + " in {0:.3f} seconds".format(time.time() - self.start_conversion_time) )
        self.button_stop.setEnabled(False)

    def stopConversion(self):
        """
        stops all threads
        """
        try:
            for proc in self.processes:
                proc.stop = True
                proc.quit()
        except AttributeError:
            # in case the app closes and no processes were running
            pass

        self.button_stop.setEnabled(False)
        self.progress_text.setText( self.progress_bar.text() + " (stopped)")

    def convert(self):
        """
        starts batch conversion
        """
        input_formats = self.input_formats.selectedItems()
        input_formats = [str( item.text() ) for item in input_formats]

        output_format_func = self.output_format.currentText()
        output_format_func = batch_convert.output_formats_dict[output_format_func]
        
        root_path = self.folder_path.text()

        threads = self.threads_slider.value()
        
        batch_convert.batchConvert(ui_obj=self, input_formats=input_formats, output_format_func=output_format_func, root_path=root_path, threads=threads)
        
    def cancel(self):
        """
        cancel button
        """
        self.stopConversion()
        self.close()


def confirmDialog(tex_count):
    """
    displays a confirmation dialog (with info about amount of found textures) for starting texture conversion process
    """
    font = QtGui.QFont()
    font.setBold( True )

    dialog = QtWidgets.QMessageBox()
    if in_hou:
        dialog.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Window)
        dialog.setProperty("houdiniStyle", True)
    dialog.setFont(font)

    dialog.setIcon(QtWidgets.QMessageBox.Information)
    dialog.setWindowTitle("Proceed?")
    dialog.setText("{} textures found, proceed?".format(tex_count))

    dialog.setStandardButtons(QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Ok)
    dialog.setDefaultButton(QtWidgets.QMessageBox.Yes)
    ret = dialog.exec_()
    
    if ret == dialog.Ok:
        return True
    else:
        return False