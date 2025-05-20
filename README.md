# bgui

**bgui** is a Python library for handling GUIs in the Blender Game Engine.

**Author:** Mitchell Stokes (Moguri)
**Email:** [mogurijin@gmail.com](mailto:mogurijin@gmail.com)

**Documentation:** [http://bgui.readthedocs.org/en/latest/](http://bgui.readthedocs.org/en/latest/)

---

## Important Notice

**This project is still under development!**
Some functions may not work yet because they haven’t been fixed.
For example: recognizing mouse clicks on the button.

---


## Changelog

### New Features

* Added the class that adapts BGUI to work with Range (`RangeBGUI`).
* Modified the text directory to better support the `TextLibrary` function call.
  *Note:* This code was previously in the `__init__` method but did not work properly there. Since Range does not have `logic.textLib`, the `BlfTextLibrary` and `TextLibrary` classes are used instead.
* Removed the use of PyQt4.

---

**Implementation with Range Engine**

**Author:** Bernardo Ribeiro
**Email:** bernardo.ribeiro@outlook.com.br

---

## How to Use

Open the directory `\examples\range 1.6`, where you’ll find the standard folder hierarchy used in the project.
Simply keep the `bgui` folder and the `range_bgui_adapter.py` file in the root directory of your project, and it will work right away.

(A basic `.Range` file was created just to demonstrate how it works.)


## Feel free to contribute to the project!