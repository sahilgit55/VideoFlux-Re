from asyncio import Lock
from config.config import Config
from asyncio import create_task, create_subprocess_exec, sleep
from asyncio.subprocess import PIPE as asyncioPIPE
from bot_helper.Telegram.Telegram_Client import Telegram
from bot_helper.Process.Running_Process import append_running_process, remove_running_process, check_running_process
from shutil import rmtree
from bot_helper.Others.Names import Names
from bot_helper.FFMPEG.FFMPEG_Commands import get_commands
from bot_helper.FFMPEG.FFMPEG_Status import FfmpegStatus
from bot_helper.Database.User_Data import get_task_limit, get_data
from time import time
from bot_helper.FFMPEG.FFMPEG_Processes import FFMPEG
from os.path import exists
from bot_helper.Others.Helper_Functions import verify_rclone_account
from bot_helper.Rclone.Rclone_Upload import upload_drive
from os import remove



LOGGER = Config.LOGGER
working_task=[]
working_task_lock = Lock()
queued_task = []
queued_task_lock = Lock()
process_status_checker_value = [0]
process_status_checker_lock = Lock()



def create_log_file(log_file):
    with open(log_file, 'w') as _:
        LOGGER.info(f'Log File Created : {log_file}')
    return


async def clear_trash(task, trash_objects, multi_tasks):
    new_task = False
    if len(multi_tasks):
        if check_running_process(task['process_status'].process_id):
                new_process_status = multi_tasks[0]
                new_process_status.move_send_files(task['process_status'].send_files)
                multi_tasks.pop(0)
                new_process_status.replace_multi_tasks(multi_tasks)
                new_process_status.move_custom_thumbnail(task['process_status'].thumbnail)
                new_task = {}
                new_task['process_status'] = new_process_status
                new_task['functions'] = []
        else:
                for t in multi_tasks:
                    del t
    async with working_task_lock:
        if task in working_task:
            working_task.remove(task)
        if new_task:
            create_task(start_task(new_task))
            working_task.append(new_task)
    await remove_running_process(task['process_status'].process_id)
    try:
        rmtree(task['process_status'].dir)
    except:
        pass
    del task['process_status']
    if trash_objects:
        for trash in trash_objects:
            del trash
    del task
    return

async def upload_files(process_status):
    drive_uplaod = False
    if not get_data()[process_status.user_id]['upload_tg']:
        r_config = f'./userdata/{str(process_status.user_id)}_rclone.conf'
        if exists(r_config):
            drive_name = get_data()[process_status.user_id]['drive_name']
            if verify_rclone_account(r_config, drive_name):
                drive_uplaod = True
    if not drive_uplaod:
        await Telegram.upload_videos(process_status)
    else:
        await upload_drive(process_status)
    return


async def process_status_checker():
    async with process_status_checker_lock:
        if process_status_checker_value[0] == 1:
            LOGGER.info(f"Process Status Checker Is Already Running")
            return
        else:
            process_status_checker_value[0] = 1
            LOGGER.info(f"Starting Process Status Checker")
    while True:
        LOGGER.info(f"Process Status Checker: Checking For Dead Processess")
        if len(working_task)==0 and len(queued_task)==0:
            LOGGER.info(f"Stopping Process Status Checker")
            break
        try:
            for task in working_task:
                    if time()-task['process_status'].ping>600:
                        LOGGER.info(f"Removing {task['process_status'].process_type} Process Because Of No Response.")
                        await task['process_status'].event.reply(f"❗Removing This Task From Working Tasks As It Is Not Responding From Last 10 Minutes.")
                        await clear_trash(task, False, [])
                        await task_manager()
        except Exception as e:
                LOGGER.info(str(e))
        await sleep(60)
    async with process_status_checker_lock:
        process_status_checker_value[0] = 0
    return


async def add_task(task):
    async with working_task_lock:
        if len(working_task)<get_task_limit():
            LOGGER.info(f"Add Task: Adding Task To Working")
            create_task(start_task(task))
            working_task.append(task)
        else:
            async with queued_task_lock:
                queued_task.append(task)
                LOGGER.info(f"Add Task: Adding Task To Queue")
    await process_status_checker()
    return


async def task_manager():
        async with working_task_lock:
            if len(working_task)<get_task_limit():
                async with queued_task_lock:
                    if len(queued_task):
                        task = queued_task[0]
                        LOGGER.info(f"Task Manager: Adding Task From Queue To Working")
                        create_task(start_task(task))
                        working_task.append(task)
                        queued_task.pop(0)
        return


async def refresh_tasks():
    while True:
        async with working_task_lock:
            if len(working_task)<get_task_limit():
                async with queued_task_lock:
                    if len(queued_task):
                        task = queued_task[0]
                        create_task(start_task(task))
                        working_task.append(task)
                        queued_task.pop(0)
                    else:
                        break
            else:
                break
        return


def get_queued_tasks_len():
        return len(queued_task)
    

async def remove_from_working_task(process_id):
    async with working_task_lock:
        for task in working_task:
                if task['process_status'].process_id==process_id:
                    working_task.remove(task)
                    LOGGER.info(f"{process_id} Removed From Working Tasks")
                    return True
    return False



async def get_ffmpeg_log_file(process_id):
    async with working_task_lock:
        for task in working_task:
                if task['process_status'].process_id==process_id:
                    if exists(f"{task['process_status'].dir}/FFMPEG_LOG.txt"):
                        return f"{task['process_status'].dir}/FFMPEG_LOG.txt"
                    else:
                        return False
    return False


