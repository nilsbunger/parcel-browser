from enum import Enum, unique


# Zip code map: https://www.titleadvantage.com/mdocs/SD_ZipCodes_South.pdf
@unique
class Neighborhood(Enum):
    Miramesa = [92126, 92121]
    SDSU = [92115, 92120, 92116, 92105]
    Clairemont = [92117, 92111, 92110]
    OceanBeach = [92107, 92106, 92133, 92140]
    Encanto = [92114, 92139]
    AlliedGardens = [92119, 92120, 92124]
    PacificBeach = [92109]


AllSdCityZips = [
    92014, 92037, 92042, 92091, 92093, 92101,
    92102, 92103, 92104, 92105, 92106, 92107, 92108, 92109, 92110, 92111, 92113, 92114, 92115, 92116, 92117, 92118,
    92119, 92120, 92121, 92122, 92123, 92124, 92126, 92127, 92128, 92129, 92130, 92131, 92134, 92136, 92137, 92139,
    92140, 92145, 92154, 92155, 92170, 92173, 92176, 92177, 92182,
]
# 92127 is black mountain ranch , it seems to be partially in SD city.

# ... add more neighborhoods here
