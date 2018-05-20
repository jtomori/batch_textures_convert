import os
import hou
import time
import platform
import subprocess
import multiprocessing
from Queue import Queue
from threading import Thread

import gui
import converters

def runGui():
    """
    displays the gui
    """
    dialog = gui.Gui()
    dialog.show()

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
    command_classes_dict = converters.GenericCommand.getValidChildCommands()

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