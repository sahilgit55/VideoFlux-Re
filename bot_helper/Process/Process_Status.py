from asyncio import sleep as asynciosleep
from bot_helper.Others.Helper_Functions import get_human_size, gen_random_string, get_readable_time, get_value, get_account_type
from os import remove
from config.config import Config
from time import time
from bot_helper.Process.Running_Process import check_running_process
from bot_helper.Others.Names import Names
from re import findall as refindall
from math import floor
from asyncio import wait_for, create_subprocess_exec
from asyncio.subprocess import PIPE as asyncioPIPE
from bot_helper.Database.User_Data import get_data
from json import loads
from os.path import getsize, isdir, exists
from shutil import move as shutil_move
from os import makedirs, rename
from aiofiles import open as aio_open


def create_direc(direc):
    if not isdir(direc):
        makedirs(direc)
    return


LOGGER = Config.LOGGER
FINISHED_PROGRESS_STR = Config.FINISHED_PROGRESS_STR
UNFINISHED_PROGRESS_STR = Config.UNFINISHED_PROGRESS_STR
download_dir = Config.DOWNLOAD_DIR
ws_name = {'5:5': 'Top Left', 'main_w-overlay_w-5:5': 'Top Right', '5:main_h-overlay_h': 'Bottom Left', 'main_w-overlay_w-5:main_h-overlay_h-5': 'Bottom Right'}

async def get_ffmpeg_process_line(proc):
        data = False
        try:
                data = await wait_for(proc.stderr.readline(), 5)
        except:
                pass
        return data


async def get_rclone_process_line(proc):
        data = False
        try:
                data = await wait_for(proc.stdout.readline(), 5)
        except Exception as e:
                LOGGER.info(f"❗Error While Getting Rclone Upload Log, Error: {str(e)}")
        return data

###############------Get_Uploaded_File_Link------###############
async def getdrivelink(search_command, event):
    process = await create_subprocess_exec(
        *search_command, stdout=asyncioPIPE
    )
    stdout, _ = await process.communicate()
    try:
        stdout = stdout.decode().strip()
        print(stdout)
        data = loads(stdout)
        file_id = data[0]["ID"]
        # name = data[0]["Name"]
        # link = f'https://drive.google.com/file/d/{file_id}/view'
        # print(link)
        return file_id
    except Exception as e:
        await event.reply(f'❌Error While Getting File ID: {str(e)}')
        LOGGER.info(str(e))
        return False

# async def check_file_drive_link(search_command, event, fileloc, r_config, drive_name, name, caption):
#                                 file_id = await getdrivelink(search_command, event)
#                                 if file_id:
#                                         try:
#                                                 fisize =str(get_human_size(getsize(fileloc)))
#                                         except:
#                                                 fisize = "Unknown"
#                                         account_type = await get_account_type(r_config, drive_name)
#                                         if account_type=="drive":
#                                                 link_text = f"⛓Link: `https://drive.google.com/file/d/{file_id}/view`"
#                                         else:
#                                                 link_text = f"⛓File ID: `{file_id}`"
#                                         file_text = f"✅Successfully Uploaded `{name}` To `{str(drive_name)}`\n\n{link_text}\n\n💽Size: {fisize}\n\n" + str(caption).strip() if caption else f"✅Successfully Uploaded `{name}` To `{str(drive_name)}`\n\n{link_text}\n\n💽Size: {fisize}"
#                                 else:
#                                         file_text = f"✅Successfully Uploaded `{name}` To `{str(drive_name)}`\n\n❗Failed To File ID\n\n" + str(caption).strip() if caption else f"✅Successfully Uploaded `{name}` To `{str(drive_name)}`\n\n❗Failed To File ID"
#                                 await event.reply(str(file_text))
#                                 return