async def get_status_message(reply):
                if not len(working_task) and not len(queued_task):
                        return False
                else:
                        retry = 0
                        if not len(working_task):
                            await reply.edit('⏳Waiting For Task To Start, Please Wait')
                            while True:
                                if len(working_task):
                                    break
                                if retry==30:
                                    break
                                await sleep(1)
                                retry+=1
                        if len(working_task):
                                final_status = ""
                                for task in working_task:
                                        final_status+= task['process_status'].status_message + "\n\n"
                                return final_status
                        else:
                            return False

def get_user_id(process_id):
    for task in working_task:
        if task['process_status'].process_id==process_id:
            return task['process_status'].user_id
    return False

async def start_task(task):
    process_status = task['process_status']
    multi_tasks = process_status.multi_tasks
    process_status.update_start_time(time())
    await append_running_process(process_status.process_id)
    loop_range = len(task['functions'])
    trash_objects = []
    if loop_range:
        process_completed = False
    else:
        process_completed = True
    for i in range(loop_range):
        dw_index = f"{str(i+1)}/{str(loop_range)}"
        if task['functions'][i][0]==Names.aria:
            process_status.set_dw_index(dw_index)
            download, aria2_status = await task['functions'][i][1](*task['functions'][i][2])
            if not download:
                await process_status.event.reply(process_status.status_message)
                break
            trash_objects.append(aria2_status)
            await process_status.update_status(aria2_status)
            if aria2_status.process_status!=1:
                await process_status.event.reply(process_status.message)
                break
            else:
                process_status.move_dw_file(aria2_status.name())
        else:
            try:
                download = await Telegram.download_tg_file(process_status, task['functions'][i][1], dw_index)
                if not download:
                    break
            except Exception as e:
                    LOGGER.info(str(e))
                    break
        if not check_running_process(process_status.process_id):
            break
        if i==loop_range-1:
            process_completed = True
            process_status.set_file_name_from_send_list()
            
    if process_completed and process_status.process_type in Names.FFMPEG_PROCESSES:
            process_completed = False
            if process_status.process_type not in [Names.merge, Names.changeMetadata, Names.changeindex]:
                if not len(multi_tasks):
                        await FFMPEG.select_audio(process_status)
                        await FFMPEG.change_metadata(process_status)
            output_list = []
            if process_status.process_type==Names.convert:
                    convert_list = get_data()[process_status.user_id]['convert']['convert_list']
            else:
                    convert_list = [1]
            ffmpeg_range = len(convert_list)
            for c in range(ffmpeg_range):
                    if process_status.process_type==Names.convert:
                            process_status.update_convert_quality(convert_list[c])
                            process_status.update_convert_index(f"{str(c+1)}/{str(ffmpeg_range)}")
                    command, log_file, input_file, output_file, file_duration = get_commands(process_status)
                    LOGGER.info(str(command))
                    create_log_file(log_file)
                    ffmpeg_process = await create_subprocess_exec(
                                                                                                                            *command,
                                                                                                                            stdout=asyncioPIPE,
                                                                                                                            stderr=asyncioPIPE,
                                                                                                                            )
                    ffmpeg_status = FfmpegStatus(ffmpeg_process, log_file, input_file, output_file, file_duration)
                    create_task(ffmpeg_status.logger(process_status.process_id, process_status.dir, command))
                    trash_objects.append(ffmpeg_status)
                    LOGGER.info('Starting Status Update')
                    await process_status.update_status(ffmpeg_status)
                    if not check_running_process(process_status.process_id):
                        try:
                            ffmpeg_process.kill()
                        except Exception as e:
                            LOGGER.info(str(e))
                        break
                    else:
                        if ffmpeg_status.returncode:
                                return_code = ffmpeg_status.returncode
                        else:
                                await ffmpeg_process.wait()
                                return_code = ffmpeg_process.returncode
                        if return_code==0:
                                output_list.append(output_file)
                                process_status.replace_send_list(output_list)
                        else:
                            if exists(f"{process_status.dir}/FFMPEG_LOG.txt"):
                                    # with open(f"{process_status.dir}/FFMPEG_LOG.txt", "w", encoding="utf-8") as f:
                                    #             f.write(str(ffmpeg_status.process_logs))
                                    await process_status.event.client.send_file(process_status.chat_id, file=f"{process_status.dir}/FFMPEG_LOG.txt", allow_cache=False, reply_to=process_status.event.message, caption=f"❌{process_status.process_type} Process Error\n\nReturn Code: {return_code}\n\nFileName: {input_file.split('/')[-1]}")
                                    remove(f"{process_status.dir}/FFMPEG_LOG.txt")
                            else:
                                await process_status.event.reply(f"❗FFMPEG Log File Not Found")
                            break
                        process_completed = True
                        if exists(f"{process_status.dir}/FFMPEG_LOG.txt"):
                            remove(f"{process_status.dir}/FFMPEG_LOG.txt")
    if process_completed and process_status.process_type in Names.FFMPEG_PROCESSES:
        if get_data()[process_status.user_id]['upload_all'] or not len(multi_tasks):
                await upload_files(process_status)
        if not len(multi_tasks):
            if check_running_process(process_status.process_id):
                    await FFMPEG.gen_sample_video(process_status)
            if check_running_process(process_status.process_id):
                    await FFMPEG.generate_ss(process_status)
    elif process_completed and process_status.process_type==Names.gensample:
        await FFMPEG.gen_sample_video(process_status, force_gen=True)
    elif process_completed and process_status.process_type==Names.genss:
        await FFMPEG.generate_ss(process_status, force_gen=True)
    elif process_completed and process_status.process_type==Names.leech:
        await Telegram.upload_videos(process_status)
    elif process_completed and process_status.process_type==Names.mirror:
        await upload_drive(process_status)
    await clear_trash(task, trash_objects, multi_tasks)
    await task_manager()
    return
