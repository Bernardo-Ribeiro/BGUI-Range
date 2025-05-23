import os
import blf
from .textlibrary import TextLibrary

class BlfTextLibrary(TextLibrary):
    def draw(self, fontid, text):
        blf.draw(fontid, text)

    def size(self, fontid, size, dpi):
        blf.size(fontid, size, dpi)

    def position(self, fontid, x, y, z):
        blf.position(fontid, x, y, z)

    def dimensions(self, fontid, text):
        return blf.dimensions(fontid, text)

    def load(self, filename):
        base_path = os.path.dirname(__file__)
        full_path = os.path.join(base_path, '..', 'fonts', filename)
        full_path = os.path.normpath(full_path)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Font not found: {full_path}")

        return blf.load(full_path)
