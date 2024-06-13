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
from utils.downloading_toolbox import NFT_Downloader_for_Whole_Collection_Alchemy
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




def filter_valid_keys(data):
    """ 过滤字典中的有效键 """
    valid_keys={'NFT_name', 'chain_type', 'contract_address', 'total_supply', 'candidate_format', 'start_index'}
    return {k: v for k, v in data.items() if k in valid_keys}






if __name__ == "__main__":

    chain_type = "ethereum"
    contract_address = "0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb"

    target_collection_info = fio.load_json(ENV.INFO_PATH / "target_collection_info.json")
    if target_collection_info is None:
        # 创建文件并保存
        collection_info = stb.get_target_collection_info(chain_type= chain_type, contract_address= contract_address)
        collection_info_json = {contract_address: collection_info}
        fio.save_json(ENV.INFO_PATH / "target_collection_info.json", collection_info_json)

    elif target_collection_info.get(contract_address) is None:
        # 更新文件并保存
        collection_info = stb.get_target_collection_info(chain_type= chain_type, contract_address= contract_address)
        target_collection_info[contract_address] = collection_info
        fio.save_json(ENV.INFO_PATH / "target_collection_info.json", target_collection_info)
    else:
        collection_info = target_collection_info[contract_address]

    # 将NFT项目的信息传入下载器中，开始下载
    arg_dict = filter_valid_keys(collection_info)
    NFT_downloader = NFT_Downloader_for_Whole_Collection_Alchemy(**arg_dict, save_path=ENV.DATASET_PATH)
    NFT_downloader.download_media_and_metadata()
