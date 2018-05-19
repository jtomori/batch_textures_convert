Batch Textures Conversion
=========================
*Batch convert textures to various render-friendly mip-mapped formats*

A few notes
-----------
This tool works on Linux and Windows. Feel free to contribute with OS X version. <br>
Right now the following output formats are supported:
* .rat - Mantra
* .tx - Arnold / PRMan
* .rs - Redshift

However it is easy to extend / modify this tool so that it suits your needs. <br>

To add new output format, simply implement a new class in **houdini/scripts/python/batch_convert.py**, which inherits from **GenericCommand()** class. Class is very simple, so it should be straightforward to add your custom output formats. <br>

This tool relies on external executables to perform conversion (e.g. *iconvert* for *RAT*, *maketx* for *TX*...). Make sure that you have them available in your system's **PATH** variable. If an executable is not found, then it will print a warning and will hide it from the options list.

Installation
------------
1. [Download](https://github.com/jtomori/batch_textures_convert/archive/master.zip) or clone this repository.

2. Add **houdini** folder from this repository into your **HOUDINI_PATH** environment variable.
    * For example add this line into your **houdini.env** file:
    ```
    HOUDINI_PATH = &;/path/to/this/repo/houdini
    ```
    * If you have set your *HOUDINI_PATH* variable already, then use followig line.
    ```
    HOUDINI_PATH = $HOUDINI_PATH;/path/to/this/repo/houdini
    ```

3. Display **Batch Convert** shelf in Houdini

Usage
-----
* Click on **Batch Convert** shelf tool
* Select which input texture formats should be converted
    * For example you could convert only jpegs or pngs
* Select output texture format
* Confirm