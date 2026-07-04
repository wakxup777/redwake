"""PyInstaller runtime hook: strip __doc__ and other metadata from license module
classes to make reverse engineering harder."""
import sys

# Strip identifying metadata from the license module after import
try:
    import redwake.license  # noqa: F401

    for mod_name in list(sys.modules):
        if mod_name.startswith("redwake.license"):
            mod = sys.modules[mod_name]
            for attr in ("__doc__", "__file__", "__cached__", "__loader__"):
                if hasattr(mod, attr):
                    try:
                        setattr(mod, attr, "")
                    except Exception:
                        pass
except Exception:
    pass
