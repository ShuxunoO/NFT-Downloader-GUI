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


import requests
import utils.file_io as fio
import utils.spider_toolbox as stb
from internetdownloadmanager import Downloader
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from source.CONST_ENV import CONST_ENV as ENV


# 定义一个NFT下载器类的通用接口类，使用不同平台的下载器类继承这个接口类
class NFT_Downloader(ABC):

    def __init__(self,  
                chain_type: str,
                NFT_name: str,
                contract_address: str,
                candidate_format: str,
                save_path: str,
                process_num: int,
                thread_num: int,
                total_supply = 0):

        self.chain_type = chain_type
        self.NFT_name = NFT_name
        self.contract_address = contract_address
        self.candidate_format = candidate_format
        self.save_path = Path(save_path)
        self.process_num = process_num
        self.thread_num = thread_num
        self.total_supply = total_supply


    # 生成payload的抽象方法，生成不同平台的payload
    @abstractmethod
    def generate_payload(self, *args, **kwargs):

        pass

    # 定义单个下载进程的抽象方法
    @abstractmethod
    def single_process_worker(self,  *args, **kwargs) -> None:
        pass

    # 定义解析响应的抽象方法
    @abstractmethod
    def parse_response(self, response) -> dict:
        pass

    # 定义下载media资源的抽象方法，因为不同平台的media资源下载方式不同
    # 并且都是以链接的形式给到
    @abstractmethod
    def media_downloader(self,  *args, **kwargs) -> None:
        pass
    
    # 定义媒体下载器的单个工作线程的方法,不强制要求实现
    def media_downloader_worker(self, *args, **kwargs) -> None:
        pass

    # 定义使用资源链接的形式下载metadata的方法
    def metadata_downloader(self, *args, **kwargs) -> None:
        pass

    #使用请求中返回的metadata数据批量保存metadata
    def save_metadata_batch(self, metadata):
        pass
    
    #定义下载metadata的单个工作线程的方法，不强制要求实现
    def metadata_downloader_worker(self, *args, **kwargs) -> None:
        pass


# 定义下载整个NFT项目的下载器类，继承NFT_Downloader接口类
class NFT_Downloader_for_Whole_Collection(NFT_Downloader):

    def __init__(self,
                chain_type: str,
                NFT_name: str,
                contract_address: str,
                candidate_format: str,
                save_path: str,
                process_num = 8,
                thread_num = 10,
                total_supply = 0,
                start_index = 0):

        super().__init__(chain_type, NFT_name, contract_address, candidate_format, save_path, process_num, thread_num, total_supply)
        self.start_index = start_index
        self.payload_list = None

    def download_media_and_metadata(self):
        # 启用进程池多进程下载
        try:
            with mp.Pool(processes = self.process_num) as pool:
                pool.map(self.single_process_worker, self.payload_list)
            pool.close()
            pool.join()
        except Exception as e:
            print(f"\nError downloading Ranking: {self.NFT_name} Process startup failed: {e}\n")
            return False

        print(f"\n**********  ##Ranking:{self.NFT_name}## Download finished! **********\n")
        return True

    @abstractmethod
    def generate_payload(self, *args, **kwargs):
        pass


