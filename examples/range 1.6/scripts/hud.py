from Range import *
import bgui
# Importing BGESystem from bge_utils is crucial, as it is the adapted version for BGE/Range.
from bgui.bge_utils import System as BGESystem
from collections import OrderedDict

class InGameHUD(types.KX_PythonComponent):
    """
    Python component to create an in-game HUD with health bar,
    stamina bar, minimap (placeholder), crosshair, and ammo counter.
    Uses bgui.ProgressBar for the health and stamina bars.
    Fixed TypeErrors in Image and Frame initialization.
    """
    args = OrderedDict([
        ("MaxHealth", 100.0),
        ("CurrentHealth", 100.0),
        ("MaxStamina", 100.0),
        ("CurrentStamina", 100.0),
        ("ClipAmmo", 30),
        ("TotalAmmo", 120),
        ("CrosshairImagePath", "crosshair.png")
    ])

    def start(self, args):
        self.scene = logic.getCurrentScene()
        self.gui_system = BGESystem("default")
        self.gui_system.group = "hud_group"

        self.max_health = float(args.get("MaxHealth", 100.0))
        self.current_health = float(args.get("CurrentHealth", self.max_health))
        self.max_stamina = float(args.get("MaxStamina", 100.0))
        self.current_stamina = float(args.get("CurrentStamina", self.max_stamina))
        self.current_clip_ammo = int(args.get("ClipAmmo", 30))
        self.total_ammo = int(args.get("TotalAmmo", 120))
        self.crosshair_image_path = args.get("CrosshairImagePath", "crosshair.png")

        self._setup_health_bar()
        self._setup_stamina_bar()
        self._setup_minimap_placeholder()
        self._setup_crosshair()
        self._setup_ammo_counter()

    def _setup_health_bar(self):
        self.health_bar = self.gui_system.add_element(
            bgui.ProgressBar, "health_bar_widget",  # Giving an explicit widget name
            size=[0.2, 0.03],
            pos=[0.02, 0.02],
            percent=self.current_health / self.max_health if self.max_health > 0 else 0,
            options=bgui.BGUI_NO_FOCUS
        )
        self._update_health_bar_visuals()

    def _setup_stamina_bar(self):
        self.stamina_bar = self.gui_system.add_element(
            bgui.ProgressBar, "stamina_bar_widget",  # Giving an explicit widget name
            size=[0.2, 0.03],
            pos=[0.02, 0.06],
            percent=self.current_stamina / self.max_stamina if self.max_stamina > 0 else 0,
            options=bgui.BGUI_NO_FOCUS
        )
        self.stamina_bar.fill_colors = [(0.1, 0.7, 0.9, 0.9)] * 4

    def _setup_minimap_placeholder(self):
        map_size_w, map_size_h = 0.15, 0.20
        margin = 0.02
        
        # For bgui.Frame, 'colors' is not a kwarg of __init__
        self.minimap_frame = self.gui_system.add_element(
            bgui.Frame, "minimap_frame_widget",  # Giving an explicit widget name
            size=[map_size_w, map_size_h],
            pos=[1.0 - map_size_w - margin, 1.0 - map_size_h - margin],
            options=bgui.BGUI_NO_FOCUS
        )
        self.minimap_frame.border = 1
        self.minimap_frame.colors = [(0.05, 0.05, 0.05, 0.6)] * 4

        self.gui_system.add_element(
            bgui.Label, "minimap_label_widget", parent=self.minimap_frame, text="Minimap",  # Giving an explicit widget name
            pos=[0.1, 0.4],
            options=bgui.BGUI_CENTERX | bgui.BGUI_NO_FOCUS
        )

    def _setup_crosshair(self):
        crosshair_img_size_w = 0.04
        aspect_ratio = render.getWindowHeight() / render.getWindowWidth()
        crosshair_img_size_h = crosshair_img_size_w * aspect_ratio

        pos_x = 0.5 - (crosshair_img_size_w / 2)
        pos_y = 0.5 - (crosshair_img_size_h / 2)

        try:
            # Fix for Image.__init__
            # The second argument to add_element (if Image) must be the image path.
            # The widget 'name' is passed as a keyword argument.
            self.crosshair_image = self.gui_system.add_element(
                bgui.Image,
                self.crosshair_image_path,  # This is the positional 'img' argument
                name="crosshair_image_widget",  # This is the widget 'name' (via kwargs)
                size=[crosshair_img_size_w, crosshair_img_size_h],
                pos=[pos_x, pos_y],
                options=bgui.BGUI_NO_FOCUS
            )
        except Exception as e:
            print(f"HUD Error: Could not load crosshair image '{self.crosshair_image_path}': {e}. Using fallback crosshair.")
            cross_line_len = 0.015
            cross_line_thick = 0.002
            center_x, center_y = 0.5, 0.5
            color_tuple = (0.9, 0.9, 0.9, 0.7)  # Renamed to avoid conflict with 'color' module

            # Fix for Frame.__init__ (colors is not a kwarg)
            crosshair_h_left = self.gui_system.add_element(bgui.Frame, "crosshair_h_left",
                size=[cross_line_len, cross_line_thick],
                pos=[center_x - cross_line_len - cross_line_thick / 2, center_y - cross_line_thick / 2],
                options=bgui.BGUI_NO_FOCUS)
            crosshair_h_left.colors = [color_tuple]*4

            crosshair_h_right = self.gui_system.add_element(bgui.Frame, "crosshair_h_right",
                size=[cross_line_len, cross_line_thick],
                pos=[center_x + cross_line_thick / 2, center_y - cross_line_thick / 2],
                options=bgui.BGUI_NO_FOCUS)
            crosshair_h_right.colors = [color_tuple]*4

            crosshair_v_top = self.gui_system.add_element(bgui.Frame, "crosshair_v_top",
                size=[cross_line_thick, cross_line_len],
                pos=[center_x - cross_line_thick / 2, center_y + cross_line_thick / 2],
                options=bgui.BGUI_NO_FOCUS)
            crosshair_v_top.colors = [color_tuple]*4

            crosshair_v_bottom = self.gui_system.add_element(bgui.Frame, "crosshair_v_bottom",
                size=[cross_line_thick, cross_line_len],
                pos=[center_x - cross_line_thick / 2, center_y - cross_line_len - cross_line_thick / 2],
                options=bgui.BGUI_NO_FOCUS)
            crosshair_v_bottom.colors = [color_tuple]*4


    def _setup_ammo_counter(self):
        pos_x = 0.98
        pos_y = 0.02
        self.ammo_label = self.gui_system.add_element(
            bgui.Label, "ammo_label_widget",  # Giving an explicit widget name
            text=f"{self.current_clip_ammo} / {self.total_ammo}",
            pos=[pos_x, pos_y],
            options=bgui.BGUI_NO_FOCUS
        )

    def _update_health_bar_visuals(self):
        if not hasattr(self, 'health_bar'): return

        health_ratio = self.current_health / self.max_health if self.max_health > 0 else 0
        self.health_bar.percent = health_ratio

        if health_ratio < 0.3:
            self.health_bar.fill_colors = [(0.9, 0.1, 0.1, 0.9)] * 4
        elif health_ratio < 0.6:
            self.health_bar.fill_colors = [(0.9, 0.9, 0.1, 0.9)] * 4
        else:
            self.health_bar.fill_colors = [(0.1, 0.8, 0.1, 0.9)] * 4

    def set_health(self, current, maximum):
        self.current_health = max(0.0, float(current))
        self.max_health = max(0.01, float(maximum))
        if self.max_health == 0 and self.current_health > 0:  # Fix: max_health should never be 0 if current_health > 0
            self.max_health = self.current_health
        elif self.max_health <= 0: self.max_health = 0.01  # Prevents division by zero

        self._update_health_bar_visuals()

    def set_stamina(self, current, maximum):
        self.current_stamina = max(0.0, float(current))
        self.max_stamina = max(0.01, float(maximum))  # Prevents division by zero
        if self.max_stamina == 0 and self.current_stamina > 0:
            self.max_stamina = self.current_stamina
        elif self.max_stamina <= 0: self.max_stamina = 0.01

        if hasattr(self, 'stamina_bar'):
            stamina_ratio = self.current_stamina / self.max_stamina if self.max_stamina > 0 else 0
            self.stamina_bar.percent = stamina_ratio

    def set_ammo(self, clip_ammo, total_ammo):
        self.current_clip_ammo = int(clip_ammo)
        self.total_ammo = int(total_ammo)
        if hasattr(self, 'ammo_label'):
            self.ammo_label.text = f"{self.current_clip_ammo} / {self.total_ammo}"

    def update(self):
        if hasattr(self, 'gui_system') and self.gui_system:
            self.gui_system.run()

    def cleanup(self):
        if hasattr(self, 'gui_system') and self.gui_system:
            self.gui_system.cleanup()
            print("HUD: GUI system cleaned up.")
