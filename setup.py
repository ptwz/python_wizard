from distutils.core import setup
import setuptools

setup(
    name = "pywizard",
    version = '1.4.3',
    description = 'A tool to convert Wave-Files to LPC bytestreams used by TMS5220 chips and emulators like the Arduino Talkie library',
    url = 'http://github.com/ptwz/python_wizard',
    author = 'Peter Turczak (python port), Patrick J. Collins (original code and most of the work), Special thanks to: Richard Wiggins Jonathan Gevaryahu Gene Frantz Frank Palazzolo',
    license = 'MIT',
    packages = ["pywizard"],
    install_requires=['scipy'],
    python_requires = '>=3.5',
    scripts = ['python_wizard', 'python_wizard_gui']
)
