import os
import hou
import time
import platform
import subprocess
import multiprocessing
from Queue import Queue, Empty
from threading import Thread

from PySide2 import QtCore

import gui
import converters

# globals for this module
input_formats = [".jpg", ".jpeg", ".tga", ".exr", ".tif", ".tiff", ".png", ".bmp", ".gif", ".ppm", ".hdr"]
output_formats_dict = converters.GenericCommand.getValidChildCommands()

def runGui():
    """
    displays the main gui
    """
    dialog = gui.MainGui()
    dialog.show()

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
    
    def run(self):
        while True:
            try:
                texture_in = self.queue.get(False)

                cmd = self.convert_command(texture_in)

                if platform.system() == "Linux":
                    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                    print " ".join(cmd)
                    print p.communicate()[0]
                elif platform.system() == "Windows":
                    pass

                self.incSignal.sig.emit()

            except Empty:
                break

        print("Thread #{} done".format(self.id))
        return

def batchConvert(ui_obj, input_formats, output_format_func, root_path):
    """
    finds and converts textures in a specified folder - spawns threads which take textures from a queue
    """

    if root_path == "":
        print("No path specified")
        return
    
    if len(input_formats) == 0:
        print("No Input formats selected")
        return

    root_path = os.path.normpath(root_path)

    textures = []

    for root, dirs, files in os.walk(root_path):
        for file in files:
            if file.lower().endswith( tuple(input_formats) ):
                textures.append(os.path.join(root, file))
    
    proceed = gui.confirm_dialog( str(len(textures)) )

    if proceed:
        ui_obj.progress_bar.setMaximum(len(textures))
        threads = multiprocessing.cpu_count() - 1    

        # convert list to a queue
        texturesQueue = Queue(maxsize=0)
        for x in xrange(len(textures)):
            texturesQueue.put(textures[x])

        print("Spawning {} threads".format(threads))
        ui_obj.processes = []
        for i in range(threads):
            proc = WorkerThread(queue=texturesQueue, convert_command=output_format_func, id=i)
            proc.incSignal.sig.connect(ui_obj.incProgressBar)
            ui_obj.processes.append(proc)

        for proc in ui_obj.processes:
            proc.start()
        
        ui_obj.button_convert.setEnabled(False)

    return        

    """
    start_time = time.time()
    threads = multiprocessing.cpu_count() - 1

    # convert list to a queue
    texturesQ = Queue(maxsize=0)
    for x in xrange(len(textures)):
        texturesQ.put(textures[x])

    # spawn threads with convert function
    for i in range(threads):
        worker = Thread(target=workerFunc, args=(texturesQ, output_format_func))
        worker.setDaemon(True)
        worker.start()

    # wait until all threads are done
    #texturesQ.join()
    msg = "Texture conversion done in {0:.3f} seconds.".format( time.time() - start_time )
    print msg
    hou.ui.displayMessage(msg, title="Done")
    """