async def check_file_drive_link(search_command, event, fileloc, r_config, drive_name, name, caption):
                                file_link = await rclone_get_link(drive_name, name, r_config)
                                try:
                                                fisize =str(get_human_size(getsize(fileloc)))
                                except:
                                                fisize = "Unknown"
                                if file_link:
                                        link_text = f"⛓Link: `{file_link}`"
                                        file_text = f"✅Successfully Uploaded `{name}` To `{str(drive_name)}`\n\n{link_text}\n\n💽Size: {fisize}\n\n" + str(caption).strip() if caption else f"✅Successfully Uploaded `{name}` To `{str(drive_name)}`\n\n{link_text}\n\n💽Size: {fisize}"
                                else:
                                        file_text = f"✅Successfully Uploaded `{name}` To `{str(drive_name)}`\n\n❗Failed To Get Link\n\n" + str(caption).strip() if caption else f"✅Successfully Uploaded `{name}` To `{str(drive_name)}`\n\n❗Failed To Get Link"
                                await event.reply(str(file_text))
                                return



async def rclone_get_link(remote,name, conf):
        cmd =  ["rclone", "link", f'--config={conf}', f"{remote}:{name}"]
        LOGGER.info(f"Getting Uploaded File {name} Link From {remote}")
        process = await create_subprocess_exec(*cmd, stdout=asyncioPIPE, stderr=asyncioPIPE)
        out, _ = await process.communicate()
        url = out.decode().strip()
        return_code = await process.wait()
        if return_code == 0:
                return url
        else:
                return False
        


def get_progress_bar_from_percentage(percentage):
    try:
        p = percentage.strip().strip("%")
        p = int(float(p))
    except:
        p = 0
    p = min(max(p, 0), 100)
    cFull = p // 8
    p_str = FINISHED_PROGRESS_STR * cFull
    p_str += UNFINISHED_PROGRESS_STR * (12 - cFull)
    return f"[{p_str}]"


def get_progress_bar_string(current,total):
    completed = int(current) / 8
    total = int(total) / 8
    p = 0 if total == 0 else round(completed * 100 / total)
    p = min(max(p, 0), 100)
    cFull = p // 8
    p_str = FINISHED_PROGRESS_STR * cFull
    p_str += UNFINISHED_PROGRESS_STR * (12 - cFull)
    return f"[{p_str}]"


def ffmpeg_status_foot(status, user_id, start_time, time_in_us):
        status_foot = ""
        if get_data()[user_id]['ffmpeg_ptime']:
                status_foot+= f"\n**P.Time**: {get_readable_time(time()-start_time)}"
        if get_data()[user_id]['ffmpeg_size']:
                if status_foot=="":
                        status_foot+= "\n"
                else:
                        status_foot+= " | "
                try:
                        status_foot+= f"**ETA Size**: {str(get_human_size((status.output_size()/time_in_us)*status.duration*1024*1024))}"
                except:
                        status_foot+= f"**ETA Size**: Unknown"
        return status_foot