# 基于Alchemy V3 API的NFT下载器类
class NFT_Downloader_for_Whole_Collection_Alchemy(NFT_Downloader_for_Whole_Collection):
    """
    基于Alchemy V3 API的NFT下载器类，完整下载一整个NFT项目
    细节参考链接：https://docs.alchemy.com/reference/getnftsforcontract-v3

    """

    def __init__(self,
                chain_type: str,
                NFT_name: str,
                contract_address: str,
                candidate_format: str,
                save_path: str,
                process_num = 8,
                thread_num = 10,
                total_supply = 0,
                start_index = 0):

        super().__init__(chain_type, NFT_name, contract_address, candidate_format, save_path, process_num, thread_num, total_supply, start_index)
        # 生成下载资源payload list
        self.payload_list = self.generate_payload(candidate_format = candidate_format,
                                                    start_index = start_index,
                                                    total_supply = total_supply)

    def generate_payload(self, *args, **kwargs):
        """
        生成下载资源payload list

        Args:
            *args: 可变参数
            **kwargs: 关键字参数

        """

        # 从参数中解析实例化PayloadFactory所需参数candidate_format，start_index，total_supply
        candidate_format = kwargs.get("candidate_format", self.candidate_format)
        start_index = kwargs.get("start_index", 0)
        total_supply = kwargs.get("total_supply", 0)

        # 实例化PayloadFactory
        payloadfactory = PayloadFactory(candidate_format = candidate_format, start = start_index, interval_length = 80, total_supply = total_supply)

        self.payload_list = payloadfactory.create_interval_tuples_with_start_len()

    # 定义单个下载进程的方法
    def single_process_worker(self, payload):
        # 1. 获取请求参数
        start, interval_length = payload

        time.sleep(random.randint(1, 3))  # 增加请求间隔
        try:
            # 发送请求
            # 随机选择一个api
            api = stb.get_random_api("Alchemy")

            url = f"https://eth-mainnet.g.alchemy.com/nft/v3/{api}/getNFTsForContract?contractAddress={self.contract_address}&withMetadata=true&startToken={start}&limit={interval_length}"
            headers = stb.get_headers()
            response = requests.get(url, headers=headers)
        except Exception as e:
            print(f" {self.NFT_name} Error encountered: {e}")
        else:
            # 4. 解析数据
            if response.status_code == 200:
                response_data = self.parse_response(response)
                # 启动多进程同时进行两个任务
                metadata_source = response_data["metadata_source"]
                media_source = response_data["media_source"]
                self.save_metadata_batch(metadata=metadata)
                self.media_downloader(img_urls=media_source)

            else:
                print(f"{self.NFT_name} Error: {response.status_code}")

    def parse_response(self, response):
        """
        从响应中解析数据。

        Args:
            response (Http response): HTTP响应数据

        Returns:
            dict: 返回解析后的数据，包括metadata资源和media资源
        """
        metadata_dict = {}
        metadata_source = {}
        media_source = {}

        NFT_list = response.json()["nfts"]
        for NFT_item in NFT_list:
            try:
                tokenId = NFT_item.get("tokenId")

                # 解析metadata资源
                """
                {
                    "tokenId": {
                        "raw": metadata,
                        "tokenUri": tokenUri
                    },
                    ……
                }
                
                
                """
                metadata_source[tokenId] = {
                    "raw" : NFT_item["raw"].get("metadata", None),
                    "tokenUri" : NFT_item.get("tokenUri", None)
                    }

                # 解析media资源
                if NFT_item.get("image", None):
                    image = NFT_item.get("image")
                else:
                    # 如果没有image字段，跳过这个NFT
                    continue

                # 将媒体资源统一成一种通用的表达方式
                """
                {
                    "tokenId": {
                        "source_list": [url1, url2, url3, ...],
                        "format": ".png"
                },
                ……

                }
                

                """
                source_list = []
                for source_item in ["cachedUrl", "pngUrl", "originalUrl", "thumbnailUrl"]:
                    # 如果字段不为空，添加到source_list中
                    link = image.get(source_item, None)
                    if link:
                        source_list.append(link)
                
                # 解析文件格式
                temp_format = image.get("contentType", None)
                if temp_format == None:
                    format = self.candidate_format
                elif temp_format == "svg+xml":
                    format = ".svg"
                else:
                    format = f".{temp_format.split('/')[-1]}"

                media_source[tokenId] = {"source_list": source_list,
                                        "format": format}

            except Exception as e:
                # 抛出异常，跳过这个NFT
                print(f"Response parsing exception: {e}. Skipping")
                continue

        metadata_dict["metadata_source"] = metadata_source
        metadata_dict["media_source"] = media_source
        return metadata_dict

    
    def media_downloader(self, media_source) -> None:
        # 启用多线程下载图片
        with ThreadPoolExecutor(max_workers = self.thread_num) as executor:
            executor.map(self.media_downloader_worker, media_source.items())
            # 等待所有线程完成
            executor.shutdown(wait=True)

    def media_downloader_worker(self, source_item) -> None:
        """
        启用idm下载图片

        Args:
            url_item (dict): 图片的资源字典, key 为 tokenId, value 为 url资源字典
        """

        key, value = source_item
        base_path = self.save_path.joinpath(f"{self.NFT_name}/img")

        # 遍历source_list中的所有链接，下载成功即退出
        for source_url in value["source_list"]:
            
            # 尝试拿到文件格式
            file_format = stb.get_file_format(source_url)
            if file_format == None:
                file_format = value["format"] 
            
            file_path = base_path.joinpath(f"{key}{file_format}")
            downloader = Downloader()
            try:
                downloader.download(url=source_url, path=file_path)
                print(f"{self.NFT_name} Media {file_path.name} downloaded successfully.")
                return  # 如果成功，则退出方法
            except Exception as e:
                print(f"Error downloading image {key} from {source_url}: {e}")

    def metadata_downloader(self, metadata_source) -> None:
        # 启用多线程下载图片
        with ThreadPoolExecutor(max_workers = self.thread_num) as executor:
            executor.map(self.metadata_downloader_worker, metadata_source.items())
            # 等待所有线程完成
            executor.shutdown(wait=True)

    def metadata_downloader_worker(self, source_item) -> None:
        """下载metadata文件

        Args:
            source_item (dict): metadata资源字典, key 为 tokenId, value 为 json文件和 url资源字典

        Returns:
            None:
        """
        key, value = source_item
        base_path = self.save_path.joinpath(f"{self.NFT_name}/metadata")
        file_path = base_path.joinpath(f"{key}.json")

        # 如果raw字段里存在metadata，直接保存
        if value["raw"].get("metadata", None):
            fio.save_json(file_path, value["raw"]["metadata"])
            print(f"{self.NFT_name} Metadata {file_path.name} saved successfully.")

        # 如果tokenUri字段不为空，下载tokenUri指向的json文件
        if value["tokenUri"]:
            # 使用idm下载
            downloader = Downloader()
            try:
                downloader.download(url = value["tokenUri"], path = file_path)
                print(f"{self.NFT_name} Metadata {file_path.name} downloaded successfully.")
            except Exception as e:
                print(f"Error downloading metadata {file_path.name} from {value['tokenUri']}: {e}")

