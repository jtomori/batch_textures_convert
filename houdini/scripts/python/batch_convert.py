import os
import hou
import time
import subprocess
import multiprocessing
from Queue import Queue
from threading import Thread

# define function which will be executed in parallel
def convert(q):
    """
    a worker function, which is run in parallel
    """
    while True:
        texture = q.get()
        
        textureRAT = texture.split(".")
        textureRAT[-1] = "rat"
        textureRAT = ".".join(textureRAT)
        cmd = "iconvert \"" + texture + "\" \"" + textureRAT + "\""
        CREATE_NO_WINDOW = 0x08000000
        subprocess.call(cmd, creationflags=CREATE_NO_WINDOW)
        
        q.task_done()

def batchConvert():
    """
    recursively finds and converts textures in a specified folder
    """
    img_options = [".jpg", ".jpeg", ".tga", ".exr", ".tif", ".tiff", ".png", ".bmp", ".gif", ".ppm", ".hdr"]
    img = hou.ui.selectFromList(choices=img_options, default_choices=range( len(img_options) ), message="Select texture formats to be converted", title="Choose texture formats", clear_on_cancel=True)    
    if len(img) == 0:
        return

    img = [ img_options[i] for i in img ]

    root = hou.getenv("JOB")
    root = os.path.normpath(root)

    path = hou.ui.selectFile(start_directory=root, title="Select a folder with textures for conversion", collapse_sequences=True, file_type=hou.fileType.Directory, chooser_mode=hou.fileChooserMode.Read)
    if path == "":
        return
    
    textures = []

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower().endswith( tuple(img) ):
                textures.append(os.path.join(root, file).replace("\\","/"))

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
            worker = Thread(target=convert, args=(texturesQ, ))
            worker.setDaemon(True)
            worker.start()

        # wait until all threads are done
        texturesQ.join()
        hou.ui.displayMessage("Texture conversion done in {} seconds.".format( time.time() - start_time ), title="Done")