def generate_ffmpeg_status_head(user_id, pmode, input_size):
        if pmode==Names.compress:
                if get_data()[user_id]['compress']['use_queue_size']:
                        qsize_text = f"**Queue Size**: {str(get_data()[user_id]['compress']['queue_size'])}"
                else:
                        qsize_text = f"**Queue Size**: False"
                text = f"\n**SYNC**: {get_data()[user_id]['compress']['sync']} | **Preset**: {get_data()[user_id]['compress']['preset']}\n"\
                        f"**CRF**: {get_data()[user_id]['compress']['crf']} | **Copy Subtitles**: {get_data()[user_id]['compress']['copy_sub']}\n"\
                        f"{qsize_text} | **MAP**: {get_data()[user_id]['compress']['map']}\n"\
                        f"**Encoder**: {get_data()[user_id]['compress']['encoder']} | **In.Size**: {get_human_size(input_size)}"
                return text
        elif pmode==Names.watermark:
                if get_data()[user_id]['watermark']['use_queue_size']:
                        qsize_text = f"**Queue Size**: {str(get_data()[user_id]['watermark']['queue_size'])}"
                else:
                        qsize_text = f"**Queue Size**: False"
                if get_data()[user_id]['watermark']['encode']:
                        encoder = get_data()[user_id]['watermark']['encoder']
                else:
                        encoder = 'False'
                        
                text = f"\n**SYNC**: {get_data()[user_id]['watermark']['sync']} | **Preset**: {get_data()[user_id]['watermark']['preset']}\n"\
                        f"**CRF**: {get_data()[user_id]['watermark']['crf']} | **Copy Subtitles**: {get_data()[user_id]['watermark']['copy_sub']}\n"\
                        f"{qsize_text} | **MAP**: {get_data()[user_id]['watermark']['map']}\n"\
                        f"**W.Size**: {get_data()[user_id]['watermark']['size']} | **W.Position**: {ws_name[get_data()[user_id]['watermark']['position']]}\n"\
                        f"**Encoder**: {encoder} | **In.Size**: {get_human_size(input_size)}"
                return text
        elif pmode==Names.merge:
                text = f"\n**MAP**: {get_data()[user_id]['merge']['map']} | **Fix Blank**: {get_data()[user_id]['merge']['fix_blank']}"
                return text
        elif pmode==Names.convert:
                if get_data()[user_id]['convert']['use_queue_size']:
                        qsize_text = f"**Queue Size**: {str(get_data()[user_id]['convert']['queue_size'])}"
                else:
                        qsize_text = f"**Queue Size**: False"
                if get_data()[user_id]['convert']['encode']:
                        encoder = get_data()[user_id]['convert']['encoder']
                else:
                        encoder = 'False'
                text = f"\n**SYNC**: {get_data()[user_id]['convert']['sync']} | **Preset**: {get_data()[user_id]['convert']['preset']}\n"\
                        f"**CRF**: {get_data()[user_id]['convert']['crf']} | **Copy Subtitles**: {get_data()[user_id]['convert']['copy_sub']}\n"\
                        f"{qsize_text} | **MAP**: {get_data()[user_id]['convert']['map']}\n"\
                        f"**Encoder**: {encoder} | **In.Size**: {get_human_size(input_size)}"
                return text
        elif pmode==Names.hardmux:
                if get_data()[user_id]['hardmux']['use_queue_size']:
                        qsize_text = f"**Queue Size**: {str(get_data()[user_id]['hardmux']['queue_size'])}"
                else:
                        qsize_text = f"**Queue Size**: False"
                if get_data()[user_id]['hardmux']['encode_video']:
                        encoder = get_data()[user_id]['hardmux']['encoder']
                else:
                        encoder = 'False'
                text = f"\n**SYNC**: {get_data()[user_id]['hardmux']['sync']} | **Preset**: {get_data()[user_id]['hardmux']['preset']}\n"\
                        f"**CRF**: {get_data()[user_id]['hardmux']['crf']} | {qsize_text}\n"\
                        f"**Encoder**: {encoder} | **In.Size**: {get_human_size(input_size)}"
                return text
        elif pmode==Names.softmux:
                text = f"\n**Subtitles Codec**: {get_data()[user_id]['softmux']['sub_codec']} | **In.Size**: {get_human_size(input_size)}"
                return text
        elif pmode==Names.softremux:
                text = f"\n**Subtitles Codec**: {get_data()[user_id]['softremux']['sub_codec']} | **In.Size**: {get_human_size(input_size)}"
                return text
        else:
                return ""




