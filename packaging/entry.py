"""Entry point used by PyInstaller to build StickOfTruth-SaveConverter.exe."""
import sys

from sot_save_converter.cli import main

sys.exit(main())
