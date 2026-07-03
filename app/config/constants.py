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

PACKING_TYPE_ICONS = {
    PackingType.CARTON: "bi bi-box-seam text-warning",
    PackingType.LOSS_PALLET: "bi bi-layers text-danger",
    PackingType.EURO_PALLET: "bi bi-grid-3x2-gap text-info",
    PackingType.SACK: "bi bi-bag text-success",
    PackingType.BARREL: "bi bi-database text-primary",
    PackingType.BIG_BAG: "bi bi-basket text-secondary",
}

LABEL_TYPE_MAP = {
    "1": True,
    "2": False,
    "3": False,
    "4": False,
    "5": False,
    "6": False,
}

ID_PAGAMENTI_ALLA_CONSEGNA = [
    "200", "201", "202", "203", "204",
    "205", "206", "207", "208", "209",
    "210", "211", "212",
    "320", "370"
]