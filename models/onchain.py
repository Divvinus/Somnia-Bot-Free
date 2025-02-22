from dataclasses import dataclass


@dataclass
class Erc20Contract:
    abi: list = open("./abi/erc_20.json", "r").read()