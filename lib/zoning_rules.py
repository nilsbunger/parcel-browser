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