class NFTDownloader:
    """
        完整下载一整个NFT项目
    """
    def __init__(self, ranking: str, NFT_name: str, payload_list: list, contractAddress: str, candidate_format: str, save_path: str, process_num = 8):
        self.ranking = ranking
        self.NFT_name = NFT_name
        self.payload_list = payload_list
        self.contractAddress = contractAddress
        self.candidate_format = candidate_format
        self.save_path = save_path
        self.process_num = process_num

    def download_media_and_metadata(self):
        # 启用进程池多进程下载
        try:
            with mp.Pool(processes = self.process_num) as pool:
                pool.map(self.single_process_worker, self.payload_list)
            pool.close()
            pool.join()
        except Exception as e:
            print(f"\nError downloading Ranking:{self.ranking}-{self.NFT_name}进程开启失败！: {e}\n")
            return False

        print(f"\n**********  ##Ranking:{self.ranking}-{self.NFT_name}## Download finished! **********\n")
        return True
    
    def download_metadata_only(self):
        # 启用进程池多进程下载
        try:
            with mp.Pool(processes = self.process_num) as pool:
                pool.map(self.download_metadata_single_worker, self.payload_list)
            pool.close()
            pool.join()
        except Exception as e:
            print(f"\nError downloading Ranking:{self.ranking}-{self.NFT_name}进程开启失败！: {e}\n")
            return False

        print(f"\n**********  ##Ranking:{self.ranking}-{self.NFT_name}## Download finished! **********\n")
        return True

    def single_process_worker(self, payload):
        # 1. 获取请求参数
        start, interval_length = payload

        time.sleep(random.randint(1, 3))  # 增加请求间隔
        try:
            # 发送请求
            # 随机选择一个api
            api = stb.get_random_api()
            url = f"https://eth-mainnet.g.alchemy.com/nft/v3/{api}/getNFTsForContract?contractAddress={self.contractAddress}&withMetadata=true&startToken={start}&limit={interval_length}"
            headers = stb.get_headers()
            response = requests.get(url, headers=headers)
        except Exception as e:
            print(f" {self.NFT_name} Error encountered: {e}")
        else:
            # 4. 解析数据
            if response.status_code == 200:
                response_data = self.parse_response(response)
                # 启动多进程同时进行两个任务
                metadata = response_data["metadata"]
                img_urls = response_data["img_url"]
                self.save_metadata_batch(metadata=metadata)
                self.download_medias(img_urls=img_urls)

            else:
                print(f"{self.NFT_name} Error: {response.status_code}")
    
    def parse_response(self, response):
        """
        从响应中解析数据。

        Args:
            response (_type_): _description_

        Returns:
            _type_: _description_
        """
        metadata_dict = {}
        NFT_list = response.json()["nfts"]
        metadata = {}
        img_url = {}
        for NFT_item in NFT_list:
            try:
                    tokenId = NFT_item.get("tokenId")
                    metadata[tokenId] = NFT_item["raw"].get("metadata", {})
                    image = NFT_item.get("image", None)
                    temp_format = image.get("contentType", None)
                    if temp_format == None:
                        format = self.candidate_format
                    else:
                        format = temp_format.split("/")[-1]
                    img_url[tokenId] = {
                                "format" : format,
                                "pngUrl" : image.get("pngUrl", None),
                                "cachedUrl" : image.get("cachedUrl", None),
                                "originalUrl" : image.get("originalUrl", None),
                                "thumbnailUrl" : image.get("thumbnailUrl", None)
                                }
            except Exception as e:
                # 抛出异常，跳过这个NFT
                print(f"Error: {e}")
                continue

        metadata_dict["metadata"] = metadata
        metadata_dict["img_url"] = img_url

        return metadata_dict

    def save_metadata_batch(self, metadata):
        """
        保存元数据。

        Args:
            metadata (dict): 元数据字典
        """

        for key, value in metadata.items():
            try:
                file_path = os.path.join(self.save_path, f"{self.NFT_name}/metadata")
                fio.save_json(file_path, f"{key}", value)
                print(f"{self.NFT_name} Metadata{key} saved successfully.")
            except Exception as e:
                print(f"Error saving metadata {key}: {e}")

    def download_medias(self, img_urls) -> None:

        # 启用多线程下载图片

        with ThreadPoolExecutor(max_workers = 10) as executor:
            executor.map(self.media_downloader, img_urls.items())

    def media_downloader(self, url_item) -> None:
        """
        启用idm下载图片

        Args:
            url_item (dict): 图片的资源字典, key 为 tokenId, value 为 url资源字典
        """

        key, value = url_item
        base_path = os.path.join(self.save_path, f"{self.NFT_name}/img")

        # 先检查文件夹是否存在，不存在则创建
        fio.check_dir(base_path)
        # 对于svg格式的图片，特殊处理一下
        if value["format"] == "svg+xml":
            file_path =os.path.join(base_path, f"{key}.{'svg'}")
        downloader = Downloader()
        
        urls_to_try = [
        ("pngUrl", "png"),
        ("cachedUrl", value['format']),
        ("originalUrl", value['format']),
        ("thumbnailUrl", "png") ]

        for url_key, file_format in urls_to_try:
            source_url = value.get(url_key)
            if source_url:  # 确保URL不为空
                file_path = os.path.join(base_path, f"{key}.{file_format}")
                try:
                    downloader.download(url=source_url, path=file_path)
                    print(f"{self.NFT_name} Media {key} downloaded successfully.")
                    return  # 如果成功，则退出方法
                except Exception as e:
                    print(f"Error downloading image {key} from {source_url}: {e}")

        print(f"Failed to download image {key} after trying all URLs.")

    # 只下载和保存metadata
    def download_metadata_single_worker(self, payload) -> None:
        # 1. 获取请求参数
        start, interval_length = payload

        time.sleep(random.randint(1, 3))  # 增加请求间隔
        try:
            # 发送请求
            # 随机选择一个api
            api = stb.get_random_api()
            url = f"https://eth-mainnet.g.alchemy.com/nft/v3/{api}/getNFTsForContract?contractAddress={self.contractAddress}&withMetadata=true&startToken={start}&limit={interval_length}"
            headers = stb.get_headers()
            response = requests.get(url, headers=headers)
        except Exception as e:
            print(f" {self.NFT_name} Error encountered: {e}")
        else:
            # 4. 解析数据
            if response.status_code == 200:
                response_data = self.parse_response(response)
                # 启动多进程同时进行两个任务
                metadata = response_data["metadata"]
                self.save_metadata_batch(metadata=metadata)


