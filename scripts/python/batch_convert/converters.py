import re
import os
import abc
import distutils.spawn

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
        if some reason conversion shouldn't happend, then returns None
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

class TxPRMan(GenericCommand):
    """
    converts textures for PRMan TX format  
    """
    @staticmethod
    def name():
        return "TX (PRMan)"

    @staticmethod
    def executable():
        return "maketx"

    @staticmethod
    def generateCommand(texture_in):
        texture_out = texture_in.split(".")
        texture_out[-1] = "tx"
        texture_out = ".".join(texture_out)

        return [TxPRMan.executable(), "-u", "--prman", "--checknan", "--filter", "lanczos3", texture_in, "-o", texture_out]

class TxArnold(GenericCommand):
    """
    converts textures for Arnold TX format  
    """
    @staticmethod
    def name():
        return "TX (Arnold)"

    @staticmethod
    def executable():
        return "maketx"

    @staticmethod
    def generateCommand(texture_in):
        texture_out = texture_in.split(".")
        texture_out[-1] = "tx"
        texture_out = ".".join(texture_out)

        return [TxArnold.executable(), "-u", "--oiio", "--checknan", "--filter", "lanczos3", texture_in, "-o", texture_out]

class Rs(GenericCommand):
    """
    converts textures for Redshift RS format  
    """
    @staticmethod
    def name():
        return "RSTEXBIN (Redshift, skip converted)"

    @staticmethod
    def executable():
        return "redshiftTextureProcessor"

    @staticmethod
    def generateCommand(texture_in):
        return [Rs.executable(), texture_in]

class RsNoSkip(GenericCommand):
    """
    converts textures for Redshift RS format, disables checking for already converted textures
    """
    @staticmethod
    def name():
        return "RSTEXBIN (Redshift, overwrite converted)"

    @staticmethod
    def executable():
        return "redshiftTextureProcessor"

    @staticmethod
    def generateCommand(texture_in):
        return [RsNoSkip.executable(), texture_in, "-noskip"]

class Dcraw(GenericCommand):
    """
    converts raw photos using dcraw utility into linear TIFF pictures in ACES2065-1 colorspace
    """
    @staticmethod
    def name():
        return "TIFF (dcraw, linear, ACES2065-1)"

    @staticmethod
    def executable():
        return "dcraw"

    @staticmethod
    def generateCommand(texture_in):
        return [Dcraw.executable(), "-4", "-T", "-v", "-o", "6", texture_in]

class Resize1K(GenericCommand):
    """
    scales image, it is expecting "_*K_" tag in file name, which will be replaced with "_1K_"
    """
    @staticmethod
    def name():
        return "Resize (1K, box, skip converted)"

    @staticmethod
    def executable():
        return "oiiotool"

    @staticmethod
    def generateCommand(texture_in):
        in_dir, in_file = os.path.split(texture_in)
        out_file = re.sub('_[0-9]K_', "_1K_", in_file)
        texture_out = os.path.join(in_dir, out_file)

        if texture_in != texture_out:
            return [Resize1K.executable(), texture_in, "-v", "--resize:filter=box", "1024x1024", "--no-clobber", "-o", texture_out]
        else:
            return None

class Resize2K(GenericCommand):
    """
    scales image, it is expecting "_*K_" tag in file name, which will be replaced with "_2K_"
    """
    @staticmethod
    def name():
        return "Resize (2K, box, skip converted)"

    @staticmethod
    def executable():
        return "oiiotool"

    @staticmethod
    def generateCommand(texture_in):
        in_dir, in_file = os.path.split(texture_in)
        out_file = re.sub('_[0-9]K_', "_2K_", in_file)
        texture_out = os.path.join(in_dir, out_file)

        if texture_in != texture_out:
            return [Resize2K.executable(), texture_in, "-v", "--resize:filter=box", "2048x2048", "--no-clobber", "-o", texture_out]
        else:
            return None

class Resize4K(GenericCommand):
    """
    scales image, it is expecting "_*K_" tag in file name, which will be replaced with "_4K_"
    """
    @staticmethod
    def name():
        return "Resize (4K, box, skip converted)"

    @staticmethod
    def executable():
        return "oiiotool"

    @staticmethod
    def generateCommand(texture_in):
        in_dir, in_file = os.path.split(texture_in)
        out_file = re.sub('_[0-9]K_', "_4K_", in_file)
        texture_out = os.path.join(in_dir, out_file)

        if texture_in != texture_out:
            return [Resize4K.executable(), texture_in, "-v", "--resize:filter=box", "4096x4096", "--no-clobber", "-o", texture_out]
        else:
            return None