class ProcessStatus:
        def __init__(self, user_id, chat_id, user_name, user_first_name, event, process_type, file_name=False, thumbnail=False, start_time=False, custom_metadata=False, custom_index=False):
                self.user_id = user_id
                self.chat_id = chat_id
                self.amap_options =  '0:a'
                self.user_name = user_name
                self.user_first_name = user_first_name
                self.event = event
                self.dir = f"{download_dir}/{user_id}/{gen_random_string(5)}"
                self.send_files = []
                self.dw_files = []
                self.subtitles = []
                self.dw_index = "-/-"
                self.file_name = file_name
                self.status_message_id = gen_random_string(5)
                self.process_id = gen_random_string(10)
                self.status_message = f"🔁Initializing\n`/cancel process {self.process_id}`"
                self.message = "Not Found"
                self.caption = False
                if not thumbnail and exists(f'./userdata/{str(user_id)}_Thumbnail.jpg'):
                        self.thumbnail = f'./userdata/{str(user_id)}_Thumbnail.jpg'
                else:
                        self.thumbnail = thumbnail
                self.process_type = process_type
                self.start_time = start_time
                self.convert_quality = 480
                self.convert_index = "-/-"
                self.ping = time()
                self.trash_objects = False
                self.multi_tasks = []
                self.multi_task_no = 0
                self.custom_metadata = custom_metadata
                self.custom_index = custom_index
                if self.user_name:
                        self.added_by = f'[{self.user_first_name}](https://t.me/{str(self.user_name)})'
                else:
                        self.added_by = self.user_first_name
                        
        def append_multi_tasks(self, task):
                self.multi_tasks.append(task)
                return
        
        def change_multi_tasks_no(self, no):
                self.multi_task_no = no
                return
        
        def get_multi_task_no(self):
                if self.multi_task_no:
                        return f"({str(self.multi_task_no-len(self.multi_tasks))}/{str(self.multi_task_no)})"
                else:
                        return ""
        
        def replace_multi_tasks(self, multi_tasks):
                self.multi_tasks = multi_tasks
                return
        
        def update_status_message(self, message):
                self.message = message
                return
        
        def update_convert_quality(self, convert_quality):
                self.convert_quality = convert_quality
                return
        
        def update_convert_index(self, convert_index):
                self.convert_index = convert_index
                return
        
        def update_process_message(self, text):
                self.status_message = text
                return
        
        def set_custom_thumbnail(self, thumbnail):
                self.thumbnail = thumbnail
                return
        
        def move_custom_thumbnail(self, thumbnail):
                if not thumbnail:
                        return
                if exists(thumbnail):
                        name = thumbnail.split("/")[-1]
                        move_dir = f"{self.dir}/thumbnail"
                        if exists(f"{move_dir}/{name}"):
                                move_dir = f"{self.dir}/{str(gen_random_string(5))}"
                        create_direc(move_dir)
                        LOGGER.info(f"Moving Thumbnail {thumbnail} To {move_dir}/{name}")
                        shutil_move(thumbnail, f"{move_dir}/{name}")
                        self.thumbnail = f"{move_dir}/{name}"
                else:
                        self.thumbnail = "./thumb.jpg"
                        LOGGER.info(f"{thumbnail} Thumbnail Not Found.")
                return
        
        def update_start_time(self, start_time):
                self.start_time = start_time
                return
        
        def set_send_files(self, name):
                self.send_files = [f"{self.dir}/{name}"]
                return
        
        def replace_send_files(self, file_name):
                self.send_files = [file_name]
                return
        
        def replace_send_list(self, send_files):
                self.send_files = send_files
                return
        
        def append_send_files(self, name):
                if f"{self.dir}/{name}" not in self.send_files:
                        self.send_files.append(f"{self.dir}/{name}")
                return
        
        def append_send_files_loc(self, fileloc):
                if fileloc not in self.send_files:
                        self.send_files.append(fileloc)
                return
        
        def append_dw_files_loc(self, fileloc):
                if fileloc not in self.dw_files:
                        self.dw_files.append(fileloc)
                return
        
        def append_dw_files(self, name):
                if f"{self.dir}/{name}" not in self.dw_files:
                        self.dw_files.append(f"{self.dir}/{name}")
                return
        
        def set_file_name(self, file_name):
                if not self.file_name:
                        self.file_name = file_name
                return
        
        def set_file_name_from_send_list(self):
                if not self.file_name:
                        try:
                                if len(self.send_files):
                                        self.file_name = self.send_files[-1].split("/")[-1]
                                        LOGGER.info(f"File Name : {self.file_name}")
                                else:
                                        LOGGER.info(f"No File In Send Files To Set File Name")
                        except Exception as e:
                                LOGGER.info(f"Error While Setting File Name  {str(e)}")
                else:
                        LOGGER.info(f"File Name Already Set : {str(self.file_name)}")
                return
        
        def set_caption(self, caption):
                self.caption = caption
                return
        
        def set_amap_options(self, options):
                self.amap_options = options
                return
        
        def set_dw_index(self, dw_index):
                self.dw_index = dw_index
                return
        
        def move_dw_file(self, name):
                if exists(f"{self.dir}/{name}"):
                        if f"{self.dir}/{name}" in self.dw_files:
                                self.dw_files.remove(f"{self.dir}/{name}")
                                move_dir = f"{self.dir}/work_files"
                                create_direc(move_dir)
                                if exists(f"{move_dir}/{name}"):
                                        LOGGER.info(f"Renaming File {move_dir}/{name}")
                                        rename(f"{move_dir}/{name}", f"{move_dir}/{str(gen_random_string(5))}_{name}")
                                LOGGER.info(f"Moving File {self.dir}/{name} To {move_dir}/{name}")
                                shutil_move(f"{self.dir}/{name}", f"{move_dir}/{name}")
                                self.send_files.append(f"{move_dir}/{name}")
                        else:
                                LOGGER.info(f"{self.dir}/{name} Not Found In DW List.")
                else:
                        LOGGER.info(f"{self.dir}/{name} File Not Found.")
                return
        
        def move_send_files(self, send_files):
                for file in send_files:
                        if exists(file):
                                name = file.split("/")[-1]
                                move_dir = f"{self.dir}/work_files"
                                if exists(f"{move_dir}/{name}"):
                                        move_dir = f"{self.dir}/{str(gen_random_string(5))}"
                                create_direc(move_dir)
                                LOGGER.info(f"Moving File {file} To {move_dir}/{name}")
                                shutil_move(file, f"{move_dir}/{name}")
                                self.send_files.append(f"{move_dir}/{name}")
                        else:
                                LOGGER.info(f"{file} File Not Found.")
                        return
        
        def append_subtitles(self, sub_loc):
                if exists(sub_loc):
                        if sub_loc not in self.subtitles:
                                self.subtitles.append(sub_loc)
                        else:
                                LOGGER.info(f"{sub_loc} Already In Subtitles.")
                else:
                        LOGGER.info(f"{sub_loc} File Not Found.")
                return
        
        def get_task_details(self):
                return f'**Added By**: {self.added_by} | **ID**: `{self.user_id}`'
        
        async def update_status(self, status):
                if status.type()==Names.ffmpeg:
                        input_size = status.input_size()
                        ffmpeg_head = generate_ffmpeg_status_head(self.user_id, self.process_type, input_size)
                total_files = len(self.send_files)
                error_no = 0
                multi_task_no = self.get_multi_task_no()
                while True:
                        self.ping = time()
                        if status.type()==Names.aria:
                                if status.process_status==0:
                                        text =f'{status.status()} [{self.dw_index}]\n'\
                                                f'`{str(status.name())}`\n'\
                                                f'{get_progress_bar_from_percentage(status.progress())} {status.progress()}\n'\
                                                f'**Added By**: {self.added_by} | **ID**: `{self.user_id}`\n'\
                                                f'**Engine**: Aria\n'\
                                                f'**Downloaded**: {get_human_size(int(status.processed_bytes()))} of {get_human_size(int(status.size_raw()))}\n'\
                                                f'**Speed**: {status.speed()} | **ETA**: {status.eta()}\n'\
                                                f"`/cancel aria {status.gid()}`" 
                                        self.status_message = text
                                        await asynciosleep(0.5)
                                else:
                                        LOGGER.info(f"Status Update Stopped, {status.process_status} Was Returned")
                                        break
                        elif status.type()==Names.ffmpeg:
                                # line = await get_ffmpeg_process_line(status.process)
                                # if line:
                                #         line = line.decode('utf-8').strip()
                                #         status.save_log(line)
                                #         print(line)
                                if not check_running_process(self.process_id):
                                                await self.event.reply("🔒Task Cancelled By User")
                                                break
                                if status.returncode:
                                        LOGGER.info('Status Update: Stopping Because ReturnCode Exists.')
                                        break
                                if exists(status.log_file):
                                        with open(status.log_file, 'r+') as file:
                                                ffmpeg_text = file.read()
                                                time_in_us = get_value(refindall("out_time_ms=(.+)", ffmpeg_text), int, 1)
                                                progress=get_value(refindall("progress=(\w+)", ffmpeg_text), str, "error")
                                                speed=get_value(refindall("speed=(\d+\.?\d*)", ffmpeg_text), float, 1)
                                                # bitrate = get_value(refindall("bitrate=(.+)", ffmpeg_text), str, "0")
                                                # fps = get_value(refindall("fps=(.+)", ffmpeg_text), str, "0")
                                else:
                                        time_in_us = 1
                                        progress="error"
                                        speed=1
                                if progress == "end":
                                        break
                                elif progress == "error":
                                        if error_no == 30:
                                                if exists(status.log_file):
                                                        try:
                                                                LOGGER.info(f"FFMPEG Process Log File Data Start>\n{str(ffmpeg_text)}\n<end FFMPEG Log File Data")
                                                        except:
                                                                LOGGER.info(f"Failed To Get FFMPEG Log Data [{str(len(ffmpeg_text))}]")
                                                        await self.event.reply(f'❗Some Error Occurred.')
                                                else:
                                                        LOGGER.info(f"FFMPEG Log File {status.log_file} Not Found.")
                                                        await self.event.reply(f'❗FFMPEG Process Log File Not Found.')
                                        if error_no==100:
                                                break
                                        error_no+=1
                                elapsed_time = time_in_us/1000000
                                if self.process_type==Names.convert:
                                                process_state = f"{Names.STATUS[self.process_type]} To {self.convert_quality}P [{self.convert_index}]"
                                                name = status.name
                                elif self.process_type!=Names.merge:
                                                process_state = Names.STATUS[self.process_type]
                                                name = status.name
                                else:
                                                process_state = f"{Names.STATUS[self.process_type]} [{total_files} Files]"
                                                name = str(self.file_name)
                                text =f'{process_state} {multi_task_no}\n'\
                                                        f'`{name}`\n'\
                                                        f'{get_progress_bar_string(elapsed_time, status.duration)} {elapsed_time * 100 / status.duration:.1f}%\n'\
                                                        f'**Added By**: {self.added_by} | **ID**: `{self.user_id}`\n'\
                                                        f'**Engine**: FFMPEG'\
                                                        f"{ffmpeg_head if get_data()[self.user_id]['detailed_messages'] else ''}\n"\
                                                        f'**Processed**: {get_readable_time(elapsed_time)} of {get_readable_time(status.duration)}\n'\
                                                        f'**Speed**: {speed}x | **ETA**: {get_readable_time(floor( (status.duration - elapsed_time) / speed))}'\
                                                        f'{ffmpeg_status_foot(status, self.user_id, self.start_time, time_in_us)}\n'\
                                                        f'`/ffmpeg log {self.process_id}`\n'\
                                                        f"`/cancel process {self.process_id}`"
                                self.status_message = text
                                await asynciosleep(0.5)
                if status.type()==Names.aria and status.name():
                        if f"{self.dir}/{status.name()}" not in self.dw_files:
                                self.dw_files.append(f"{self.dir}/{status.name()}")
                return
        
        def telegram_update_status(self,current,total, mode, name, start_time, status, engine, client=False):
                self.ping = time()
                if client:
                        if not check_running_process(self.process_id):
                                client.stop_transmission()
                try:
                        speed = current / round(time() - start_time)
                except:
                        speed = 1
                text =f'{status}\n'\
                        f'`{name}`\n'\
                        f'{get_progress_bar_string(current,total)} {current * 100 / total:.1f}%\n'\
                        f'**Added By**: {self.added_by} | **ID**: `{self.user_id}`\n'\
                        f'**Engine**: {engine}\n'\
                        f'**{mode}**: {get_human_size(current)} of {get_human_size(total)}\n'\
                        f'**Speed**: {get_human_size(speed)}ps | **ETA**: {get_readable_time((total-current)/speed)}\n'\
                        f"`/cancel process {self.process_id}`"
                self.status_message = text
                return
                
                
        async def rclone__update_status(self, rclone_process, name, search_command, fileloc, r_config, drive_name, status):
                Cancel = False
                while True:
                    self.ping = time()
                    try:
                                async for line in rclone_process.stdout:
                                        if not check_running_process(self.process_id):
                                                Cancel = True
                                                break
                                        line = line.decode().strip()
                                        print(line)
                                        async with aio_open(f"{self.dir}/upload_log_{str(name)}.txt", "a+", encoding="utf-8") as f:
                                                        await f.write(f'{str(line)}\n')
                                        try:
                                                datam = refindall("Transferred:.*ETA.*", line)
                                                if datam is not None:
                                                    if len(datam) > 0:
                                                        progress = datam[0].replace("Transferred:", "").strip().split(",")
                                                        percentage= progress[1].strip("% ")
                                                        dwdata = progress[0].strip().split('/')
                                                        eta = progress[3].strip().replace('ETA', '').strip()
                                                        text =f'{status}\n'\
                                                                f'`{name}`\n'\
                                                                f'{get_progress_bar_from_percentage(percentage)} {percentage}%\n'\
                                                                f'**Added By**: {self.added_by} | **ID**: `{self.user_id}`\n'\
                                                                f'**Engine**: {Names.rclone}\n'\
                                                                f'**Uploaded**: {dwdata[0].strip()} of {dwdata[1].strip()}\n'\
                                                                f'**Speed**: {progress[2]} | **ETA**: {eta}\n'\
                                                                f"`/cancel process {self.process_id}`"
                                                        self.status_message = text
                                                        await asynciosleep(0.5)
                                        except Exception as e:
                                                            await self.event.reply(f'❌Error While Updating Rclone Upload Status Message: {str(e)}')
                                                            LOGGER.info(str(e))
                    except ValueError:
                            continue
                    else:
                            break
                if not Cancel:
                        await rclone_process.wait()
                        if rclone_process.returncode==0:
                                await check_file_drive_link(search_command, self.event, fileloc, r_config, drive_name, name, self.caption)
                        else:
                                if exists(f"{self.dir}/upload_log_{str(name)}.txt"):
                                                await self.event.client.send_file(self.chat_id, file=f"{self.dir}/upload_log_{str(name)}.txt", allow_cache=False, reply_to=self.event.message, caption=f"❌Error While Uploading {str(name)} To Drive")
                                else:
                                        await self.event.reply(f'❗Rclone Log File Not Found')
                else:
                        try:
                                rclone_process.kill()
                        except Exception as e:
                                LOGGER.info(str(e))
                        if exists(f"{self.dir}/upload_log_{str(name)}.txt"):
                                remove(f"{self.dir}/upload_log_{str(name)}.txt")
                        return False
                if exists(f"{self.dir}/upload_log_{str(name)}.txt"):
                        remove(f"{self.dir}/upload_log_{str(name)}.txt")
                return True
