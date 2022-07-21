from enum import Enum, unique


@unique
class Neighborhood(Enum):
    Miramesa = [92126, 92121]
    SDSU = [92115, 92120]
    Clairemont = [92117, 92111]
    OceanBeach = [92107]
    Encanto = [92114, 92139]
    AlliedGardens = [92119, 92120, 92124]

    # ... add more neighborhoods here