# 用于生成payload的工厂类，可以根据需要生成不同的NFT资源payload
class PayloadFactory:
    def __init__(self,
                candidate_format: str,
                start=0,
                interval_length=80,
                total_supply=0):

        self.start = start
        self.interval_length = interval_length
        self.total_supply = total_supply
        self.candidate_format = candidate_format

    def create_interval_tuples_with_start_end(self) -> list:
        """
        使用给定的间隔和结束值创建一个区间元组列表。

        :return: 一个区间元组列表。
        """
        result = []
        start = self.start
        while start < self.totalSupply:
            result.append((start, min(start + self.interval_length, self.totalSupply)))
            start += self.interval_length
        return result

    def create_interval_tuples_with_start_len(self) -> list:
        """
        使用给定的间隔和结束值创建一个区间元组列表, 列表中的元素形式为（区间开始，区间间隔）。

        :return: 一个区间元组列表。
        """
        result = []
        start = self.start
        while start < self.total_supply:
            if start + self.interval_length < self.total_supply:
                result.append((start, self.interval_length))
            else:
                result.append((start, self.total_supply - start + 1))
            start += self.interval_length
        return result
    

    def create_tasks_for_missing_nft(self, missing_list: list[int]) -> list[list[int]]:
        """
        使用给定的间隔和结束值将 missing_list 划分为子列表。

        Args:
        :param interval_length: 区间值，整数。
        :param missing_list: 结束值，整数。

        :return: 一个区间元组列表。
        """
        return [missing_list[i:i+self.interval_length] for i in range(0, len(missing_list), self.interval_length)]
    

# 检查路径是否存在，不存在就创建一个文件夹
def check_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def downlaod_metadata_batch(cid):
    """下载cid对应的metadata文件夹中的所有文件

    Args:
        cid (IPFS_CID): IPFS CID
    """
    pass

def change_file_extention(dir_path, new_extention: str):
    """修改file_path文件夹中所有文件成指定后缀名

    Args:
        file_path (str): 文件路径
        new_extention (str): 新的后缀名
    """
    # 获取当前文件夹中所有文件的文件名
    file_list = os.listdir(dir_path)
    tqdm_file_list = tqdm(file_list, desc="changing file's extention to {}".format(new_extention), unit="item", ncols=150, total = len(file_list))
    for file_name in tqdm_file_list:
        # 获取文件的路径
        old_file_path = os.path.join(dir_path, file_name)
        new_file_name = file_name.split(".")[0] + new_extention
        new_file_path = os.path.join(dir_path, new_file_name)
        os.rename(old_file_path, new_file_path)


def get_all_file_path(dir_path):
    """获取目录下所有文件的路径

    Args:
        dir_path (str): 目录路径

    Returns:
        list: 所有文件路径的列表
    """
    return [dir_path + "/" + file_name for file_name in os.listdir(dir_path)]


