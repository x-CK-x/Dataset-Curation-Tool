from krita import Krita
from .krita_dataset_bridge import KritaDatasetBridgeExtension

Krita.instance().addExtension(KritaDatasetBridgeExtension(Krita.instance()))
