from aria2p import API as ariaAPI, Client as ariaClient
from time import time, sleep
from config.config import Config
from bot_helper.Others.Helper_Functions import get_readable_time
from threading import Lock
from re import findall as re_findall
from threading import Thread
from bot_helper.Others.Names import Names



LOGGER = Config.LOGGER
EDIT_SLEEP_TIME_OUT = 7
TORRENT_TIMEOUT = 600
MAGNET_REGEX = r"magnet:\?xt=urn:btih:[a-zA-Z0-9]*"

aria2_download_list_lock = Lock()
aria2_download_list = []


def getDownloadByGid(gid):
    for dl in aria2_download_list:
            if dl.gid() == gid:
                return dl
    return None


def get_download(gid):
        return Aria2.client.get_download(gid)


def is_magnet(url: str):
    magnet = re_findall(MAGNET_REGEX, url)
    return bool(magnet)


def new_thread(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper


@new_thread
def __onDownloadStarted(api, gid):
    LOGGER.info(f"onDownloadStarted: {gid}")
    found = False
    retry = 0
    download = api.get_download(gid)
    while True:
        if dl := getDownloadByGid(gid):
            dl.onDownloadStarted()
            found = True
            break
        if retry==10:
            break
        retry+=1
        sleep(1)
    if not found:
            LOGGER.info(f"onDownloadStarted: {gid} function not found")
    return


@new_thread
def __onDownloadComplete(api, gid):
    LOGGER.info(f"onDownloadComplete : {gid}")
    if dl := getDownloadByGid(gid):
        dl.onDownloadComplete()
    return

@new_thread
def __onBtDownloadComplete(api, gid):
    LOGGER.info(f"onBtDownloadComplete: {gid}")
    if dl := getDownloadByGid(gid):
        dl.onBtDownloadComplete()
    return

@new_thread
def __onDownloadStopped(api, gid):
    LOGGER.info(f"onDownloadStopped: {gid}")
    try:
        if dl := getDownloadByGid(gid):
            dl.onDownloadStopped('❌Dead torrent!')
    except:
        pass
    return

@new_thread
def __onDownloadError(api, gid):
    LOGGER.info(f"onDownloadError: {gid}")
    error = "None"
    try:
        download = api.get_download(gid)
        error = download.error_message
    except:
        pass
    LOGGER.info(error)
    if dl := getDownloadByGid(gid):
        LOGGER.info("GivingError")
        dl.onDownloadError(error)
    else:
        LOGGER.info("NoGidFound")
    return


def start_listener():
        Aria2.client.listen_to_notifications(threaded=True,
                                    on_download_start=__onDownloadStarted,
                                    on_download_error=__onDownloadError,
                                    on_download_stop=__onDownloadStopped,
                                    on_download_complete=__onDownloadComplete,
                                    on_bt_download_complete=__onBtDownloadComplete,
                                    timeout=60)
        return


class Aria2:
    client = ariaAPI(ariaClient(host="http://localhost", port=6800, secret=""))
    aria2_options = {}
    aria2c_global = ['bt-max-open-files', 'download-result', 'keep-unfinished-download-result', 'log', 'log-level',
                 'max-concurrent-downloads', 'max-download-result', 'max-overall-download-limit', 'save-session',
                 'max-overall-upload-limit', 'optimize-concurrent-downloads', 'save-cookies', 'server-stat-of']
    if not aria2_options:
        aria2_options = client.client.get_global_option()
        del aria2_options['dir']
    else:
        a2c_glo = {}
        for op in aria2c_global:
            if op in aria2_options:
                a2c_glo[op] = aria2_options[op]
        client.set_global_options(a2c_glo)
    
    async def add_aria2c_download(link, listener, filename, auth, ratio, seed_time):
            path = listener.dir
            args = {'dir': path, 'max-upload-limit': '1K'}
            a2c_opt = {**Aria2.aria2_options}
            [a2c_opt.pop(k) for k in Aria2.aria2c_global if k in Aria2.aria2_options]
            args.update(a2c_opt)
            if filename:
                args['out'] = filename
            if auth:
                args['header'] = f"authorization: {auth}"
            if ratio:
                args['seed-ratio'] = ratio
            if seed_time:
                args['seed-time'] = seed_time
            if TORRENT_TIMEOUT:
                args['bt-stop-timeout'] = str(TORRENT_TIMEOUT)
            if is_magnet(link):
                LOGGER.info("ARIA2: MAGNET LINK FOUND")
                download = Aria2.client.add_magnet(link, args)
            else:
                LOGGER.info("ARIA2: HTTP LINK FOUND")
                download = Aria2.client.add_uris([link], args)
            if download.error_message:
                error = str(download.error_message).replace('<', ' ').replace('>', ' ')
                LOGGER.info(f"Download Error: {error}")
                listener.update_status_message(f"❌Download Error: {error}")
                LOGGER.info(f"ARIA2 DOWNLOAD ERROR: {error}")
                return False, False
            with aria2_download_list_lock:
                aria2_status = AriaDownloadStatus(download.gid, listener, time())
                aria2_download_list.append(aria2_status)
                LOGGER.info(f"Aria2Download Started: {download.gid}")
                return download, aria2_status
            
    async def cancel_download(gid):
            if dl := getDownloadByGid(gid):
                await dl.cancel_download()
                return


class AriaDownloadStatus:
    def __init__(self, gid, listener, start_time, seeding=False):
        self.__gid = gid
        self.__listener= listener
        self.__download = get_download(gid)
        self.start_time = start_time
        self.seeding = seeding
        self.process_status = 0

    def __update(self):
        self.__download = self.__download.live
        if self.__download is None:
             self.__download = get_download(self.__gid)
        elif self.__download.followed_by_ids:
            self.__gid = self.__download.followed_by_ids[0]
            self.__download = get_download(self.__gid)

    def progress(self):
        return self.__download.progress_string()
    
    def is_complete(self):
        return self.__download.is_complete
    
    def error_message(self):
        return self.__download.error_message
    
    def has_failed(self):
        return self.__download.has_failed

    def size_raw(self):
        return self.__download.total_length

    def processed_bytes(self):
        return self.__download.completed_length

    def speed(self):
        self.__update()
        return self.__download.download_speed_string()

    def name(self):
        if self.__download.name:
                return self.__download.name
        else:
                return False

    def size(self):
        return self.__download.total_length_string()

    def eta(self):
        return self.__download.eta_string()

    def status(self):
        self.__update()
        download = self.__download
        if download.is_waiting:
            return Names.STATUS_WAITING
        elif download.is_paused:
            return Names.STATUS_PAUSED
        elif download.seeder and self.seeding:
            return Names.STATUS_SEEDING
        else:
            return Names.STATUS_DOWNLOADING

    def seeders_num(self):
        return self.__download.num_seeders

    def leechers_num(self):
        return self.__download.connections

    def uploaded_bytes(self):
        return self.__download.upload_length_string()

    def upload_speed(self):
        self.__update()
        return self.__download.upload_speed_string()

    def ratio(self):
        return f"{round(self.__download.upload_length / self.__download.completed_length, 3)}"

    def seeding_time(self):
        return f"{get_readable_time(time() - self.start_time)}"
        
    def listener(self):
        return self.__listener
        
    def download(self):
        return self

    def gid(self):
        try:
            self.__update()
        except:
            pass
        return self.__gid

    def type(self):
        return Names.aria
    
    def onDownloadStarted(self):
        self.listener().update_status_message(Names.STATUS_DOWNLOADING)
        self.listener().append_dw_files(self.name())
        return
    
    def onDownloadComplete(self):
        self.listener().update_status_message("✅Download Has Completed")
        self.process_status = 1
        return
    
    def onBtDownloadComplete(self):
        self.listener().update_status_message("🟡Download Has Completed")
        self.process_status = 1
        return
    
    def onDownloadStopped(self, msg):
        sleep(5)
        if self.process_status!=-2:
            self.listener().update_status_message(msg)
            self.process_status = -1
        return
    
    def onDownloadError(self, error):
        self.listener().update_status_message(f"❌Download Error: {error}")
        self.process_status = -1
        return

    async def cancel_download(self):
        self.__update()
        if self.__download.seeder and self.seeding:
            LOGGER.info(f"Cancelling Seed: {self.name()}")
            LOGGER.info(f"Seeding stopped with Ratio: {self.ratio()} and Time: {self.seeding_time()}")
            self.listener().update_status_message(f"Cancelling Seed: {self.name()}")
            self.process_status = -2
            Aria2.client.remove([self.__download], force=True, files=True)
        elif downloads := self.__download.followed_by:
            LOGGER.info(f"Cancelling Download: {self.name()}")
            self.listener().update_status_message('🔒Task Cancelled By User')
            self.process_status = -2
            downloads.append(self.__download)
            Aria2.client.remove(downloads, force=True, files=True)
        else:
            LOGGER.info(f"Cancelling Download: {self.name()}")
            self.process_status = -2
            self.listener().update_status_message('🔒Task Cancelled By User') 
            Aria2.client.remove([self.__download], force=True, files=True)

