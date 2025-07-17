import xml.etree.ElementTree as ET
from .label import Label
from .widget import Widget
from .slider import Slider
from .frame_button import FrameButton
from .progress_bar import ProgressBar
# Add other widget imports as needed

# Mapping XML tag names to BGUI widget classes
WIDGET_MAP = {
    'Label': Label,
    'Slider': Slider,
    'Button': FrameButton,
    'ProgressBar': ProgressBar,
}

def load_ui_from_xml(xml_path, parent, theme=None):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    widgets = []
    for elem in root:
        widget = create_widget_from_elem(elem, parent)
        if widget:
            widgets.append(widget)
    return {w.name: w for w in widgets if hasattr(w, "name")}

def create_widget_from_elem(elem, parent):
    widget_type = elem.tag
    widget_class = WIDGET_MAP.get(widget_type)
    if not widget_class:
        print(f"Unknown widget type: {widget_type}")
        return None
    # Convert XML attributes to widget constructor arguments
    kwargs = {k: try_parse_widget_arg(k, v) for k, v in elem.attrib.items()}
    # Ensure 'parent' is the first argument
    widget = widget_class(parent, **kwargs)
    # Recursively create children, if any
    for child in elem:
        create_widget_from_elem(child, widget)
    return widget

def try_parse_widget_arg(key, value):
    # Convert comma-separated strings to lists of floats for certain attributes
    if key in ("pos", "size", "base_color", "color", "outline_color", "fill_color", "fill_colors"):
        return [float(x) for x in value.split(",")]
    # Try to convert to int or float, otherwise keep as string
    for fn in (int, float):
        try:
            return fn(value)
        except ValueError:
            continue
    return value 