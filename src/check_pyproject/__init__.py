from usingversion import getattr_with_version

# version      set to the application's version from the pyproject.toml file.
__getattr__ = getattr_with_version("check_pyproject", __file__, __name__)
