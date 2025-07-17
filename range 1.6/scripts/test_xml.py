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
        self.cube = self.scene.objects["Cube"]
        theme_name = "default"
        self.gui_system = BGESystem(theme_name)
        
        script_dir = os.path.dirname(__file__)
        xml_path = os.path.join(script_dir, 'interface.xml')
        self.widgets = load_ui_from_xml(xml_path, self.gui_system.main_frame, theme=theme_name)
        self.slider = self.widgets.get("volume")
        
        def on_slider_change(value):
            scale = max(0.1, value / 50.0)  # Evita escala zero
            self.cube.localScale = [scale, scale, scale]
            print("Escala do cubo:", self.cube.localScale)
        
        self.slider.set_on_value_change(on_slider_change)

    def update(self):
        self.gui_system.run()
        