def get_task_range(process_num, data_length):
    """
    获取每个进程的工作范围

    Args:
        process_num (int): 进程数量
        data_length (_type_): 任务列表长度

    Returns:
        list: 返回每个进程的工作范围组成的列表
    """
    # 计算每个进程要处理的数据量
    data_per_process = data_length // process_num
    # 计算每个进程要处理的数据范围
    range_list = []
    for i in range(process_num):
        if i != process_num - 1:
            # NFT 排行默认从1开始，所以这里要+1
            range_list.append((i*data_per_process+1, (i+1)*data_per_process))
        else:
            range_list.append((i*data_per_process, data_length))
    return range_list


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


def download_NFT_collection_from_IPFS(metadata_path, img_path, delimiter="/"):
    """
    下载整个 collection 中的所有图片
    
    Args: 
        metadata_path (str): metadata文件夹路径
        img_path (str): 图片文件夹路径
        delimiter (str, optional): 分隔符. Defaults to "/".
    
    Returns:
        None:

    """
    with ipfshttpclient.connect() as client:
        file_list = os.listdir(metadata_path)
        for file in tqdm(file_list, desc="Downloading images", unit="file", ncols=150, leave=False):
            file_path = os.path.join(metadata_path, file)
            metadata = fio.load_json(file_path)
            image_cid = metadata["image"].split(delimiter)[-1]
            image = client.cat(image_cid)
            img_name = file.split(".")[0] + ".png"
            with open(os.path.join(img_path, img_name), "wb") as f:
                f.write(image)


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



# https://ipfs.io/ipfs/bafybeib6rkqikdf7czbrtzjphk5k6cdi44smd5ewwc3ysihwr3g2onpwl4/3.png



def parse_response(response, candidate_format):
    metadata_dict = {}
    data = json.loads(response.text)
    metadata = {}
    img_url = {}
    for data_item in data:
        tokenId = str(data_item["id"]["tokenId"])
        metadata[tokenId] = data_item["metadata"]
        img_url[tokenId] = {
                            # "NFT_name" : data_item["contractMetadata"]["name"],
                            "format" : data_item["media"][0].get("format", candidate_format),
                            "url" : data_item["media"][0]["gateway"]
                            }
    metadata_dict["NFT_name"] = data[0]["contractMetadata"]["name"]
    metadata_dict["metadata"] = metadata
    metadata_dict["img_url"] = img_url

    return metadata_dict


def parse_response_V3(response, candidate_format) -> dict:
    """
    解析getNFTMetadataBatch_V3版本返回的response，返回metadata和img_url

    Args:
        response (json): getNFTMetadataBatch_V3返回的response
        candidate_format (str): 候选的数据格式

    Returns:
        dict: metadata和img_url组成的dict数据
    """
    metadata_dict = {}
    data = json.loads(response.text).get("nfts")
    metadata = {}
    img_url = {}
    for data_item in data:
        tokenId = str(data_item["tokenId"])
        metadata[tokenId] = data_item["raw"]["metadata"]
        format = data_item["image"].get("contentType")
        if format != None:
            format = format.split("/")[-1]
        else:
            format = candidate_format
        img_url[tokenId] = {
                            # "NFT_name" : data_item["contractMetadata"]["name"],
                            "format" : format,
                            "pngUrl" : data_item["image"].get("pngUrl", None),
                            "originalUrl" : data_item["image"].get("originalUrl", None)
                            }
    metadata_dict["metadata"] = metadata
    metadata_dict["img_url"] = img_url
    return metadata_dict


def parse_response_V4_byNFTScan(response, candidate_format) -> dict:
    """
    解析getNFTMetadataBatch_V3版本返回的response，返回metadata和img_url

    Args:
        response (json): getNFTMetadataBatch_V3返回的response
        candidate_format (str): 候选的数据格式

    Returns:
        dict: metadata和img_url组成的dict数据
    """
    metadata_dict = {}
    data = json.loads(response.text).get("data")
    metadata = {}
    img_url = {}
    for data_item in data:
        tokenId = str(data_item["token_id"])
        metadata[tokenId] = json.loads(data_item.get("metadata_json"))
        format = data_item.get("content_type")
        if format != None:
            format = format.split("/")[-1]
        else:
            format = candidate_format

        content_uri = data_item.get("content_uri")
        # 如果以Qm开头，说明是ipfs的cid，需要转换成ipfs的url
        if content_uri.startswith("Qm"):
            content_uri = f"https://ipfs.io/{content_uri}"

        image_uri = data_item.get("image_uri")
        if image_uri.startswith("Qm"):
            image_uri = f"https://ipfs.io/{image_uri}"

        nftscan_uri = data_item.get("nftscan_uri")
        img_url[tokenId] = {
                            # "NFT_name" : data_item["contractMetadata"]["name"],
                            "format" : format,
                            "content_uri" : content_uri,
                            "image_uri" : image_uri,
                            "nftscan_uri" : nftscan_uri
                            }
    metadata_dict["metadata"] = metadata
    metadata_dict["img_url"] = img_url
    return metadata_dict

