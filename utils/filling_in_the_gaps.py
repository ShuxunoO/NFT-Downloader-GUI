import functools
import io
import json
import multiprocessing as mp
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from abc import ABC, abstractmethod
from pathlib import Path
import re


import requests
import utils.file_io as fio
import utils.spider_toolbox as stb
from internetdownloadmanager import Downloader
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from source.CONST_ENV import CONST_ENV as ENV



class Add_Unreleased_NFT(object):
    """下载单元类，用于多线程下载
    """
    def __init__(self,thread_num, NFT_name, save_path, base_url, NFT_list, candidate_format):
        self.thread_num = thread_num
        self.NFT_name = NFT_name
        self.save_path = save_path
        self.base_url = base_url
        self.NFT_list = NFT_list
        self.candidate_format = candidate_format

    def payload_generator(self, NFT_list):
        """
        生成payload
        """
        payload_list = []
        if self.base_url.startswith("ipfs://"):
            self.base_url = f"https://ipfs.io/ipfs/{self.base_url.split('//')[-1]}"
        for NFT in NFT_list:
            payload_list.append(self.base_url + str(NFT) + self.candidate_format)
            # payload_list.append(self.base_url + str(NFT))

        return payload_list


    def download(self):
        """
        """
        payload_list = self.payload_generator(self.NFT_list)
        print("Start download...")
        # 启用多线程下载图片
        with ThreadPoolExecutor(max_workers = self.thread_num) as executor:
            # 使用 functools.partial 应用额外的参数
            partial_worker = functools.partial(self.single_worker)
            executor.map(partial_worker, payload_list)
            # 等待所有线程完成
            executor.shutdown(wait=True)

    # https://ipfs.io/ipfs/bafybeib6rkqikdf7czbrtzjphk5k6cdi44smd5ewwc3ysihwr3g2onpwl4/3.png

    def single_worker(self, url) -> None:
        """
        启用idm下载图片

        Args:
            url (dict): 资源链接
            NFT_name (str): NFTcollection名称
            save_path (str): 文件的保存路径
        """

        base_path = os.path.join(self.save_path, f"{self.NFT_name}/img")
        img_name = url.split("/")[-1]
        # 只取名字中的数字
        # img_name = url.split("/")[-1] + self.candidate_format
        file_path = os.path.join(base_path, img_name)
        # 先检查文件夹是否存在，不存在则创建
        fio.check_dir(base_path)

        downloader = Downloader()              
        try:

            downloader.download(url = url, path= file_path)
            print(f"{self.NFT_name} Image{img_name} downloaded successfully.")
        except Exception as e:
            print(f"Error downloading image {img_name}: {e}, retrying...")

class Add_Unreleased_NFT_metadata(Add_Unreleased_NFT):
    """下载单元类，用于多线程下载
    """
    def __init__(self,thread_num, NFT_name, save_path, base_url, NFT_list, candidate_format):
        super().__init__(thread_num, NFT_name, save_path, base_url, NFT_list, candidate_format)

    def payload_generator(self, NFT_list):
        """
        生成payload
        """
        payload_list = []
        if self.base_url.startswith("ipfs://"):
            self.base_url = f"https://ipfs.io/ipfs/{self.base_url.split('//')[-1]}"
        for NFT in NFT_list:
            # payload_list.append(self.base_url + str(NFT))
            payload_list.append(self.base_url + str(NFT) + self.candidate_format)
            # payload_list.append(self.base_url + f"{str(NFT)}.dogsunchainednft.com")
        return payload_list
    
    def single_worker(self, url) -> None:
        """
        启用request下载图片

        Args:
            url (dict): 资源链接
            NFT_name (str): NFTcollection名称
            save_path (str): 文件的保存路径
        """

        base_path = os.path.join(self.save_path, f"{self.NFT_name}/metadata")
        json_name = url.split("/")[-1]

        file_path = os.path.join(base_path, json_name)
        # file_path = os.path.join(base_path, json_name + self.candidate_format)
        # 先检查文件夹是否存在，不存在则创建
        fio.check_dir(base_path)
        # 发送HTTP GET请求到指定的URL
        response = requests.get(url)

        # 检查请求是否成功
        if response.status_code == 200:
            # 如果成功，将响应内容写入文件
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"Download {json_name}{self.candidate_format} successfully.")
        else:
            print(f"Failed to download. Status code: {response.status_code}")



