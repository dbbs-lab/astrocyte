import os

__version__ = "0.0.1"

class Package:
  def __init__(self):
    self.mods = []

class Mod:
  pass

def package():
  pkg = Package()
  pkg.name = os.path.basename(os.path.dirname(__file__))

  return pkg
