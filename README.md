# bgui - Range

**bgui - Range** is an adaptation of the Python library **bgui** for handling graphical user interfaces (GUI) in the Range Engine.

**Adaptation author:** Bernardo Ribeiro  
**Email:** bernardo.ribeiro@outlook.com.br

**Original base:** [bgui by Mitchell Stokes (Moguri)](mailto:mogurijin@gmail.com)  
**Original documentation:** [http://bgui.readthedocs.org/en/latest/](http://bgui.readthedocs.org/en/latest/)

---

## Important Notice

**This project is under development!**
Some features may not be working properly or have not yet been adapted.

---

## How to Use

1. Go to the `range 1.6` directory, which contains the standard project hierarchy.
2. Use the `bgui` folder directly in your Range Engine project.
3. Usage examples can be found in `range 1.6/scripts/` (e.g., `slider_example.py`, `test_ui.py`).
4. Example `.range` files are also available for reference.

> **Tip:** Just keep the `bgui` folder at the root of your Range Engine project to start using it.

---

## XML UI Editor - How to Use

The project includes a visual tool to create and edit BGUI XML files in your browser.

1. Open `tools/xml_ui_editor.html` in your local browser.
2. In the **Hierarchy** panel, click **Load XML** to import an existing interface file, or start from scratch.
3. In the **Inspector** panel, fill widget fields (type, name, pos, size, text, etc.) and click **Add widget**.
4. Use the widget list to **Edit**, **Up**, **Down**, or **Delete** existing widgets.
5. In the **Viewport** panel, use the 16:9 preview as a visual reference while building the interface.
6. Optionally load a theme using **Load default theme.cfg** or by selecting a custom theme file.
7. Click **Generate XML** to refresh the output text.
8. Click **Save XML** to write directly to a file (when browser permissions allow), or **Download interface.xml** as a fallback.

### Notes

- The viewport is currently a preview-only area (no drag-and-drop editing yet).
- Browser CSS rendering may differ slightly from in-game OpenGL rendering.
- The generated XML is compatible with the BGUI XML loader used in this project.

---

## Contribute!

Feel free to contribute to the project, report issues, or suggest improvements.