# 针对缺少的NFT下载器类
def create_tasks_for_missing_nft(missing_list: list[int], interval_length: int = 50) -> list[list[int]]:
    """
    使用给定的间隔和结束值将 missing_list 划分为子列表。

    Args:
    :param interval_length: 区间值，整数。
    :param missing_list: 结束值，整数。

    :return: 一个区间元组列表。
    """
    return [missing_list[i:i+interval_length] for i in range(0, len(missing_list), interval_length)]


def generate_payload_for_missing_NFT(missing_list, contractAddress) -> dict:
    """
    生成负载，用于下载 missing_list 中的NFT
    Args:
        download_range (list): 要下载的个别NFT的列表
        contractAddress (str): 要下载的合约地址

        Returns:
            dict: 负载
    """
    tokens = []
    for index in missing_list:
        tokens.append({
            "contractAddress": contractAddress,
            "tokenId": str(index)
        })
    payload = {
        "tokens": tokens,
        "refreshCache": True
    }
    return payload

def generate_payload_for_missing_NFT_by_V4_byNFTScan(missing_list, contractAddress) -> dict:
    """
    生成负载，用于下载 missing_list 中的NFT
    Args:
        download_range (list): 要下载的个别NFT的列表
        contractAddress (str): 要下载的合约地址

        Returns:
            dict: 负载
    """
    tokens = []
    for index in missing_list:
        tokens.append({
            'contract_address': contractAddress,
            'token_id': str(index)
        })
    payload = {
        'show_attribute': 'true',
        'contract_address_with_token_id_list': tokens
    }
    return payload

def payload_factory_for_missing_NFT(missing_list, contractAddress, interval_length=80) -> list:
    """负载生成器，用于missing_list 中的NFT

    Args:
        missing_list (list): 要下载的NFT组成的编号列表
        contractAddress (_type_): 要下载NFT的合约地址

    Returns:
        list: 负载列表
    """

    task_list = create_tasks_for_missing_nft(missing_list, interval_length)
    payload_list = []
    for task in task_list:
        payload_body = generate_payload_for_missing_NFT(task, contractAddress)
        payload_list.append(payload_body)
    return payload_list

def payload_factory_for_missing_NFT_V4_byNFTScan(missing_list, contractAddress, interval_length=80) -> list:
    """负载生成器，用于missing_list 中的NFT

    Args:
        missing_list (list): 要下载的NFT组成的编号列表
        contractAddress (_type_): 要下载NFT的合约地址

    Returns:
        list: 负载列表
    """

    task_list = create_tasks_for_missing_nft(missing_list, interval_length)
    payload_list = []
    for task in task_list:
        payload_body = generate_payload_for_missing_NFT_by_V4_byNFTScan(task, contractAddress)
        payload_list.append(payload_body)
    return payload_list


def add_missing_NFT_from_IPFS(task_range, metadata_path, img_path, delimiter="/"):
    """
    为缺失的NFT添加图片
    
    Args:   
        task_range (tuple): 任务范围
        metadata_path (str): metadata文件夹路径
        img_path (str): 图片文件夹路径
        delimiter (str, optional): 分隔符. Defaults to "/".
    
    Returns:
        None:

    """
    with ipfshttpclient.connect() as client:
        begin, end = task_range
        for index in tqdm(range(begin, end+1), desc="Downloading images", unit="file", ncols=150, leave=False):
            json_name = str(index) + ".json"
            file_path = os.path.join(metadata_path, json_name)
            metadata = fio.load_json(file_path)
            image_cid = metadata["image"].split(delimiter)[-1]
            image = client.cat(image_cid)
            img_name = str(index) + ".png"
            with open(os.path.join(img_path, img_name), "wb") as f:
                f.write(image)
