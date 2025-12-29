from Range import *
import bgui
from bgui.bge_utils import System as BGESystem
from collections import OrderedDict


class MainMenu(types.KX_PythonComponent):
    args = OrderedDict({
    })
    def start(self,args):
        self.scene = logic.getCurrentScene()
        theme_name = "default"
        
        self.gui_system = BGESystem(theme_name)

        self.btn_solid = self.gui_system.add_element(
            bgui.FrameButton,
            "btn_solid",
            text="Solid Button",
            pos=[0.3, 0.6],
            size=[0.4, 0.1],
            solid_color=True
        )
        self.btn_solid.on_click = self.on_button_click 

        self.btn_gradient = self.gui_system.add_element(
            bgui.FrameButton,
            "btn_gradient", 
            text="Gradient Button",
            pos=[0.3, 0.4],
            size=[0.4, 0.1],
            solid_color=False
        )
        self.btn_gradient.on_click = self.on_button_click

        self.btn_custom = self.gui_system.add_element(
            bgui.FrameButton,
            "btn_custom",
            text="Custom Color",
            pos=[0.3, 0.2],
            size=[0.4, 0.1],
            base_color=(0.91, 0.47, 0.45, 1.0), 
            solid_color=False
        )
        self.btn_custom.on_click = self.on_button_click

        self.original_colors = {
            "btn_solid": self.btn_solid.base_color,
            "btn_gradient": self.btn_gradient.base_color,
            "btn_custom": self.btn_custom.base_color,
        }

    def on_button_click(self, button):
        clicked_button_name = button.name
        new_color = (0.2, 0.6, 0.8, 1.0)

        for btn_name, original_color in self.original_colors.items():
            current_button = self.gui_system.get_element(btn_name)
            if btn_name == clicked_button_name:
                current_button.set_base_color(new_color)
            else:
                current_button.set_base_color(original_color)

    def update(self):
        self.gui_system.run()