def save_metadata_batch(NFT_name, save_path, metadata):

    for key, value in metadata.items():
        try:
            file_path = os.path.join(save_path, f"{NFT_name}/metadata")
            # 先检查文件夹是否存在，不存在则创建
            fio.check_dir(file_path)
            fio.save_json(file_path, f"{key}", value)
        except Exception as e:
            print(f"Error saving metadata {key}: {e}")

def get_download_img(NFT_name, img_urls, save_path):

    # 启用多线程下载图片
    url_items = img_urls.items()
    with ThreadPoolExecutor(max_workers = 10) as executor:
        # 使用 functools.partial 应用额外的参数
        partial_worker = functools.partial(single_thread_worker, NFT_name = NFT_name, save_path = save_path)
        executor.map(partial_worker, url_items)

        # 等待所有线程完成
        executor.shutdown(wait=True)

def get_download_img_V3(NFT_name, img_urls, save_path):

    # 启用多线程下载图片
    url_items = img_urls.items()
    with ThreadPoolExecutor(max_workers = 10) as executor:
        # 使用 functools.partial 应用额外的参数
        partial_worker = functools.partial(single_idm_worker, NFT_name = NFT_name, save_path = save_path)
        executor.map(partial_worker, url_items)

        # 等待所有线程完成
        executor.shutdown(wait=True)

def get_download_img_V4_byNFTScan(NFT_name, img_urls, save_path):

    # 启用多线程下载图片
    url_items = img_urls.items()
    with ThreadPoolExecutor(max_workers = 10) as executor:
        # 使用 functools.partial 应用额外的参数
        partial_worker = functools.partial(single_idm_worker_V4_byNFTScan, NFT_name = NFT_name, save_path = save_path)
        executor.map(partial_worker, url_items)

        # 等待所有线程完成
        executor.shutdown(wait=True)


def single_thread_worker(url_item, NFT_name, save_path) -> None:
    """
    启用单线程下载图片

    Args:
        url_item (dict): 图片的资源字典, key 为 tokenId, value 为 url资源
        NFT_name (str): NFTcollection名称
        save_path (str): 文件的保存路径
    """

    key, value = url_item
    base_path = os.path.join(save_path, f"{NFT_name}/img")

    # 先检查文件夹是否存在，不存在则创建
    fio.check_dir(base_path)
    # 对于svg格式的图片，特殊处理一下
    if value["format"] == "svg+xml":
        file_path =os.path.join(base_path, f"{key}.{'svg'}")
    else:
        file_path =os.path.join(base_path, f"{key}.{value['format']}")                        
    # 防止被屏蔽，设置随机的请求头
    headers = stb.get_headers()
    try:
        # TODO: 需要增加svg转png的功能
        req = Request(value["url"], headers=headers)

        # 设置随机时延
        time.sleep(random.randint(1, 3))
        with urlopen(req) as response, open(file_path, "wb") as out_file:
            out_file.write(response.read())
        print(f"{NFT_name} Image{key} downloaded successfully.")
    except Exception as e:
        print(f"Error downloading image {key}: {e}")


def single_idm_worker(url_item, NFT_name, save_path) -> None:
    """
    启用idm下载图片

    Args:
        url_item (dict): 图片的资源字典, key 为 tokenId, value 为 url资源
        NFT_name (str): NFTcollection名称
        save_path (str): 文件的保存路径
    """

    key, value = url_item
    base_path = os.path.join(save_path, f"{NFT_name}/img")
    # 先检查文件夹是否存在，不存在则创建
    fio.check_dir(base_path)
    # 对于svg格式的图片，特殊处理一下
    if value["format"] == "svg+xml":
        file_path =os.path.join(base_path, f"{key}.{'svg'}")
    downloader = Downloader()                        
    try:
        # TODO: 需要增加svg转png的功能
        source_url = value.get("pngUrl")
        file_path = os.path.join(base_path, f"{key}.png")
        downloader.download(url = source_url, path= file_path)
        print(f"{NFT_name} Image{key} downloaded successfully.")
    except Exception as e:
        print(f"Error downloading image {key}: {e}, retrying...")
        try:
            print(f"Retrying downloading image {key}...")
            source_url = value.get("originalUrl")
            file_path =os.path.join(base_path, f"{key}.{value['format']}")
            downloader.download(url = source_url, path= file_path)
            print(f"{NFT_name} Image{key} downloaded successfully.")
        except Exception as e:
            print(f"Error downloading image {key}: {e}")

