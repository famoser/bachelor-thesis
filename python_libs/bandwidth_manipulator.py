import pickle
import os
import json
import time
import requests as request
import datetime
import psutil
import subprocess
import time
import json

from .config import StaticConfig

config = StaticConfig()


class BandwidthManipulator:
    def __enter__(self):
        self.clear_rate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear_rate()

    @staticmethod
    def set_rate(rate: str = "1M"):
        os.system("sudo tcset --device " + config.network_device + " --direction incoming --rate " + rate + " --overwrite")

    @staticmethod
    def clear_rate():
        os.system("sudo tcdel --device " + config.network_device + " --all")
