import abc

class TextLibrary(metaclass=abc.ABCMeta):
    """Class for handling text drawing."""

    @abc.abstractmethod
    def load(self, filename):
        pass

    @abc.abstractmethod
    def draw(self, fontid, text):
        pass

    @abc.abstractmethod
    def dimensions(self, fontid, text):
        pass

    @abc.abstractmethod
    def position(self, fontid, x, y, z):
        pass

    @abc.abstractmethod
    def size(self, fontid, size, dpi):
        pass
