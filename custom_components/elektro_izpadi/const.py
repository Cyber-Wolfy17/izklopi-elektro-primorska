"""Constants for the Elektro Primorska izpadi integration."""

DOMAIN = "elektro_izpadi"

CONF_KRAJ = "kraj"
CONF_HISNA_STEVILKA = "hisna_stevilka"
CONF_OBMOCJE = "obmocje"
CONF_UPDATE_INTERVAL = "update_interval"

API_URL = "https://elektro-primorska.si/wp-admin/admin-ajax.php"
TIMEZONE = "Europe/Ljubljana"
DATETIME_FORMAT = "%d.%m.%Y %H:%M"

DEFAULT_UPDATE_INTERVAL = 30
MIN_UPDATE_INTERVAL = 5
MAX_UPDATE_INTERVAL = 1440

MAX_LISTED_OUTAGES = 10

OBMOCJA = {
    "vsi": "Vsa nadzorništva",
    "ajdovscina": "Ajdovščina",
    "bilje": "Bilje",
    "bovec": "Bovec",
    "cerkno": "Cerkno",
    "dekani": "Dekani",
    "gorica": "Nova Gorica",
    "idrija": "Idrija",
    "ilbistrica": "Ilirska Bistrica",
    "izola": "Izola",
    "kanal": "Kanal",
    "kobarid": "Kobarid",
    "koper": "Koper",
    "kozina": "Kozina",
    "piran": "Piran",
    "pivka": "Pivka",
    "postojna": "Postojna",
    "sezana": "Sežana",
    "tolmin": "Tolmin",
}
