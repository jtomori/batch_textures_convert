import os
import time
import subprocess
from PySide2 import QtCore
from threading import Thread
from Queue import Queue, Empty
from collections import defaultdict

import gui
import converters

# config
input_formats = [".jpg", ".jpeg", ".tga", ".exr", ".tif", ".tiff", ".png", ".bmp", ".gif", ".ppm", ".hdr", ".cr2"]
default_selected_formats = [".jpg", ".jpeg", ".exr"]
default_output_format = "RSTEXBIN (Redshift, skip converted)"
ext_priority = ["jpg", "png", "cr2", "exr"]
paths_separator = " /// "

output_formats_dict = converters.GenericCommand.getValidChildCommands()

def getBestTextureFormat(ext_list, extensions):
    """
    returns index to a texture from tex_list which has the highest priority in ext_list
    if none of texture extensions is in ext_list, will return None
    
    ext_list
        is list of extensions in ascending order (the latter, the higher priority), e.g.:
        ["jpg", "tif", "png", "exr", "rat"]
    """    
    idx = -1
    for ext in ext_list:
        if ext.lower() in extensions:
            idx = extensions.index(ext)
    
    if idx != -1:
        return idx
    else:
        return None

def runGui(path=None, parent=None):
    """
    displays the main gui,
    path parameter is a string which will set folder path
    """
    dialog = gui.MainGui(path=path, parent=parent)
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

                if cmd:
                    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, startupinfo=startupinfo)
                    out = p.communicate()[0]
                    print "\nThread #{}".format(self.id)
                    print "Command: {}".format( " ".join(cmd) )
                    print "Command output:\n{dashes}\n{out}{dashes}".format(out=out, dashes="-"*50)
                    print "Return code: {}\n".format(p.returncode)
                else:
                    print "Cmd is None, skipping..."

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

    # select the best texture available (prefer exr to jpg if filename and path are the same)
    textures_no_ext = [".".join(tex.split(".")[:-1]) for tex in textures]
    duplicates = defaultdict(list)

    for i,item in enumerate(textures_no_ext):
        duplicates[item].append(i)

    duplicates = {key:value for key, value in duplicates.items() if len(value)>1}

    remove_indices = []
    for key, value in duplicates.iteritems():
        dict_replace = {}
        dict_replace["indices"] = value # points to elements of texture list
        dict_replace["extensions"] = [textures[idx].split(".")[-1] for idx in value]
        dict_replace["best_ext_index"] = dict_replace["indices"][ getBestTextureFormat(ext_priority, dict_replace["extensions"]) ]
        dict_replace["remove_indices"] = [i for i in dict_replace["indices"] if i != dict_replace["best_ext_index"]]
        for i in dict_replace["remove_indices"]:
            remove_indices.append(i)

        duplicates[key] = dict_replace

    textures = [tex for i, tex in enumerate(textures) if i not in remove_indices]
    
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
