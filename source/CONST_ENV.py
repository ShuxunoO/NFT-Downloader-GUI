from pathlib import Path

# 检查路径是否存在，不存在就创建一个文件夹
def check_dir(dir_path):
    Path(dir_path).mkdir(parents=True, exist_ok=True)

class CONST_ENV():
    BASE_PATH = Path(__file__).resolve().parent.parent
    INFO_PATH = BASE_PATH / "data" / "info"
    DATASET_PATH = BASE_PATH / "DataSet"
    API_KEYS_PATH = BASE_PATH / "data" / "api_keys.json"
    LOGGING_PATH = BASE_PATH / "data" / "log"
    RE_DOWNLOAD_FILES_INFO_PATH = INFO_PATH / "re_download_files_info"
    CHECKING_LOGGING_PATH = LOGGING_PATH / "checking_log"
    DOWNLOAD_LOGGING_PATH = LOGGING_PATH / "download_log"

    check_dir(INFO_PATH)
    check_dir(DATASET_PATH)
    check_dir(LOGGING_PATH)
    check_dir(CHECKING_LOGGING_PATH)
    check_dir(DOWNLOAD_LOGGING_PATH)
    check_dir(RE_DOWNLOAD_FILES_INFO_PATH)
