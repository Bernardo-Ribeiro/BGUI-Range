#Slider still doesn't work 100%

from Range import *
from bgui import *
from bgui.bge_utils import System as BGESystem
from collections import OrderedDict

# This script should be attached to an object in the scene
# and set to always execute (Always)

class SimpleSlider(types.KX_PythonComponent):
    # Arguments exposed in the UI
    args = OrderedDict([
        ("ContainerFrameSize", [200, 80]),  # Size of the frame containing the slider and label
        ("ContainerFramePosition", [10, 10]), # Position of the frame on the screen
        ("SliderSize", [180, 20]),  # Size of the slider in pixels, relative to ContainerFrame
        ("SliderPosition", [10, 50]),  # Position of the slider in pixels, relative to ContainerFrame
        ("MinValue", 0.0),  # Minimum value
        ("MaxValue", 1.0),  # Maximum value
        ("InitialValue", 0.5),  # Initial value
        ("ShowLabel", True),  # Whether to show the label
        ("LabelPosition", [10, 15])  # Position of the label in pixels, relative to ContainerFrame
    ])

    def awake(self, args):
        # Initialize the UI system
        self.system = BGESystem("default")
        self.system.group = "slider_group"

        # Get arguments
        self.container_frame_size_px = args.get("ContainerFrameSize", [200, 80])
        self.container_frame_pos_px = args.get("ContainerFramePosition", [10, 10])
        self.slider_size_px = args.get("SliderSize", [180, 20])
        self.slider_pos_px = args.get("SliderPosition", [10, 50])
        self.min_value = float(args.get("MinValue", 0.0))
        self.max_value = float(args.get("MaxValue", 1.0))
        self.initial_value = float(args.get("InitialValue", 0.5))
        self.show_label = args.get("ShowLabel", True)
        self.label_pos_px = args.get("LabelPosition", [10, 15])

    def start(self, args):
        # Create a frame to contain the slider and label.
        # This frame uses BGUI_NO_NORMALIZE, so its 'size' and 'pos' are in pixels.
        self.container_frame = self.system.add_element(
            Frame,
            "container_frame_for_slider",
            size=self.container_frame_size_px,
            pos=self.container_frame_pos_px,
            options=BGUI_NO_NORMALIZE # Important: dimensions in pixels
        )

        # Normalize the slider's size and position relative to the container_frame
        norm_slider_size = [
            self.slider_size_px[0] / self.container_frame_size_px[0] if self.container_frame_size_px[0] != 0 else 0,
            self.slider_size_px[1] / self.container_frame_size_px[1] if self.container_frame_size_px[1] != 0 else 0
        ]
        norm_slider_pos = [
            self.slider_pos_px[0] / self.container_frame_size_px[0] if self.container_frame_size_px[0] != 0 else 0,
            self.slider_pos_px[1] / self.container_frame_size_px[1] if self.container_frame_size_px[1] != 0 else 0
        ]

        # Create the slider as a child of the container_frame
        # Its 'size' and 'pos' are normalized, and it uses options=0 (default)
        self.slider = self.system.add_element(
            Slider,
            "slider_widget",
            parent=self.container_frame,
            value=self.initial_value,
            min_value=self.min_value,
            max_value=self.max_value,
            size=norm_slider_size,
            pos=norm_slider_pos,
            options=0 # Default, expects normalized size/pos
        )

        # Add a label to show the value if needed
        if self.show_label:
            # Normalize the label's position relative to the container_frame
            norm_label_pos = [
                self.label_pos_px[0] / self.container_frame_size_px[0] if self.container_frame_size_px[0] != 0 else 0,
                self.label_pos_px[1] / self.container_frame_size_px[1] if self.container_frame_size_px[1] != 0 else 0
            ]
            self.value_label = self.system.add_element(
                Label,
                "slider_label_widget",
                parent=self.container_frame,
                text=f"{self.initial_value:.2f}",
                pos=norm_label_pos,
                options=0 # Default, expects normalized pos
            )
            self.slider.set_on_value_change(self._on_slider_change)
        
    def update(self):
        # Update the UI system
        if hasattr(self, 'system'):
            self.system.run()
        
    def _on_slider_change(self, value):
        # Update the label with the new value
        if hasattr(self, 'value_label'):
            self.value_label.text = f"{value:.2f}"
            
    def set_value(self, value):
        """Sets the slider value"""
        if hasattr(self, 'slider'):
            self.slider.value = value
            
    def get_value(self):
        """Returns the current slider value"""
        if hasattr(self, 'slider'):
            return self.slider.value
        return 0.5

    def cleanup(self):
        """Cleans up resources when the component is removed"""
        if hasattr(self, 'system'):
            self.system.cleanup()
            print("Slider: GUI system cleaned up.") 