def single_idm_worker_V4_byNFTScan(url_item, NFT_name, save_path) -> None:
    """
    启用idm下载图片

    Args:
        url_item (dict): 图片的资源字典, key 为 tokenId, value 为 url资源
        NFT_name (str): NFTcollection名称
        save_path (str): 文件的保存路径
    """

    key, value = url_item
    base_path = os.path.join(save_path, f"{NFT_name}/img")
    # 先检查文件夹是否存在，不存在则创建
    fio.check_dir(base_path)
    # 对于svg格式的图片，特殊处理一下
    if value["format"] == "svg+xml":
        file_path =os.path.join(base_path, f"{key}.{'svg'}")
    success_flag = False
    downloader = Downloader()
    try:
        # TODO: 需要增加svg转png的功能
        source_url = value.get("content_uri")
        file_path = os.path.join(base_path, f"{key}.png")
        downloader.download(url = source_url, path= file_path)
        print(f"{NFT_name} Image{key} downloaded successfully.")
        success_flag = True
    except Exception as e:
        print(f"Error downloading image {key}: {e}, retrying...")

    if success_flag == False:
        try:
            source_url = value.get("image_uri")
            file_path =os.path.join(base_path, f"{key}.{value['format']}")
            downloader.download(url = source_url, path= file_path)
            print(f"{NFT_name} Image{key} downloaded successfully.")
            success_flag = True
        except Exception as e:
            print(f"Error downloading image {key}: {e}, third trying...")
            
    if success_flag == False:
        try:
            source_url = value.get("nftscan_uri")
            file_path =os.path.join(base_path, f"{key}.{value['format']}")
            downloader.download(url = source_url, path= file_path)
            print(f"{NFT_name} Image{key} downloaded successfully.")
        except Exception as e:
            print(f"Image {key} download failed: {e}")

def single_process_worker(payload, NFT_name, candidate_format, save_path):
    time.sleep(random.randint(1, 3))  # 增加请求间隔
    try:
        # 发送请求
        # 随机选择一个api
        api = stb.get_random_api()
        base_url =  f"https://eth-mainnet.g.alchemy.com/nft/v2/{api}/getNFTMetadataBatch"
        response = requests.post(base_url, json=payload, headers=stb.get_headers())
        # 4. 解析数据
        if response.status_code == 200:
            response_data = parse_response(response, candidate_format)
            metadata = response_data["metadata"]
            save_metadata_batch(NFT_name, save_path, metadata)
            img_urls = response_data["img_url"]
            get_download_img(NFT_name=NFT_name, img_urls=img_urls, save_path=save_path)
        else:
            print(f"{NFT_name} Error: {response.status_code}")
    except Exception as e:
        print(f" {NFT_name} Error encountered: {e}")


def single_process_worker_V3(payload, NFT_name, candidate_format, save_path):
    time.sleep(random.randint(1, 3))  # 增加请求间隔
    try:
        # 发送请求
        # 随机选择一个api
        api = stb.get_random_api()
        base_url =  f"https://eth-mainnet.g.alchemy.com/nft/v3/{api}/getNFTMetadataBatch"
        response = requests.post(base_url, json=payload, headers=stb.get_headers())
        # 4. 解析数据
        if response.status_code == 200:
            response_data = parse_response_V3(response, candidate_format)
            metadata = response_data["metadata"]
            save_metadata_batch(NFT_name, save_path, metadata)
            img_urls = response_data["img_url"]
            get_download_img_V3(NFT_name=NFT_name, img_urls=img_urls, save_path=save_path)
        else:
            print(f"{NFT_name} Error: {response.status_code}")
    except Exception as e:
        print(f" {NFT_name} Error encountered: {e}")



def single_process_worker_V4_byNFTScan(payload, NFT_name, candidate_format, save_path):
    time.sleep(random.randint(1, 3))  # 增加请求间隔
    try:
        # 发送请求
        base_url = "https://restapi.nftscan.com/api/v2/assets/batch"
        headers = {
                    'Content-Type': 'application/json',
                    'X-API-KEY': 'v1XEO1Ftw909EvfoXx6c9rV9',
                }
        response = requests.post(base_url, json=payload, headers=headers)
        # 4. 解析数据
        if response.status_code == 200:
            response_data = parse_response_V4_byNFTScan(response, candidate_format)
            metadata = response_data["metadata"]
            save_metadata_batch(NFT_name, save_path, metadata)
            img_urls = response_data["img_url"]
            get_download_img_V4_byNFTScan(NFT_name=NFT_name, img_urls=img_urls, save_path=save_path)
        else:
            print(f"{NFT_name} Error: {response.status_code}")
    except Exception as e:
        print(f" {NFT_name} Error encountered: {e}")

