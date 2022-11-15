import slicer, importlib, functools
from Utils import BusyCursor

def check_and_install_package(module_names, pip_install_name, pre_install_hook=None):
    """
    Check if given module can be imported, and if not then prompt user to possibly attempt an install.
    Args:
      module_names: a list of strings for the modules for which import needs to succeed
      pip_install_name: the name of the package to install using pip in order to make the import succeed
        (or whatever text should follow "pip install" in the installation command)
      pre_install_hook: an optional callable that will be called before installation, in the event that installation is going to take place
    Returns whether the import can succeed at the end.
    """
    try:
        modules = []
        for module_name in module_names:
            modules.append(importlib.import_module(module_name))
        version_text = "\n".join(
            [
                f"  {module_name} version: {module.__version__}"
                for module, module_name in zip(modules, module_names)
                if hasattr(module, "__version__")
            ]
        )
        slicer.util.infoDisplay("Modules found!\n" + version_text, "Modules Found")
        return True
    except ModuleNotFoundError as e1:
        wantInstall = slicer.util.confirmYesNoDisplay(f"Package was not found. Install it?\nDetails of missing import: {e1}", "Missing Dependency")
        if wantInstall:
            if pre_install_hook is not None:
                pre_install_hook()
            with BusyCursor.BusyCursor():
                slicer.util.pip_install(pip_install_name)
            try:
                for module_name in module_names:
                    importlib.import_module(module_name)
                slicer.util.infoDisplay("Finished installing.", "Install Success")
                return True
            except ModuleNotFoundError as e2:
                slicer.util.errorDisplay("Unable to install package. Check the console for details.", "Install Error")
                print(e2)
                return False

check_and_install_fhirclient = functools.partial(check_and_install_package, ["fhirclient"], "fhirclient")