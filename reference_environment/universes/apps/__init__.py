"""ARE apps for the Bharat universes (see universes/blr_pranjal_01/app_schemas.md).

Importing this package registers every write tool with ARE's verifier and makes the
apps loadable by ARE's scenario importer.
"""

from .commerce import CommerceApp, KartBazaarApp, StyleGaliApp
from .common import BharatProtocol
from .dawaghar import DawaGharApp
from .grader import register_grader_settings
from .paysetu import PaySetuApp
from .railmitra import RailMitraApp
from .registration import register_with_are
from .safarhub import SafarHubApp
from .sehatcare import SehatCareApp
from .thalidash import ThaliDashApp

BHARAT_APP_CLASSES = (
    PaySetuApp,
    RailMitraApp,
    SafarHubApp,
    KartBazaarApp,
    StyleGaliApp,
    ThaliDashApp,
    SehatCareApp,
    DawaGharApp,
)

register_grader_settings()
register_with_are(BHARAT_APP_CLASSES)

__all__ = [
    "BHARAT_APP_CLASSES",
    "BharatProtocol",
    "CommerceApp",
    "DawaGharApp",
    "KartBazaarApp",
    "PaySetuApp",
    "RailMitraApp",
    "SafarHubApp",
    "SehatCareApp",
    "StyleGaliApp",
    "ThaliDashApp",
    "register_grader_settings",
    "register_with_are",
]
