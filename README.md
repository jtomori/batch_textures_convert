# Batch Textures Conversion
*Batch convert textures to various render-friendly mip-mapped formats*

<br>

## Intro
This tool helps with pre-processing of textures for offline renderers. It can be used as a standalone application.

Renderers usually convert common texture formats *(jpg, png, tga..)* into more render friendly mip-mapped formats *(rat, rs, tx..)* which can be a time consuming process. Mainly if the renderer discards the converted texture afterwards and this process gets repeated many times.

It is therefore more efficient to pre-convert them once and let renderers use them.

It can be also used as a batch images converter, e.g. for converting raw photos with dcraw.

<br>

<img src="./img/screen_ubuntu.png" alt="Ubuntu standalone screenshot" height="300px"> <img src="./img/screen_win.png" alt="Windows standalone screenshot" height="300px">
<br>

*Screenshots from Ubuntu and Windows standalone*

You can see this tool in action [here](https://www.youtube.com/watch?v=5-p3__vsktg).

<br>

## Installation
TBD
```
pip install ...
```

<br>

## Usage
TBD
```
batch-textures-convert
```

Arguments:
```
...
```

*  **Standalone**
    * `$ python batch_textures_converter.py`
        * you can specify optional `--path` argument, which will set folder path (see `$ python batch_textures_converter.py --help` for help)
* Select a root folder containing textures you want to convert, it will be scanned recursively
    * You can also select/copypaste multiple folders, they will be separated with `" /// "`
* Select which input texture formats should be converted
    * For example you could convert only jpegs or pngs
* Select output texture format
* Set number of parallel processes to be run
    * Note that it does not scale linearly and at some point you will hit disk/network IO limit
* Confirm

<br>

## A few notes
* This tool works on Linux and Windows. Feel free to test it under and contribute for OS X version.
    Right now the following output formats are supported:
    
    * .rat - Mantra (iconvert)
    * .tx - Arnold (maketx)
    * .tx - PRMan (maketx)
    * .rs - Redshift (redshiftTextureProcessor)
    * .tiff - Dcraw (dcraw)
    * .exr - OpenImageIO (oiiotool)
    
    However it is easy to extend / modify this tool so that it suits your needs. Note that those are only presets. Those tools can handle more formats and can be customized for different cases. Check man pages of the tools for more information.

* To add new output format, simply implement a new class in **scripts/python/batch_convert/converters.py**, which inherits from **GenericCommand()** class. Class is very simple, so it should be straightforward to add your custom output formats.

* This tool relies on external executables to perform conversion (e.g. *iconvert* for *RAT*, *maketx* for *TX*...). Make sure that you have them available in your system's **PATH** variable. If an executable is not found, then it will print a warning and will hide it from the output formats list in gui.

* `batch_convert.runGui()` accepts optional argument: `path`, use it setting default folder path

* If there are multiple textures with the same name, but different extensions, the tool will pick the one with the highest priority, as specified in `ext_priority` list in `__init__.py`

* Check beggining of `__init__.py` for configuration

## Development
Create virtual environment.
```
python3 -m venv venv
```

Activate the environment and install dependencies in it.
```
source venv/bin/activate
pip install -r requirements.txt
```

### Guidelines
* Autoformat document with *autopep8*, with maximum line length set to 120 (VSCode is configured for it)
* Use type hints
* Write docs into docstrings, use google style
