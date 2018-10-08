import os
import time
import subprocess
from PySide2 import QtCore
from threading import Thread
from Queue import Queue, Empty

import gui
import converters

# globals for this module
input_formats = [".jpg", ".jpeg", ".tga", ".exr", ".tif", ".tiff", ".png", ".bmp", ".gif", ".ppm", ".hdr"]
output_formats_dict = converters.GenericCommand.getValidChildCommands()
paths_separator = " /// "

def runGui(path=None):
    """
    displays the main gui,
    path parameter is a string which will set folder path
    """
    dialog = gui.MainGui(path=path)
    dialog.show()
    return dialog

class IncSignal(QtCore.QObject):
    """
    a class used for sending signals
    """
    sig = QtCore.Signal()

class WorkerThread(QtCore.QThread):
    """
    thread class, which is taking textures from a queue and converting them
    """
    def __init__(self, queue, convert_command, id):
        super(WorkerThread, self).__init__()

        self.incSignal = IncSignal()
        self.queue = queue
        self.convert_command = convert_command
        self.id = id
        self.stop = False

    def run(self):
        while not self.stop:
            try:
                texture_in = self.queue.get(False)

                cmd = self.convert_command(texture_in)

                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, startupinfo=startupinfo)
                out = p.communicate()[0]
                print "\nThread #{}".format(self.id)
                print "Command: {}".format( " ".join(cmd) )
                print "Command output:\n{dashes}\n{out}{dashes}".format(out=out, dashes="-"*50)
                print "Return code: {}\n".format(p.returncode)

                if not self.stop:
                    self.incSignal.sig.emit()

            except Empty:
                reason = "empty queue"
                break

        if self.stop:
            reason = "stopped"

        print("Thread #{} finished ({})".format(self.id, reason))
        return

def batchConvert(ui_obj, input_formats, output_format_func, root_path, threads):
    """
    finds and converts textures in a specified folder - spawns threads which take textures from a queue
    """

    if root_path == "":
        print("No path specified")
        return
    
    if len(input_formats) == 0:
        print("No Input formats selected")
        return

    textures = []

    root_path = root_path.split(paths_separator)

    for path in root_path:
        path = os.path.normpath(path)

        for root, dirs, files in os.walk(path):
            for file in files:
                if file.lower().endswith( tuple(input_formats) ):
                    textures.append(os.path.join(root, file))
    
    textures = list( set(textures) )
    proceed = gui.confirmDialog( str(len(textures)) )

    if proceed:
        # convert list to a queue
        texturesQueue = Queue(maxsize=0)
        for x in xrange(len(textures)):
            texturesQueue.put(textures[x])

        ui_obj.progress_bar.setMaximum(len(textures))
        ui_obj.progress_bar.show()
        ui_obj.progress_text.show()
        ui_obj.button_convert.setEnabled(False)
        ui_obj.button_stop.setEnabled(True)
        ui_obj.start_conversion_time = time.time()        

        print("Spawning {} threads".format(threads))
        ui_obj.processes = []
        for i in range(threads):
            proc = WorkerThread(queue=texturesQueue, convert_command=output_format_func, id=i)
            proc.incSignal.sig.connect(ui_obj.incProgressBar)
            ui_obj.processes.append(proc)

        for proc in ui_obj.processes:
            proc.start() 

    return
