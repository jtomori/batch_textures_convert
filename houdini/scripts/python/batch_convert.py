import os
import hou
import time
import platform
import subprocess
import multiprocessing
from Queue import Queue
from threading import Thread

def rat_command(texture_in):
    """
    converts textures to Mantra RAT format
    """
    texture_out = texture_in.split(".")
    texture_out[-1] = "rat"
    texture_out = ".".join(texture_out)
    
    return ["iconvert", texture_in, texture_out]

def tx_command(texture_in):
    """
    converts textures for Arnold/PRman TX format
    """
    texture_out = texture_in.split(".")
    texture_out[-1] = "tx"
    texture_out = ".".join(texture_out)

    return ["maketx", "-u", "--oiio", "--checknan", "--filter", "lanczos3", texture_in, "-o", texture_out]

def worker_convert(q, convert_command):
    """
    a worker function, which is run in parallel
    """
    while True:
        texture_in = q.get()
        
        #cmd = rat_command(texture_in)
        #cmd = tx_command(texture_in)
        cmd = convert_command(texture_in)

        if platform.system() == "Linux":
            p = subprocess.Popen( cmd, stdout=subprocess.PIPE)
            print " ".join(cmd)
            print p.communicate()[0]
        elif platform.system() == "Windows":
            pass

        #textureRAT = texture.split(".")
        #textureRAT[-1] = "rat"
        #textureRAT = ".".join(textureRAT)
        #cmd = "iconvert \"" + texture + "\" \"" + textureRAT + "\""
        #CREATE_NO_WINDOW = 0x08000000
        #subprocess.call(cmd, creationflags=CREATE_NO_WINDOW)
        
        q.task_done()

def batchConvert():
    """
    recursively finds and converts textures in a specified folder
    """

    # ask user for formats to convert
    img_options = [".jpg", ".jpeg", ".tga", ".exr", ".tif", ".tiff", ".png", ".bmp", ".gif", ".ppm", ".hdr"]
    img = hou.ui.selectFromList(choices=img_options, default_choices=range( len(img_options) ), message="Select texture formats to be converted", title="Choose texture formats", clear_on_cancel=True)    
    if len(img) == 0:
        return

    img = [ img_options[i] for i in img ]

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

    convert_command = rat_command

    if proceed:
        start_time = time.time()
        threads = multiprocessing.cpu_count() - 1

        # convert list to a queue
        texturesQ = Queue(maxsize=0)
        for x in xrange(len(textures)):
            texturesQ.put(textures[x])

        # spawn threads with convert function
        for i in range(threads):
            worker = Thread(target=worker_convert, args=(texturesQ, convert_command))
            worker.setDaemon(True)
            worker.start()

        # wait until all threads are done
        texturesQ.join()
        hou.ui.displayMessage("Texture conversion done in {0:.3f} seconds.".format( time.time() - start_time ), title="Done")