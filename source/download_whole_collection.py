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
from utils.download_toolbox import PayloadFactory, NFTDownloader
import requests
import utils.file_io as fio
import utils.spider_tool_box as stb
from CONST_ENV import CONST_ENV as ENV
from utils.logging_factory import LoggerFactory
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



def download_a_whole_collection(ranking, target_collection, save_path, process_num = 8) -> bool:

    # 读取一些项目信息，用于构造下载参数

    NFT_name = target_collection["contractMetadata"]["name"]
    NFT_name = remove_special_char(NFT_name)
    total_supply = int(target_collection["contractMetadata"]["totalSupply"])
    candidate_format = target_collection["media"][0].get("format", "unknown")
    contractAddress = target_collection["contract_address"][0]

    # 创建存放媒体文件和JSON数据的文件夹
    fio.check_dir(os.path.join(save_path, f"{NFT_name}/img"))
    fio.check_dir(os.path.join(save_path, f"{NFT_name}/metadata"))

    # 获取NFT项目的起始toenId
    start = stb.get_start_file_index(contractAddress)
    if start == None:
        # 如果请求失败，则使用默认的start
        start = 0
    interval_length = 80

    payloadfactory = PayloadFactory(start = start, interval_length = interval_length, total_supply = total_supply, candidate_format = candidate_format)
    # 构造payload body
    payload_list = payloadfactory.create_interval_tuples_with_start_len()

    NFT_downloader = NFTDownloader(ranking = ranking, NFT_name = NFT_name, payload_list = payload_list, contractAddress = contractAddress, candidate_format = candidate_format, save_path = save_path, process_num = process_num)

    print(f"\n**********  ##Ranking:{ranking}-{NFT_name}## starts Download...  **********\n")
    flag = NFT_downloader.download_media_and_metadata()
    return flag



if __name__ == "__main__":

    flag = download_a_whole_collection(ranking = str(ranking), target_collection=target_collection, save_path=save_path, process_num = process_num)

    # 如果顺利下载完成 的信息写进记录文件
    if flag:
        download_record["have_download_phase_3"].update({str(ranking): NFT_name})
        fio.save_json(ENV.DOWNLOAD_LOGGING_PATH, "_download_record", download_record)