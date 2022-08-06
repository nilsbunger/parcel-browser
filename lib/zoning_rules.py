import math

ZONING_FRONT_SETBACKS_IN_FEET = {
    "RS-1-1": 25,
    "RS-1-2": 25,
    "RS-1-3": 20,
    "RS-1-4": 20,
    "RS-1-5": 20,
    "RS-1-6": 15,
    "RS-1-7": 15,
    "RS-1-8": 25,
    "RS-1-9": 25,
    "RS-1-10": 25,
    "RS-1-11": 20,
    "RS-1-12": 15,
    "RS-1-13": 15,
    "RS-1-14": 15,
    "RM-1-1": 15,   # RM zone setbacks are a minimum for 50% of frontage, and minimum+5' for other 50%.
    "RM-1-2": 15,
    "RM-1-3": 15,
    "RM-2-4": 15,
    "RM-2-5": 15,
    "RM-2-6": 15,
    "RM-3-7": 10,
    "RM-3-8": 10,
    "RM-3-9": 10,
    "RM-4-10": 15,  # "Varies" according to table, need to check
    "RM-4-11": 15,  # "Varies" according to table, need to check
    "RM-5-12": 15,
}

ZONING_FAR = {
    "RS-1-1": 0.45,
    "RS-1-8": 0.45,
    "RS-1-9": 0.6,
    "RS-1-10": 0.6,
    "RS-1-11": 0.6,
    "RS-1-12": 0.6,
    "RS-1-13": 0.6,
    "RS-1-14": 0.6,
    "RM-1-1": 0.75,
    "RM-1-2": 0.9,
    "RM-1-3": 1.05,
    "RM-2-4": 1.2,
    "RM-2-5": 1.35,
    "RM-2-6": 1.5,
    "RM-3-7": 1.8,
    "RM-3-8": 2.25,
    "RM-3-9": 2.7,
    "RM-4-10": 3.6,
    "RM-4-11": 7.2,
    "RM-5-12": 1.8,
}

ZONING_HEIGHT = {
    "RS-1": 24,
    "RM-1": 30,
    "RM-2": 40
}


def get_far(zone, lot_size):
    # Check 131.0446. Table 131-04J.
    # Convert lot size to sqft
    lot_size_sqft = lot_size * 10.7639

    # Use the table if there's an entry
    if zone in ZONING_FAR:
        return ZONING_FAR[zone]

    # Otherwise, compute based on formula on the table
    if lot_size_sqft <= 3000:
        return 0.7
    elif lot_size_sqft <= 4000:
        return 0.65
    elif lot_size_sqft >= 19001:
        return 0.45
    else:
        return 0.6 - 0.01 * (math.ceil(lot_size_sqft / 1000) - 5)
