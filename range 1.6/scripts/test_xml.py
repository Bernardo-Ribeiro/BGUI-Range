import os
from Range import *
from bgui.bge_utils import System as BGESystem
from collections import OrderedDict
from bgui.xml_loader import load_ui_from_xml

class MainMenu(types.KX_PythonComponent):
    args = OrderedDict({
    })
    def start(self, args):
        self.scene = logic.getCurrentScene()
        theme_name = "default"
        self.gui_system = BGESystem(theme_name)

        script_dir = os.path.dirname(__file__)
        xml_path = os.path.join(script_dir, 'interface.xml')
        self.widgets = load_ui_from_xml(xml_path, self.gui_system, theme=theme_name)

    def update(self):
        self.gui_system.run()
