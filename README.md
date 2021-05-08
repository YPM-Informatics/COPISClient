# COPIS Client

COPIS (Computer-Operated Photogrammetric Imaging System) is a desktop application which captures large numbers of overlapping images from multiple viewpoints around an object for photogrammetric 3D reconstruction.

For more information, see the project page at [copis3d.org](http://copis3d.org/).

![Screenshot](img/screenshot.jpg)

## Getting Started

### Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install any necessary project dependencies.

```bash
pip install -r requirements.txt
```

If you have both Python 2.x and 3.x versions installed, you may need to specify:

```bash
python3 -m pip install -r requirements.txt
```
__Note: This project supports Python version 3.x.x.__
### Usage

To start the application from the project root, run:
```bash
python copis/client.py
```
Or, using the start script in that folder, run:
```bash
python copisclient.py
```
*Note: These 2 commands can be run from any folder in the project directory tree.*
### Configuration File

The configuration file `config.ini` contains initialization settings.

## License

COPIS Client as a whole is licensed under the GNU General Public License, Version 3. Please note that files where it is difficult to state this license note (such as images) are distributed under the same terms.

Credit to some parts of the source code go to [Printrun](https://github.com/kliment/Printrun) and [PrusaSlicer](https://github.com/prusa3d/PrusaSlicer).
