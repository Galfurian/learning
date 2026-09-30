"""A tiny discrete-time simulator of a production cell.

The recipe (YAML) says which stations exist, how parts flow through them and
which faults happen. The behavior of each station type is Python code in
``factory/stations/``. Running the simulation produces one log per station.

    factory = Factory.from_yaml("recipes/default.yaml")
    factory.run()
    factory.logbook.lines("M1")
    factory.truth()
"""

from .config import Recipe, load_recipe
from .factory import Factory
from .part import Part
from .station import Station, station

__all__ = ["Factory", "Part", "Recipe", "Station", "load_recipe", "station"]
