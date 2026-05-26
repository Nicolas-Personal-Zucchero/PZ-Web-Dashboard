import pytz
from dachser_edi import PackingType

ITALY_TZ = pytz.timezone("Europe/Rome")

ZEBRA_IP = "192.168.1.172"

PACKING_TYPE_MAP = {
        1: PackingType.CARTON,
        2: PackingType.LOSS_PALLET,
        3: PackingType.EURO_PALLET,
        4: PackingType.LOSS_PALLET,
        5: PackingType.LOSS_PALLET,
        6: PackingType.SACK,
        7: None, #Non presente su mexal al 18-05-26
        8: PackingType.BARREL,
        9: None, #Non presente su mexal al 18-05-26
        10: PackingType.BIG_BAG,
        11: None, #Non presente su mexal al 18-05-26
        12: PackingType.LOSS_PALLET,
        13: PackingType.CARTON,
        14: PackingType.CARTON,
        15: PackingType.CARTON,
        16: PackingType.CARTON,
        17: PackingType.CARTON,
        18: PackingType.LOSS_PALLET,
        19: PackingType.LOSS_PALLET,
    }

LABEL_TYPE_MAP = {
    "1": True,
    "2": False,
    "3": True,
    "4": False,
    "5": False,
    "6": True,
}