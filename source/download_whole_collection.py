"""
Download all the graphic data of the specified NFT according
to the given blockchain category and contract address


"""

import json
import multiprocessing as mp
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen

import requests
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.file_io as fio
import utils.spider_toolbox as stb
from utils.downloading_toolbox import NFT_Downloader_for_Whole_Collection
from CONST_ENV import CONST_ENV as ENV

from pathlib import Path
from internetdownloadmanager import Downloader


def remove_special_char(string):
    """去除字符串中的特殊字符

    Args:
        string (str): 输入字符串

    Returns:
        str: 返回去除特殊字符后的字符串
    """
    special_char = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|"]
    for char in special_char:
        string = string.replace(char, " ")
    return string




def get_target_collection_info(chain_type, contract_address) -> dict:
    """获取目标NFT项目的信息

    Args:
        ranking (int): NFT项目的排名

    Returns:
        dict: 返回NFT项目的信息
    """
    info_dict = {
        "chain_type": chain_type,
        "contract_address": contract_address,
        "NFT_name": "",
        "total_supply": 1000,
        "candidate_format": "png",
        "get_start_file_index": 0
    }




if __name__ == "__main__":

    NFT_downloader = NFT_Downloader_for_Whole_Collection(chain_type="Ethereum",
                                                        contract_address="0x495f947276749ce646f68ac8c248420045cb7b5e",
                                                        save_path=ENV.DATASET_PATH,
                                                        process_num=8)
    NFT_downloader.download_media_and_metadata()