# 只下载和保存metadata
def download_metadata_only(payload, save_path, candidate_format ="josn") -> None:
    """
    只下载和保存metadata

    Args:
        payload (list): 需要发送请求的payload列表
        save_path (str): 保存路径
        candidate_format (str, optional): Defaults to "josn".
    """
    time.sleep(random.randint(1, 3))  # 增加请求间隔
    try:
        # 发送请求
        # 随机选择一个api
        api = stb.get_random_api()
        base_url =  f"https://eth-mainnet.g.alchemy.com/nft/v2/{api}/getNFTMetadataBatch"
        response = requests.post(base_url, json=payload, headers=stb.get_headers())
        # 4. 解析数据
        if response.status_code == 200:
            response_data = parse_response(response, candidate_format)
            NFT_name = response_data["NFT_name"]
            metadata = response_data["metadata"]
            save_metadata_batch(NFT_name, save_path, metadata)
        else:
            print(f"{NFT_name} Error: {response.status_code}")
    except Exception as e:
        print(f" {NFT_name} Error encountered: {e}")


# 只下载和保存metadata
def download_metadata_only_V3(payload, save_path, candidate_format ="josn") -> None:
    """
    只下载和保存metadata

    Args:
        payload (list): 需要发送请求的payload列表
        save_path (str): 保存路径
        candidate_format (str, optional): Defaults to "josn".
    """
    time.sleep(random.randint(1, 3))  # 增加请求间隔
    try:
        # 发送请求
        # 随机选择一个api
        api = stb.get_random_api()
        base_url =  f"https://eth-mainnet.g.alchemy.com/nft/v3/{api}/getNFTMetadataBatch"
        response = requests.post(base_url, json=payload, headers=stb.get_headers())
        # 4. 解析数据
        if response.status_code == 200:
            response_data = parse_response_V3(response, candidate_format)
            NFT_name = response_data["NFT_name"]
            metadata = response_data["metadata"]
            save_metadata_batch(NFT_name, save_path, metadata)
        else:
            print(f"{NFT_name} Error: {response.status_code}")
    except Exception as e:
        print(f" {NFT_name} Error encountered: {e}")

def download_a_whole_collection(NFT_name, contractAddress, total_supply, candidate_format, save_path):

    # 1. 任务分割
    start = 0
    end = total_supply
    interval_length = 80

    # 2. 构造payload body
    payload_list = stb.payload_factory_a_collection(start = start, totalSupply = end, interval_length = interval_length, contractAddress = contractAddress)
    print("Start downloading...")

    # 启用进程池多进程下载
    try:
        with mp.Pool(processes=5) as pool:
            pool.starmap(single_process_worker, [(payload_list, NFT_name, candidate_format, save_path) for payload_list in payload_list])
        pool.close()
        pool.join()
    except Exception as e:
        print(f"Error downloading {NFT_name}进程开启失败！: {e}")
    print("********** Download finished! **********")


def download_missing_NFTs(target_collection, missing_list, save_path):

    # 2. 构造payload body
    contractAddress = target_collection["contract_address"][0]
    NFT_name = target_collection["contractMetadata"].get("name")
    candidate_format = target_collection["media"][0].get("format", "png")
    payload_list = stb.payload_factory_for_missing_NFT(missing_list = missing_list, interval_length = 50, contractAddress = contractAddress)
    
    print("Start download...")
    # 启用进程池多进程下载
    try:
        with mp.Pool(processes = 8) as pool:
            pool.starmap(single_process_worker_V3, [(payload, NFT_name, candidate_format, save_path) for payload in payload_list])
        pool.close()
        pool.join()
        print("******************** Downloading has finished! ********************")
    except Exception as e:
        print(f"Error downloading {NFT_name}进程开启失败！: {e}")

def download_missing_NFTs_V4_byNFTScan(target_collection, missing_list, save_path):

    # 2. 构造payload body
    contractAddress = target_collection["contract_address"][0]
    NFT_name = target_collection["contractMetadata"].get("name")
    candidate_format = target_collection["media"][0].get("format", "png")
    payload_list = stb.payload_factory_for_missing_NFT_V4_byNFTScan(missing_list = missing_list, interval_length = 50, contractAddress = contractAddress)
    
    print("Start download...")

    # 启用进程池多进程下载
    try:
        with mp.Pool(processes = 8) as pool:
            pool.starmap(single_process_worker_V4_byNFTScan, [(payload, NFT_name, candidate_format, save_path) for payload in payload_list])
        pool.close()
        pool.join()
        print("******************** Downloading has finished! ********************")
    except Exception as e:
        print(f"Error downloading {NFT_name}进程开启失败！: {e}")

def download_missing_metadata(target_collection, missing_list, save_path):

    # 2. 构造payload body
    contractAddress = target_collection["contract_address"]
    NFT_name = target_collection["contractMetadata"].get("name")
    candidate_format = target_collection["media"][0].get("format", "png")
    payload_list = stb.payload_factory_for_missing_NFT(missing_list = missing_list, interval_length = 80, contractAddress = contractAddress)
    print("Start downloading...")

    # 启用进程池多进程下载
    try:
        with mp.Pool(processes=10) as pool:
            pool.starmap(download_metadata_only_V3, [(payload_list, save_path) for payload_list in payload_list])
        pool.close()
        pool.join()
    except Exception as e:
        print(f"Error downloading {NFT_name}进程开启失败！: {e}")
    print("********** Download finished! **********")


