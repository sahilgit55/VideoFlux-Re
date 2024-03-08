from config.config import Config
from telethon import events, Button
from bot_helper.Others.Helper_Functions import getbotuptime, get_config, delete_trash, get_logs_msg, gen_random_string, get_readable_time, get_human_size, botStartTime, get_current_time, get_env_keys, export_env_file, get_env_dict, get_host_stats
from os.path import exists
from asyncio import sleep as asynciosleep
from os import execl, makedirs, remove
from os.path import isdir, isfile
from sys import argv, executable
from bot_helper.Aria2.Aria2_Engine import Aria2, getDownloadByGid
from bot_helper.Process.Process_Status import ProcessStatus
from time import time
from asyncio import create_task
from bot_helper.Database.User_Data import get_data, new_user, change_task_limit, get_task_limit, saveoptions
from bot_helper.Telegram.Telegram_Client import Telegram
from bot_helper.Process.Running_Tasks import add_task, get_status_message, get_user_id, get_queued_tasks_len, refresh_tasks, remove_from_working_task, get_ffmpeg_log_file
from bot_helper.Process.Running_Process import remove_running_process
from asyncio import Lock
from psutil import virtual_memory, cpu_percent, disk_usage
from bot_helper.Others.Names import Names
from telethon.errors.rpcerrorlist import MessageIdInvalidError
from re import findall
from requests import get
from bot_helper.Others.SpeedTest import speedtest
from subprocess import run as srun
from heroku3 import from_key


status_update = {}
status_update_lock = Lock()


if not isdir('./userdata'):
    makedirs("./userdata")





#////////////////////////////////////Variables////////////////////////////////////#
sudo_users = Config.SUDO_USERS
owner_id = Config.OWNER_ID
allowed_chats = Config.ALLOWED_CHATS
TELETHON_CLIENT = Telegram.TELETHON_CLIENT
LOGGER = Config.LOGGER
SAVE_TO_DATABASE = Config.SAVE_TO_DATABASE

#////////////////////////////////////Functions////////////////////////////////////#


async def hardmux_multi_task(multi_process_status, event, chat_id, user_id, process_command):
        new_event = await ask_media_OR_url(event, chat_id, user_id, [process_command, "stop"], f"Send Subtitle SRT File", 120, False, True, allow_magnet=False, allow_url=False)
        if new_event and new_event not in ["cancelled", "stopped"]:
            if new_event.message.file:
                if not str(new_event.message.file.mime_type).startswith("video/") and not str(new_event.message.file.mime_type).startswith("image/"):
                    if new_event.message.file.size<512000:
                        sub_name = new_event.message.file.name
                        create_direc(f"{multi_process_status.dir}/subtitles")
                        sub_dw_loc = check_file(f"{multi_process_status.dir}/subtitles", sub_name)
                        sub_path = await new_event.download_media(file=sub_dw_loc)
                        multi_process_status.append_subtitles(sub_path)
                        return True
                    else:
                        await event.reply("❌Subtitle Size Is More Than 500KB, Is This Really A Subtitle File")
                        return False
                else:
                    await event.reply("❌I Need A Subtitle File.")
                    return False
            else:
                await event.reply("❗Only Telegram File Is Supported")
                return False
        else:
            return False



async def append_multi_task(process_status, process_name, command, event):
    multi_process_status = ProcessStatus(process_status.user_id, process_status.chat_id, process_status.user_name, process_status.user_first_name, event, process_name, process_status.file_name)
    process_add_result = True
    if process_name==Names.hardmux:
                process_add_result = await hardmux_multi_task(multi_process_status, event, process_status.chat_id, process_status.user_id, command)
    elif process_name==Names.watermark:
                process_add_result = await ask_watermark(event, process_status.chat_id, process_status.user_id, command, True, all_handle=True)
                    
    if not process_add_result:
            del multi_process_status
            return False
    else:
        process_status.append_multi_tasks(multi_process_status)
        return True



###############------Multi-Tasks------###############
async def multi_tasks(process_status, command):
    ffmpeg_functions = [Names.compress, 
                                            Names.watermark,
                                            Names.convert, 
                                            Names.hardmux]
    p_text = ''
    for p in ffmpeg_functions:
        p_text+= f"`{p}`\n"
    q = 1
    p_command = command
    ffmpeg_functions.append("stop")
    ffmpeg_functions.append("cancel")
    m_result = True
    chat_event = process_status.event
    while True:
        process_text = f'What To Do With The Output From **{str(p_command).replace("/", "").upper()}** Process\n🔶Multi Task No: {str(q)}\n🔶Choose From Below:\n\n{str(p_text)}\n🔷Send `stop` To Process Task\n🔷Send `cancel` To Cancel Task'
        process_ask_result = await ask_text_list(process_status.chat_id, process_status.user_id, chat_event, 120, process_text, ffmpeg_functions)
        if process_ask_result:
            if process_ask_result.message.message=="stop":
                    break
            elif process_ask_result.message.message=="cancel":
                    await process_ask_result.reply("✅Task Cancelled")
                    m_result = False
                    break
            add_result = await append_multi_task(process_status, process_ask_result.message.message, command, process_ask_result)
            if add_result:
                    p_command = process_ask_result.message.message
                    chat_event = process_ask_result
                    q+=1
    return m_result



###############------Create_Dire------###############
def create_direc(direc):
    if not isdir(direc):
        makedirs(direc)
    return

###############------Check_File------###############
def check_file(loc, file_name):
    if isfile(f"{loc}/{file_name}"):
        return f"{loc}/{gen_random_string(5)}_{file_name}"
    else:
        return f"{loc}/{file_name}"

###############------Download_From_Direct_Link------###############
def dw_file_from_url(url, filename):
        r = get(url, allow_redirects=True, stream=True)
        with open(filename, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=1024 * 10):
                        if chunk:
                                fd.write(chunk)
        return
    
###############------Download_Rclone_Config------###############
for user_id in get_data():
    link = get_data()[user_id]['rclone_config_link']
    if link:
        LOGGER.info(f"🔽Downloading Rclone Config For User_ID {user_id} From Link {link}")
        r_config = f'./userdata/{str(user_id)}_rclone.conf'
        try:
            dw_file_from_url(link, r_config)
        except Exception as e:
            LOGGER.info(f"❗Error While Downloading Rclone Config For User_ID {user_id} From Link {link}")
    else:
        LOGGER.info(f"🟡Rclone Config Link Not Found For User_ID {user_id}")
            

###############------Check_Magenet------###############
def is_magnet(url: str):
    magnet = findall(r"magnet:\?xt=urn:btih:[a-zA-Z0-9]*", url)
    return bool(magnet)



#////////////////////////////////////Telethon Functions////////////////////////////////////#

###############------Mention_User------###############
def get_mention(event):
    return "["+event.message.sender.first_name+"](tg://user?id="+str(event.message.sender.id)+")"

###############------Check_File_Or_URL_Event------###############
async def get_url_from_message(new_event):
        if new_event.message.file:
            return new_event
        else:
            return str(new_event.message.message)

###############------Get_Username------###############
def get_username(event):
    try:
        if event.message.sender.username:
            user_name = event.message.sender.username
        else:
            user_name = False
    except:
            user_name = False
    return user_name

###############------Check_Auth_User------###############
def user_auth_checker(event):
    if event.is_private:
        if event.message.sender.id == owner_id:
            return True
    else:
        if event.message.sender.id in sudo_users or event.message.sender.id in allowed_chats or event.message.sender.id == owner_id:
            return True
    return False

###############------Check_Sudo_User_Event------###############
def sudo_user_checker_event(event):
    if event.message.sender.id in sudo_users or event.message.sender.id == owner_id:
            return True
    return False

###############------Check_Sudo_User_ID------###############
def sudo_user_checker_id(user_id):
    if user_id in sudo_users or user_id == owner_id:
            return True
    return False

###############------Check_Owner_User_Event------###############
def owner_checker(event):
    if event.message.sender.id == owner_id:
            return True
    return False

###############------Get_Link------###############
async def get_link(event):
    custom_file_name = False
    if "|" in event.message.message:
        ext_data = event.message.message.split('|')
        custom_file_name = str(ext_data[-1]).strip()
        commands = ext_data[0].strip().split(' ')
    else:
        commands = event.message.message.split(' ')
    if len(commands)==2:
            if str(commands[1]).startswith("http") or is_magnet(commands[1]):
                return commands[1], custom_file_name
            else:
                return "invalid", custom_file_name
    else:
            if event.reply_to_msg_id:
                msg_object = await TELETHON_CLIENT.get_messages(event.message.chat.id, ids=event.reply_to_msg_id)
                if not msg_object.file:
                    if str(msg_object.message).startswith("http") or is_magnet(str(msg_object.message)):
                        return str(msg_object.message), custom_file_name
                    else:
                        return "invalid", custom_file_name
                else:
                    return msg_object, custom_file_name
            else:
                return False, custom_file_name

###############------Ask_User_ID------###############
async def get_sudo_user_id(event):
    if event.reply_to_msg_id:
        reply_data = await TELETHON_CLIENT.get_messages(event.message.chat.id, ids=event.reply_to_msg_id)
        return reply_data.from_id.user_id
    return False


###############------Get_Custom_Name------###############
async def get_custom_name(event):
    custom_file_name = False
    if "|" in event.message.message:
        ext_data = event.message.message.split('|')
        custom_file_name = str(ext_data[-1]).strip()
    return custom_file_name

###############------Ask_Text------###############
async def ask_text(chat_id, user_id, event, timeout, message, text_type, include_list=False):
    async with TELETHON_CLIENT.conversation(chat_id) as conv:
            handle = conv.wait_event(events.NewMessage(chats=chat_id, incoming=True, from_users=[user_id], func=lambda e: e.message.message), timeout=timeout)
            ask = await event.reply(f'*️⃣ {str(message)} [{str(timeout)} secs]')
            try:
                new_event = await handle
            except Exception as e:
                await ask.reply('🔃Timed Out! Task Has Been Cancelled.')
                LOGGER.info(e)
                return False
            try:
                if not include_list:
                    return text_type(new_event.message.message)
                else:
                    if text_type(new_event.message.message) not in include_list:
                        await new_event.reply(f'❌Invalid Input')
                        return False
                    else:
                        return new_event
            except:
                await new_event.reply(f'❌Invalid Input')
                return False



###############------Ask_Text_Event------###############
async def ask_text_event(chat_id, user_id, event, timeout, message, message_hint=False):
    async with TELETHON_CLIENT.conversation(chat_id) as conv:
            handle = conv.wait_event(events.NewMessage(chats=chat_id, incoming=True, from_users=[user_id], func=lambda e: e.message.message), timeout=timeout)
            msg = f"*️⃣ {str(message)} [{str(timeout)} secs]"
            if message_hint:
                msg += f"\n\n{message_hint}"
            ask = await event.reply(msg)
            try:
                new_event = await handle
            except Exception as e:
                await ask.reply('🔃Timed Out! Task Has Been Cancelled.')
                LOGGER.info(e)
                return False
            return new_event

###############------Ask_Text_List------###############
async def ask_text_list(chat_id, user_id, event, timeout, message, include_list):
    async with TELETHON_CLIENT.conversation(chat_id) as conv:
            handle = conv.wait_event(events.NewMessage(chats=chat_id, incoming=True, from_users=[user_id], func=lambda e: str(e.message.message) in include_list), timeout=timeout)
            ask = await event.reply(f'*️⃣ {str(message)} [{str(timeout)} secs]')
            try:
                new_event = await handle
            except Exception as e:
                await ask.reply('🔃Timed Out! Task Has Been Cancelled.')
                LOGGER.info(e)
                return False
            return new_event

###############------Ask Media OR URL------###############
async def ask_media_OR_url(event, chat_id, user_id, keywords, message, timeout, mtype, s_handle, allow_magnet=True, allow_url=True, message_hint=False, allow_command=False, stop_on_url=True):
    async with TELETHON_CLIENT.conversation(chat_id) as conv:
            handle = conv.wait_event(events.NewMessage(chats=chat_id, incoming=True, from_users=[user_id], func=lambda e: e.message.file or str(e.message.message) in keywords or str(e.message.message).startswith("http")), timeout=timeout)
            msg = f"*️⃣ {str(message)} [{str(timeout)} secs]"
            if message_hint:
                msg += f"\n\n{message_hint}"
            ask = await event.reply(msg)
            try:
                new_event = await handle
            except Exception as e:
                await ask.reply('🔃Timed Out! Task Has Been Cancelled.')
                return False
            if new_event.message.file:
                if mtype:
                    if not str(new_event.message.file.mime_type).startswith(mtype):
                        await new_event.reply(f'❗[{str(new_event.message.file.mime_type)}] This is not a valid file.')
                        return False
                return new_event
            elif new_event.message.message:
                if str(new_event.message.message)=='stop':
                    if s_handle:
                        await ask.reply('✅Task Stopped')
                    return "stopped"
                elif str(new_event.message.message)=='cancel':
                    await ask.reply('✅Task Cancelled')
                    return "cancelled"
                elif str(new_event.message.message).startswith("http"):
                    if allow_url:
                        return new_event
                    else:
                        await ask.reply('❌HTTP Link Are Not Allowed.')
                        if stop_on_url:
                            return "stopped"
                        else:
                            return "pass"
                elif is_magnet(str(new_event.message.message)):
                    if allow_magnet:
                        return new_event
                    else:
                        await ask.reply('❌Magnet Link Are Not Allowed.')
                        if stop_on_url:
                            return "stopped"
                        else:
                            return "pass"
                else:
                    if allow_command:
                            await ask.reply(f'❗You have already started {str(new_event.message.message).replace("/", "")} task.')
                            return "pass"
                    else:
                            await ask.reply(f'❌You already started {str(new_event.message.message).replace("/", "")} task. Now send {str(new_event.message.message)} command again')
                            return "cancelled"

###############------Ask URL------###############
async def ask_url(event, chat_id, user_id, keywords, message, timeout, s_handle, allow_magnet=True, allow_url=True, message_hint=False, allow_command=False, stop_on_url=True):
    async with TELETHON_CLIENT.conversation(chat_id) as conv:
            handle = conv.wait_event(events.NewMessage(chats=chat_id, incoming=True, from_users=[user_id], func=lambda e: str(e.message.message) in keywords or str(e.message.message).startswith("http") or is_magnet(str(e.message.message))), timeout=timeout)
            msg = f"*️⃣ {str(message)} [{str(timeout)} secs]"
            if message_hint:
                msg += f"\n\n{message_hint}"
            ask = await event.reply(msg)
            try:
                new_event = await handle
            except Exception as e:
                await ask.reply('🔃Timed Out! Task Has Been Cancelled.')
                return False
            if str(new_event.message.message)=='stop':
                    if s_handle:
                        await ask.reply('✅Task Stopped')
                    return "stopped"
            elif str(new_event.message.message)=='cancel':
                await ask.reply('✅Task Cancelled')
                return "cancelled"
            elif str(new_event.message.message).startswith("http"):
                if allow_url:
                    return new_event
                else:
                    await ask.reply('❌HTTP Link Are Not Allowed.')
                    if stop_on_url:
                        return "stopped"
                    else:
                        return "pass"
            elif is_magnet(str(new_event.message.message)):
                if allow_magnet:
                    return new_event
                else:
                    await ask.reply('❌Magnet Link Are Not Allowed.')
                    if stop_on_url:
                        return "stopped"
                    else:
                        return "pass"
            else:
                if allow_command:
                        await ask.reply(f'❗You have already started {str(new_event.message.message).replace("/", "")} task.')
                        return "pass"
                else:
                        await ask.reply(f'❌You already started {str(new_event.message.message).replace("/", "")} task. Now send {str(new_event.message.message)} command again')
                        return "cancelled"

###############------Get_Thumbnail------###############
async def get_thumbnail(process_status, keywords, timeout):
    if get_data()[process_status.user_id]['custom_thumbnail']:
        async with TELETHON_CLIENT.conversation(process_status.chat_id) as conv:
            handle = conv.wait_event(events.NewMessage(chats=process_status.chat_id, incoming=True, from_users=[process_status.user_id], func=lambda e: e.message.media or str(e.message.message) in keywords), timeout=timeout)
            ask = await process_status.event.reply(f'*️⃣ Send Thumbnail [{str(timeout)} secs]')
            try:
                new_event = await handle
            except Exception as e:
                await ask.reply('🔃Timed Out! Task Has Been Cancelled.')
                LOGGER.info(str(e))
                return
            if new_event.message.media:
                if not str(new_event.message.file.mime_type).startswith('image/'):
                    await new_event.reply(f'❗[{str(new_event.message.file.mime_type)}] This is not a valid thumbnail.')
                    return
            elif new_event.message.message:
                if str(new_event.message.message)=='pass':
                    await ask.reply('✅Task Passed')
                    return
                else:
                    await ask.reply(f'❗You already started a task, now send {str(new_event.message.message)} command again.')
                    return False
            custom_thumb = await new_event.download_media(file=f"{process_status.dir}/{process_status.process_id}.jpg")
            process_status.set_custom_thumbnail(custom_thumb)
            return
    else:
        return


###############------Ask_WaterMark------###############
async def ask_watermark(event, chat_id, user_id, cmd, wt_check, all_handle=False):
    watermark_path = f'./userdata/{str(user_id)}_watermark.jpg'
    watermark_check = exists(watermark_path)
    if watermark_check:
            if wt_check:
                return True
            text = f"Watermark Already Present\n\n🔷Send Me New Watermark Image To Replace."
    else:
            text = f"Watermark Not Present\n\n🔶Send Me Watermark Image To Save."
    new_event = await ask_media_OR_url(event, chat_id, user_id, [f"/{cmd}", "stop"], text, 120, "image/", True, False, False)
    if new_event and new_event not in ["cancelled", "stopped"]:
        await TELETHON_CLIENT.download_media(new_event.message, watermark_path)
        if exists(watermark_path):
            return True
    if all_handle:
        await new_event.reply('❗Failed To Get Watermark.')
    return False



###############------Ask_Thumbnail------###############
async def ask_thumbnail(event, chat_id, user_id, cmd):
    Thumbnail_path = f'./userdata/{str(user_id)}_Thumbnail.jpg'
    Thumbnail_check = exists(Thumbnail_path)
    if Thumbnail_check:
            text = f"Thumbnail Already Present\n\n🔷Send Me New Thumbnail To Replace."
    else:
            text = f"Thumbnail Not Present\n\n🔶Send Me Thumbnail To Save."
    new_event = await ask_media_OR_url(event, chat_id, user_id, [f"/{cmd}", "stop"], text, 120, "image/", True, False, False)
    if new_event and new_event not in ["cancelled", "stopped"]:
        await TELETHON_CLIENT.download_media(new_event.message, Thumbnail_path)
        if exists(Thumbnail_path):
            return True
    return False


async def update_status_message(event):
        reply  = await event.reply("⏳Please Wait")
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        status_update_id = gen_random_string(5)
        async with status_update_lock:
            if chat_id not in status_update:
                status_update[chat_id] = {}
            status_update[chat_id].clear()
            status_update[chat_id]['update_id'] = status_update_id
        await asynciosleep(2)
        while True:
            status_message = await get_status_message(reply)
            if not status_message:
                try:
                    await reply.edit(f"No Running Process!\n\n**CPU:** {cpu_percent()}% | **FREE:** {get_human_size(disk_usage('/').free)}\n**RAM:** {virtual_memory().percent}% | **UPTIME:** {get_readable_time(time() - botStartTime)}\n**QUEUED:** {get_queued_tasks_len()} | **TASK LIMIT:** {get_task_limit()}")
                except:
                    await event.reply(f"No Running Process!\n\n**CPU:** {cpu_percent()}% | **FREE:** {get_human_size(disk_usage('/').free)}\n**RAM:** {virtual_memory().percent}% | **UPTIME:** {get_readable_time(time() - botStartTime)}\n**QUEUED:** {get_queued_tasks_len()} | **TASK LIMIT:** {get_task_limit()}")
                break
            if status_update[chat_id]['update_id'] != status_update_id:
                await reply.delete()
                break
            if get_data()[user_id]['show_stats']:
                status_message += f"**CPU:** {cpu_percent()}% | **FREE:** {get_human_size(disk_usage('/').free)}"
                status_message += f"\n**RAM:** {virtual_memory().percent}% | **UPTIME:** {get_readable_time(time() - botStartTime)}\n"
            if get_data()[user_id]['show_time']:
                    status_message+= "**Current Time:** " + get_current_time() + "\n"
            status_message += f"**QUEUED:** {get_queued_tasks_len()} | **TASK LIMIT:** {get_task_limit()}"
            try:
                await reply.edit(status_message, buttons=[
                        [Button.inline('⭕ Close', 'close_settings')]])
            except MessageIdInvalidError:
                break
            except Exception as e:
                LOGGER.info(f"Status Update Error: {str(e)}")
            await asynciosleep(get_data()[user_id]['update_time'])
        LOGGER.info(f"Status Updating Complete")
        return


###############------Save_Rclone_Config------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/saveconfig', func=lambda e: user_auth_checker(e)))
async def _saverclone(event):
        user_id = event.message.sender.id
        chat_id = event.message.chat.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        r_config = f'./userdata/{str(user_id)}_rclone.conf'
        check_config = exists(r_config)
        link = False
        if check_config:
                text = f"Rclone Config Already Present\n\nSend Me New Config To Replace."
        else:
                text = f"Rclone Config Not Present\n\nSend Me Config To Save."
        new_event = await ask_media_OR_url(event, chat_id, user_id, ["/saveconfig", "stop"], text, 120, "text/", True, False)
        if new_event and new_event not in ["cancelled", "stopped"]:
            if new_event.message.file:
                await new_event.download_media(file=r_config)
            else:
                link = str(new_event.message.message)
                dw_file_from_url(link, r_config)
                await saveoptions(user_id, 'rclone_config_link', link, SAVE_TO_DATABASE)
            if not exists(r_config):
                await new_event.reply("❌Failed To Download Config File.")
                return
            accounts = await get_config(r_config)
            if not accounts:
                await delete_trash(r_config)
                await new_event.reply("❌Invalid Config File Or Empty Config File.")
                return
            await saveoptions(user_id, 'drive_name', accounts[0], SAVE_TO_DATABASE)
            if link:
                await saveoptions(user_id, 'rclone_config_link', link, SAVE_TO_DATABASE)
            await new_event.reply(f"✅Config Saved Successfully\n\n🔶Using {str(get_data()[user_id]['drive_name'])} Drive For Uploading.")
        return


###############------Change_Task_Limit------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/tasklimit', func=lambda e: owner_checker(e)))
async def _changetasklimit(event):
        user_id = event.message.sender.id
        chat_id = event.message.chat.id
        limit = await ask_text(chat_id, user_id, event, 120, "Send New Task Limit", int)
        if limit:
            change_task_limit(int(limit))
            await refresh_tasks()
            await event.reply(f'✅Successfully Set New Limit: {get_task_limit()}')
            return


###############------Restart------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/restart', func=lambda e: owner_checker(e)))
async def _restart(event):
        chat_id = event.message.chat.id
        reply = await event.reply("♻Restarting...")
        srun(["pkill", "-f", "aria2c|ffmpeg|rclone"])
        srun(["python3", "update.py"])
        with open(".restartmsg", "w") as f:
                f.truncate(0)
                f.write(f"{chat_id}\n{reply.id}\n")
        execl(executable, executable, *argv)
        

###############------Restart_Heroku------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/herokurestart', func=lambda e: owner_checker(e)))
async def _heroku_restart(event):
        chat_id = event.message.chat.id
        if Config.HEROKU_APP_NAME and Config.HEROKU_API_KEY:
            heroku_conn = from_key(Config.HEROKU_API_KEY)
            reply = await event.reply("♻Restarting Heroku Dyno...")
            with open(".restartmsg", "w") as f:
                    f.truncate(0)
                    f.write(f"{chat_id}\n{reply.id}\n")
            for dyno in heroku_conn.app(Config.HEROKU_APP_NAME).dynos():
                LOGGER.info(str(dyno))
                LOGGER.info(str(dyno.command))
                dyno.restart()
        else:
            await event.reply("❗Heroku App Name Or Heroku API Key Not Found")
        return


###############------Get_Logs_Message------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/log', func=lambda e: sudo_user_checker_event(e)))
async def _log(event):
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        log_file = "Logging.txt"
        if exists(log_file):
                await event.reply(str(get_logs_msg(log_file)))
        else:
            await event.reply("❗Log File Not Found")
        return


###############------Get_Log_File------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/logs', func=lambda e: sudo_user_checker_event(e)))
async def _logs(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        log_file = "Logging.txt"
        if exists(log_file):
            try:
                await TELETHON_CLIENT.send_file(chat_id, file=log_file, allow_cache=False)
            except Exception as e:
                await event.reply(str(e))
        else:
            await event.reply("❗Log File Not Found")
        return


###############------Reset_Database------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/resetdb', func=lambda e: owner_checker(e)))
async def _resetdb(event):
        await event.reply("*️⃣Are you sure?\n\n🚫 This will reset your all database 🚫", buttons=[
                [Button.inline('Yes 🚫', 'resetdb_True')],
                [Button.inline('No 😓', 'resetdb_False')],
                [Button.inline('⭕Close', 'close_settings')]
            ])
        return


###############------Save_WaterMark_Image------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/savewatermark', func=lambda e: user_auth_checker(e)))
async def _savewatermark(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        check_watermark = await ask_watermark(event, chat_id, user_id, "savewatermark", False)
        if not check_watermark:
            await event.reply("❗Failed To Get Watermark.")
        else:
            await event.reply("✅Watermark saved successfully.")
        return


###############------Save_Thumbnail------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/savethumb', func=lambda e: user_auth_checker(e)))
async def _savethumb(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        check_thumbnail = await ask_thumbnail(event, chat_id, user_id, "savethumb")
        if not check_thumbnail:
            await event.reply("❗Failed To Get Thumbnail.")
        else:
            await event.reply("✅Thumbnail saved successfully.")
        return


###############------Renew------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/renew', func=lambda e: owner_checker(e)))
async def _renew(event):
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        await event.reply("*️⃣Are you sure?\n\n🚫 This will delete all your downloads and saved watermark locally 🚫", buttons=[
                [Button.inline('Yes 🚫', 'renew_True')],
                [Button.inline('No 😓', 'renew_False')],
                [Button.inline('⭕Close', 'close_settings')]
            ])
        return

###############------Save_Stats------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/stats', func=lambda e: sudo_user_checker_event(e)))
async def _stats_msg(event):
    await event.reply(str(await get_host_stats()), parse_mode='html')
    return


###############------Speed_Test------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/speedtest', func=lambda e: sudo_user_checker_event(e)))
async def _speed_test(event):
    chat_id = event.message.chat.id
    reply = await event.reply("⏳Running Speed Test, Please Wait.....")
    try:
        file_path, caption = await speedtest()
        await TELETHON_CLIENT.send_file(chat_id, file=file_path, caption=caption, reply_to=event.message, allow_cache=False, parse_mode='html')
    except Exception as e:
        await event.reply(str(e))
    await reply.delete()
    return


###############------Start_Message------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/start'))
async def _startmsg(event):
    text = f"Hi {get_mention(event)}, I Am Alive."
    await event.reply(text, buttons=[
    [Button.url('⭐ Bot By 𝚂𝚊𝚑𝚒𝚕 ⭐', 'https://t.me/nik66')],
    [Button.url('❤ Join Channel ❤', 'https://t.me/nik66x')]
])
    return

###############------Bot_UpTime------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/time', func=lambda e: sudo_user_checker_event(e)))
async def _timecmd(event):
    await event.reply(f'♻Bot Is Alive For {getbotuptime()}')
    return


###############------Cancel Process------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/cancel', func=lambda e: user_auth_checker(e)))
async def _cancel(event):
        user_id = event.message.sender.id
        commands = event.message.message.split(' ')
        if len(commands)==3:
                processx = commands[1]
                process_id = commands[2]
                try:
                        if processx=="aria":
                            if dl := getDownloadByGid(process_id):
                                if dl.listener().user_id==user_id or user_id==owner_id:
                                    await Aria2.cancel_download(process_id)
                                    await remove_from_working_task(dl.listener().process_id)
                                else:
                                    await event.reply(f'❗You Have No Permission To Cancel This Task')
                                    return
                            else:
                                await event.reply(f'❗No download with this id')
                                return
                        elif processx=="process":
                            add_user_id = get_user_id(process_id)
                            if add_user_id:
                                if add_user_id==user_id or user_id==owner_id:
                                    cancel_result = await remove_running_process(process_id)
                                    await remove_from_working_task(process_id)
                                    if not cancel_result:
                                            await event.reply(f'❗No process with this id')
                                            return
                                else:
                                    await event.reply(f'❗You Have No Permission To Cancel This Task')
                                    return
                            else:
                                if user_id==owner_id:
                                    cancel_result = await remove_running_process(process_id)
                                    await remove_from_working_task(process_id)
                                    if not cancel_result:
                                            await event.reply(f'❗No process with this id')
                                            return
                                else:
                                    await event.reply(f'❗You Have No Permission To Cancel This Task')
                                    return
                        await event.reply(f'✅Successfully Cancelled.')
                except Exception as e:
                        await event.reply(str(e))
                return
        else:
                await event.reply(f'❗Give Me Process ID To Cancel.')
        return


###############------FFMPEF Log------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/ffmpeg', func=lambda e: user_auth_checker(e)))
async def _ffmpeg_log(event):
        chat_id = event.message.chat.id
        commands = event.message.message.split(' ')
        if len(commands)==3:
                processx = commands[1]
                process_id = commands[2]
                try:
                        if processx=="log":
                            log_file = await get_ffmpeg_log_file(process_id)
                            if log_file:
                                await TELETHON_CLIENT.send_file(chat_id, file=log_file, allow_cache=False)
                            else:
                                await event.reply("❗Log File Not Found")
                except Exception as e:
                        await event.reply(str(e))
                return
        else:
                await event.reply(f'❗Give Me Process ID.')
        return

###############------Compress------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/compress', func=lambda e: user_auth_checker(e)))
async def _compress_video(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        link, custom_file_name = await get_link(event)
        if link=="invalid":
            await event.reply("❗Invalid link")
            return
        elif not link:
            new_event = await ask_media_OR_url(event, chat_id, user_id, ["/compress", "stop"], "Send Video or URL", 120, "video/", True)
            if new_event and new_event not in ["cancelled", "stopped"]:
                link = await get_url_from_message(new_event)
            else:
                return
        user_name = get_username(event)
        user_first_name = event.message.sender.first_name
        process_status = ProcessStatus(user_id, chat_id, user_name, user_first_name, event, Names.compress, custom_file_name)
        await get_thumbnail(process_status, ["/compress", "pass"], 120)
        task = {}
        task['process_status'] = process_status
        task['functions'] = []
        if type(link)==str:
                task['functions'].append(["Aria", Aria2.add_aria2c_download, [link, process_status, False, False, False, False]])
        else:
            task['functions'].append(["TG", [link]])
        if get_data()[user_id]['multi_tasks']:
                m_result = await multi_tasks(process_status, '/compress')
                if not m_result:
                    for t in process_status.multi_tasks:
                        del t
                    for f in task['functions']:
                        del f
                    del process_status
                    return
                final_multi_tasks = []
                final_convert_task = False
                for m_task in process_status.multi_tasks:
                    if m_task.process_type==Names.convert:
                        final_convert_task = m_task
                    else:
                        final_multi_tasks.append(m_task)
                if final_convert_task:
                    final_multi_tasks.append(final_convert_task)
                process_status.replace_multi_tasks(final_multi_tasks)
                final_multi_tasks_no = len(final_multi_tasks)+1
                process_status.change_multi_tasks_no(final_multi_tasks_no)
                for f in final_multi_tasks:
                    f.change_multi_tasks_no(final_multi_tasks_no)
        create_task(add_task(task))
        await update_status_message(event)
        return


###############------Status------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/status', func=lambda e: user_auth_checker(e)))
async def _status(event):
        reply  = await event.reply("⏳Please Wait")
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        status_update_id = gen_random_string(5)
        async with status_update_lock:
            if chat_id not in status_update:
                status_update[chat_id] = {}
            status_update[chat_id].clear()
            status_update[chat_id]['update_id'] = status_update_id
        await asynciosleep(2)
        while True:
            status_message = await get_status_message(reply)
            if not status_message:
                try:
                    await reply.edit(f"No Running Process!\n\n**CPU:** {cpu_percent()}% | **FREE:** {get_human_size(disk_usage('/').free)}\n**RAM:** {virtual_memory().percent}% | **UPTIME:** {get_readable_time(time() - botStartTime)}\n**QUEUED:** {get_queued_tasks_len()} | **TASK LIMIT:** {get_task_limit()}")
                except:
                    await event.reply(f"No Running Process!\n\n**CPU:** {cpu_percent()}% | **FREE:** {get_human_size(disk_usage('/').free)}\n**RAM:** {virtual_memory().percent}% | **UPTIME:** {get_readable_time(time() - botStartTime)}\n**QUEUED:** {get_queued_tasks_len()} | **TASK LIMIT:** {get_task_limit()}")
                break
            if status_update[chat_id]['update_id'] != status_update_id:
                await reply.delete()
                break
            if get_data()[user_id]['show_stats']:
                status_message += f"**CPU:** {cpu_percent()}% | **FREE:** {get_human_size(disk_usage('/').free)}"
                status_message += f"\n**RAM:** {virtual_memory().percent}% | **UPTIME:** {get_readable_time(time() - botStartTime)}\n"
            if get_data()[user_id]['show_time']:
                    status_message+= "**Current Time:** " + get_current_time() + "\n"
            status_message += f"**QUEUED:** {get_queued_tasks_len()} | **TASK LIMIT:** {get_task_limit()}"
            try:
                await reply.edit(status_message, buttons=[
                        [Button.inline('⭕ Close', 'close_settings')]])
            except MessageIdInvalidError:
                break
            except Exception as e:
                LOGGER.info(f"Status Update Error: {str(e)}")
            await asynciosleep(get_data()[user_id]['update_time'])
        LOGGER.info(f"Status Updating Complete")
        return


###############------Settings------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/settings', func=lambda e: user_auth_checker(e)))
async def _settings(event):
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        text = f"⚙ Hi {get_mention(event)} Choose Your Settings"
        await event.reply(text, buttons=[
        [Button.inline('#️⃣ General', 'general_settings')],
        [Button.inline('❣ Telegram', 'telegram_settings')],
        [Button.inline('📝 Progress Bar', 'progress_settings')],
        [Button.inline('🏮 Compression', 'compression_settings')],
        [Button.inline('🛺 Watermark', 'watermark_settings')],
        [Button.inline('🍧 Merge', 'merge_settings')],
        [Button.inline('🚜 Convert', 'convert_settings')],
        [Button.inline('🚍 HardMux', 'hardmux_settings')],
        [Button.inline('🎮 SoftMux', 'softmux_settings')],
        [Button.inline('🛩SoftReMux', 'softremux_settings')],
        [Button.inline('⭕Close Settings', 'close_settings')]
    ])
        return

###############------Watermark------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/watermark', func=lambda e: user_auth_checker(e)))
async def _add_watermark_to_video(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        check_watermark = await ask_watermark(event, chat_id, user_id, "watermark", True)
        if not check_watermark:
            await event.reply("❗Failed To Get Watermark.")
            return
        link, custom_file_name = await get_link(event)
        if link=="invalid":
            await event.reply("❗Invalid link")
            return
        elif not link:
            new_event = await ask_media_OR_url(event, chat_id, user_id, ["/watermark", "stop"], "Send Video or URL", 120, "video/", True)
            if new_event and new_event not in ["cancelled", "stopped"]:
                link = await get_url_from_message(new_event)
            else:
                return
        user_name = get_username(event)
        user_first_name = event.message.sender.first_name
        process_status = ProcessStatus(user_id, chat_id, user_name, user_first_name, event, Names.watermark, custom_file_name)
        await get_thumbnail(process_status, ["/watermark", "pass"], 120)
        task = {}
        task['process_status'] = process_status
        task['functions'] = []
        if type(link)==str:
                task['functions'].append(["Aria", Aria2.add_aria2c_download, [link, process_status, False, False, False, False]])
        else:
            task['functions'].append(["TG", [link]])
        if get_data()[user_id]['multi_tasks']:
                m_result = await multi_tasks(process_status, '/watermark')
                if not m_result:
                    for t in process_status.multi_tasks:
                        del t
                    for f in task['functions']:
                        del f
                    del process_status
                    return
                final_multi_tasks = []
                final_convert_task = False
                for m_task in process_status.multi_tasks:
                    if m_task.process_type==Names.convert:
                        final_convert_task = m_task
                    else:
                        final_multi_tasks.append(m_task)
                if final_convert_task:
                    final_multi_tasks.append(final_convert_task)
                process_status.replace_multi_tasks(final_multi_tasks)
                final_multi_tasks_no = len(final_multi_tasks)+1
                process_status.change_multi_tasks_no(final_multi_tasks_no)
                for f in final_multi_tasks:
                    f.change_multi_tasks_no(final_multi_tasks_no)
        create_task(add_task(task))
        await update_status_message(event)
        return


###############------Merge_Videos------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/merge', func=lambda e: user_auth_checker(e)))
async def _merge_videos(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        custom_file_name = await get_custom_name(event)
        user_name = get_username(event)
        user_first_name = event.message.sender.first_name
        process_status = ProcessStatus(user_id, chat_id, user_name, user_first_name, event, Names.merge, custom_file_name)
        task = {}
        task['process_status'] = process_status
        task['functions'] = []
        file_index = 1
        Cancel = False
        while True:
            new_event = await ask_media_OR_url(event, chat_id, user_id, ["/merge", "stop", "cancel"], f"Send Video or URL No {file_index}", 120, "video/", False, message_hint=f"🔷Send `stop` To Process Merge\n🔷Send `cancel` To Cancel Merge Process", allow_command=True)
            if new_event and new_event not in ["cancelled", "stopped", "pass"]:
                link = await get_url_from_message(new_event)
                if type(link)==str:
                    task['functions'].append(["Aria", Aria2.add_aria2c_download, [link, process_status, False, False, False, False]])
                else:
                    task['functions'].append(["TG", [link]])
                file_index+=1
            elif new_event=="stopped":
                break
            elif new_event=="cancelled":
                Cancel = True
                break
            elif not new_event:
                Cancel = True
                break
        if Cancel:
            del process_status
            return
        if len(task['functions'])<2:
            del process_status
            await event.reply("❗Atleast 2 Files Required To Merge")
            return
        await get_thumbnail(process_status, ["/merge", "pass"], 120)
        if get_data()[user_id]['multi_tasks']:
                m_result = await multi_tasks(process_status, '/merge')
                if not m_result:
                    for t in process_status.multi_tasks:
                        del t
                    for f in task['functions']:
                        del f
                    del process_status
                    return
                final_multi_tasks = []
                final_convert_task = False
                for m_task in process_status.multi_tasks:
                    if m_task.process_type==Names.convert:
                        final_convert_task = m_task
                    else:
                        final_multi_tasks.append(m_task)
                if final_convert_task:
                    final_multi_tasks.append(final_convert_task)
                process_status.replace_multi_tasks(final_multi_tasks)
                final_multi_tasks_no = len(final_multi_tasks)+1
                process_status.change_multi_tasks_no(final_multi_tasks_no)
                for f in final_multi_tasks:
                    f.change_multi_tasks_no(final_multi_tasks_no)
        create_task(add_task(task))
        await update_status_message(event)
        return
    

###############------SoftMux------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/softmux', func=lambda e: user_auth_checker(e)))
async def _softmux_subtitles(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        link, custom_file_name = await get_link(event)
        if link=="invalid":
            await event.reply("❗Invalid link")
            return
        elif not link:
            new_event = await ask_media_OR_url(event, chat_id, user_id, ["/softmux", "stop"], "Send Video or URL", 120, "video/", True)
            if new_event and new_event not in ["cancelled", "stopped"]:
                link = await get_url_from_message(new_event)
            else:
                return
        user_name = get_username(event)
        user_first_name = event.message.sender.first_name
        process_status = ProcessStatus(user_id, chat_id, user_name, user_first_name, event, Names.softmux, custom_file_name)
        file_index = 1
        Cancel = False
        while True:
            new_event = await ask_media_OR_url(event, chat_id, user_id, ["/softmux", "stop", "cancel"], f"Send Subtitle SRT File No {file_index}", 120, False, False, message_hint=f"🔷Send `stop` To Process SoftMux\n🔷Send `cancel` To Cancel SoftMux Process", allow_command=True, allow_magnet=False, allow_url=False, stop_on_url=False)
            if new_event and new_event not in ["cancelled", "stopped", "pass"]:
                if new_event.message.file:
                    if not str(new_event.message.file.mime_type).startswith("video/") and not str(new_event.message.file.mime_type).startswith("image/"):
                        if new_event.message.file.size<512000:
                            sub_name = new_event.message.file.name
                            create_direc(f"{process_status.dir}/subtitles")
                            sub_dw_loc = check_file(f"{process_status.dir}/subtitles", sub_name)
                            sub_path = await new_event.download_media(file=sub_dw_loc)
                            process_status.append_subtitles(sub_path)
                            file_index+=1
                        else:
                            await event.reply("❌Subtitle Size Is More Than 500KB, Is This Really A Subtitle File")
                    else:
                        await event.reply("❌I Need A Subtitle File")
                else:
                    await event.reply("❗Only Telegram File Is Supported")
            elif new_event=="stopped":
                break
            elif new_event=="cancelled":
                Cancel = True
                break
            elif not new_event:
                Cancel = True
                break
        if Cancel:
            del process_status
            return
        if len(process_status.subtitles)==0:
            del process_status
            await event.reply("❗Atleast 1 Files Required To SoftMux")
            return
        await get_thumbnail(process_status, ["/softmux", "pass"], 120)
        task = {}
        task['process_status'] = process_status
        task['functions'] = []
        if type(link)==str:
                task['functions'].append(["Aria", Aria2.add_aria2c_download, [link, process_status, False, False, False, False]])
        else:
            task['functions'].append(["TG", [link]])
        if get_data()[user_id]['multi_tasks']:
                m_result = await multi_tasks(process_status, '/softmux')
                if not m_result:
                    for t in process_status.multi_tasks:
                        del t
                    for f in task['functions']:
                        del f
                    del process_status
                    return
                final_multi_tasks = []
                final_convert_task = False
                for m_task in process_status.multi_tasks:
                    if m_task.process_type==Names.convert:
                        final_convert_task = m_task
                    else:
                        final_multi_tasks.append(m_task)
                if final_convert_task:
                    final_multi_tasks.append(final_convert_task)
                process_status.replace_multi_tasks(final_multi_tasks)
                final_multi_tasks_no = len(final_multi_tasks)+1
                process_status.change_multi_tasks_no(final_multi_tasks_no)
                for f in final_multi_tasks:
                    f.change_multi_tasks_no(final_multi_tasks_no)
        create_task(add_task(task))
        await update_status_message(event)
        return
    
###############------softremux------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/softremux', func=lambda e: user_auth_checker(e)))
async def _softremux_subtitles(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        link, custom_file_name = await get_link(event)
        if link=="invalid":
            await event.reply("❗Invalid link")
            return
        elif not link:
            new_event = await ask_media_OR_url(event, chat_id, user_id, ["/softremux", "stop"], "Send Video or URL", 120, "video/", True)
            if new_event and new_event not in ["cancelled", "stopped"]:
                link = await get_url_from_message(new_event)
            else:
                return
        user_name = get_username(event)
        user_first_name = event.message.sender.first_name
        process_status = ProcessStatus(user_id, chat_id, user_name, user_first_name, event, Names.softremux, custom_file_name)
        file_index = 1
        Cancel = False
        while True:
            new_event = await ask_media_OR_url(event, chat_id, user_id, ["/softremux", "stop", "cancel"], f"Send Subtitle SRT File No {file_index}", 120, False, False, message_hint=f"🔷Send `stop` To Process Softremux\n🔷Send `cancel` To Cancel Softremux Process", allow_command=True, allow_magnet=False, allow_url=False, stop_on_url=False)
            if new_event and new_event not in ["cancelled", "stopped", "pass"]:
                if new_event.message.file:
                    if not str(new_event.message.file.mime_type).startswith("video/") and not str(new_event.message.file.mime_type).startswith("image/"):
                        if new_event.message.file.size<512000:
                            sub_name = new_event.message.file.name
                            create_direc(f"{process_status.dir}/subtitles")
                            sub_dw_loc = check_file(f"{process_status.dir}/subtitles", sub_name)
                            sub_path = await new_event.download_media(file=sub_dw_loc)
                            process_status.append_subtitles(sub_path)
                            file_index+=1
                        else:
                            await event.reply("❌Subtitle Size Is More Than 500KB, Is This Really A Subtitle File")
                    else:
                        await event.reply("❌I Need A Subtitle File.")
                else:
                    await event.reply("❗Only Telegram File Is Supported")
            elif new_event=="stopped":
                break
            elif new_event=="cancelled":
                Cancel = True
                break
            elif not new_event:
                Cancel = True
                break
        if Cancel:
            del process_status
            return
        if len(process_status.subtitles)==0:
            del process_status
            await event.reply("❗Atleast 1 Files Required To softremux")
            return
        await get_thumbnail(process_status, ["/softremux", "pass"], 120)
        task = {}
        task['process_status'] = process_status
        task['functions'] = []
        if type(link)==str:
                task['functions'].append(["Aria", Aria2.add_aria2c_download, [link, process_status, False, False, False, False]])
        else:
            task['functions'].append(["TG", [link]])
        if get_data()[user_id]['multi_tasks']:
                m_result = await multi_tasks(process_status, '/softremux')
                if not m_result:
                    for t in process_status.multi_tasks:
                        del t
                    for f in task['functions']:
                        del f
                    del process_status
                    return
                final_multi_tasks = []
                final_convert_task = False
                for m_task in process_status.multi_tasks:
                    if m_task.process_type==Names.convert:
                        final_convert_task = m_task
                    else:
                        final_multi_tasks.append(m_task)
                if final_convert_task:
                    final_multi_tasks.append(final_convert_task)
                process_status.replace_multi_tasks(final_multi_tasks)
                final_multi_tasks_no = len(final_multi_tasks)+1
                process_status.change_multi_tasks_no(final_multi_tasks_no)
                for f in final_multi_tasks:
                    f.change_multi_tasks_no(final_multi_tasks_no)
        create_task(add_task(task))
        await update_status_message(event)
        return

###############------Convert------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/convert', func=lambda e: user_auth_checker(e)))
async def _convert_video(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        link, custom_file_name = await get_link(event)
        if link=="invalid":
            await event.reply("❗Invalid link")
            return
        elif not link:
            new_event = await ask_media_OR_url(event, chat_id, user_id, ["/convert", "stop"], "Send Video or URL", 120, "video/", True)
            if new_event and new_event not in ["cancelled", "stopped"]:
                link = await get_url_from_message(new_event)
            else:
                return
        user_name = get_username(event)
        user_first_name = event.message.sender.first_name
        process_status = ProcessStatus(user_id, chat_id, user_name, user_first_name, event, Names.convert, custom_file_name)
        await get_thumbnail(process_status, ["/convert", "pass"], 120)
        task = {}
        task['process_status'] = process_status
        task['functions'] = []
        if type(link)==str:
                task['functions'].append(["Aria", Aria2.add_aria2c_download, [link, process_status, False, False, False, False]])
        else:
            task['functions'].append(["TG", [link]])
        create_task(add_task(task))
        await update_status_message(event)
        return


###############------hardmux------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/hardmux', func=lambda e: user_auth_checker(e)))
async def _hardmux_subtitle(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        link, custom_file_name = await get_link(event)
        if link=="invalid":
            await event.reply("❗Invalid link")
            return
        elif not link:
            new_event = await ask_media_OR_url(event, chat_id, user_id, ["/hardmux", "stop"], "Send Video or URL", 120, "video/", True)
            if new_event and new_event not in ["cancelled", "stopped"]:
                link = await get_url_from_message(new_event)
            else:
                return
        user_name = get_username(event)
        user_first_name = event.message.sender.first_name
        process_status = ProcessStatus(user_id, chat_id, user_name, user_first_name, event, Names.hardmux, custom_file_name)
        new_event = await ask_media_OR_url(event, chat_id, user_id, ["/hardmux", "stop"], f"Send Subtitle SRT File", 120, False, True, allow_magnet=False, allow_url=False)
        if new_event and new_event not in ["cancelled", "stopped"]:
            if new_event.message.file:
                if not str(new_event.message.file.mime_type).startswith("video/") and not str(new_event.message.file.mime_type).startswith("image/"):
                    if new_event.message.file.size<512000:
                        sub_name = new_event.message.file.name
                        create_direc(f"{process_status.dir}/subtitles")
                        sub_dw_loc = check_file(f"{process_status.dir}/subtitles", sub_name)
                        sub_path = await new_event.download_media(file=sub_dw_loc)
                        process_status.append_subtitles(sub_path)
                    else:
                        await event.reply("❌Subtitle Size Is More Than 500KB, Is This Really A Subtitle File")
                        del process_status
                        return
                else:
                    await event.reply("❌I Need A Subtitle File.")
                    del process_status
                    return
            else:
                await event.reply("❗Only Telegram File Is Supported")
                del process_status
                return
        else:
            del process_status
            return
        if len(process_status.subtitles)==0:
            del process_status
            await event.reply("❗Atleast 1 Files Required To hardmux")
            return
        await get_thumbnail(process_status, ["/hardmux", "pass"], 120)
        task = {}
        task['process_status'] = process_status
        task['functions'] = []
        if type(link)==str:
                task['functions'].append(["Aria", Aria2.add_aria2c_download, [link, process_status, False, False, False, False]])
        else:
            task['functions'].append(["TG", [link]])
        if get_data()[user_id]['multi_tasks']:
                m_result = await multi_tasks(process_status, '/hardmux')
                if not m_result:
                    for t in process_status.multi_tasks:
                        del t
                    for f in task['functions']:
                        del f
                    del process_status
                    return
                final_multi_tasks = []
                final_convert_task = False
                for m_task in process_status.multi_tasks:
                    if m_task.process_type==Names.convert:
                        final_convert_task = m_task
                    else:
                        final_multi_tasks.append(m_task)
                if final_convert_task:
                    final_multi_tasks.append(final_convert_task)
                process_status.replace_multi_tasks(final_multi_tasks)
                final_multi_tasks_no = len(final_multi_tasks)+1
                process_status.change_multi_tasks_no(final_multi_tasks_no)
                for f in final_multi_tasks:
                    f.change_multi_tasks_no(final_multi_tasks_no)
        create_task(add_task(task))
        await update_status_message(event)
        return

###############------Change_Config------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/changeconfig', func=lambda e: owner_checker(e)))
async def _changeconfig(event):
        if not exists('config.env'):
            await event.reply("❗`config.env` File Not Found")
            return
        tg_button = []
        for key in get_env_keys('config.env'):
            tg_button.append([Button.inline(key, f'env_{key}')])
        if tg_button:
            tg_button.append([Button.inline('⭕Close Settings', 'close_settings')])
            await event.reply("Choose Variable To Change", buttons=tg_button)
        else:
            await event.reply("❗No Variable In `config.env` File")
        return

###############------Clear_Config------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/clearconfigs', func=lambda e: owner_checker(e)))
async def _clearconfig(event):
        if exists('./userdata/botconfig.env'):
            remove("./userdata/botconfig.env")
            await event.reply(f"✅Successfully Cleared")
        else:
            await event.reply(f"❗Config Not Found")
        return

###############------Check_Sudo------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/checksudo', func=lambda e: owner_checker(e)))
async def _checksudo(event):
    await event.reply(str(sudo_users))
    return
    

###############------Add_Sudo------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/addsudo', func=lambda e: owner_checker(e)))
async def _addsudo(event):
    chat_id = event.message.chat.id
    user_id = event.message.sender.id
    sudo_id = await get_sudo_user_id(event)
    if not sudo_id:
        sudo_id = await ask_text(chat_id, user_id, event, 120, "Send User ID", int)
        if not sudo_id:
            return
    if sudo_id not in sudo_users:
            sudo_users.append(sudo_id)
            if exists("./userdata/botconfig.env"):
                config_dict = get_env_dict('./userdata/botconfig.env')
            elif exists("config.env"):
                config_dict = get_env_dict('config.env')
            else:
                config_dict = {}
            sudo_data = ""
            for u in sudo_users:
                sudo_data+= f"{u} "
            config_dict["SUDO_USERS"] = sudo_data.strip()
            export_env_file("./userdata/botconfig.env", config_dict)
            await event.reply(f"✅Successfully Added To Sudo Users.\n\n{str(sudo_users)}")
            return
    else:
        await event.reply(f"❗ID Already In Sudo Users.\n\n{str(sudo_users)}")
        return


###############------Delete_Sudo------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/delsudo', func=lambda e: owner_checker(e)))
async def _delsudo(event):
    chat_id = event.message.chat.id
    user_id = event.message.sender.id
    sudo_id = await get_sudo_user_id(event)
    if not sudo_id:
        sudo_id = await ask_text(chat_id, user_id, event, 120, "Send User ID", int)
        if not sudo_id:
            return
    if sudo_id in sudo_users:
            sudo_users.remove(sudo_id)
            if exists("./userdata/botconfig.env"):
                config_dict = get_env_dict('./userdata/botconfig.env')
            elif exists("config.env"):
                config_dict = get_env_dict('config.env')
            else:
                config_dict = {}
            sudo_data = ""
            for u in sudo_users:
                sudo_data+= f"{u} "
            config_dict["SUDO_USERS"] = sudo_data.strip()
            export_env_file("./userdata/botconfig.env", config_dict)
            await event.reply(f"✅Successfully Removed From Sudo Users.\n\n{str(sudo_users)}")
            return
    else:
        await event.reply(f"❗ID Not Found In Sudo Users.\n\n{str(sudo_users)}")
        return


###############------Generate_Sample_Video------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/gensample', func=lambda e: user_auth_checker(e)))
async def _gen_video_sample(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        link, custom_file_name = await get_link(event)
        if link=="invalid":
            await event.reply("❗Invalid link")
            return
        elif not link:
            new_event = await ask_media_OR_url(event, chat_id, user_id, ["/gensample", "stop"], "Send Video or URL", 120, "video/", True)
            if new_event and new_event not in ["cancelled", "stopped"]:
                link = await get_url_from_message(new_event)
            else:
                return
        user_name = get_username(event)
        user_first_name = event.message.sender.first_name
        process_status = ProcessStatus(user_id, chat_id, user_name, user_first_name, event, Names.gensample, custom_file_name)
        task = {}
        task['process_status'] = process_status
        task['functions'] = []
        if type(link)==str:
                task['functions'].append(["Aria", Aria2.add_aria2c_download, [link, process_status, False, False, False, False]])
        else:
            task['functions'].append(["TG", [link]])
        create_task(add_task(task))
        await update_status_message(event)
        return

###############------Generate_Screenshots------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/genss', func=lambda e: user_auth_checker(e)))
async def _gen_screenshots(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        link, custom_file_name = await get_link(event)
        if link=="invalid":
            await event.reply("❗Invalid link")
            return
        elif not link:
            new_event = await ask_media_OR_url(event, chat_id, user_id, ["/genss", "stop"], "Send Video or URL", 120, "video/", True)
            if new_event and new_event not in ["cancelled", "stopped"]:
                link = await get_url_from_message(new_event)
            else:
                return
        user_name = get_username(event)
        user_first_name = event.message.sender.first_name
        process_status = ProcessStatus(user_id, chat_id, user_name, user_first_name, event, Names.genss, custom_file_name)
        task = {}
        task['process_status'] = process_status
        task['functions'] = []
        if type(link)==str:
                task['functions'].append(["Aria", Aria2.add_aria2c_download, [link, process_status, False, False, False, False]])
        else:
            task['functions'].append(["TG", [link]])
        create_task(add_task(task))
        await update_status_message(event)
        return


###############------Change_MetaData------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/changemetadata', func=lambda e: user_auth_checker(e)))
async def _change_metadata(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        command = '/changemetadata'
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        link, custom_file_name = await get_link(event)
        if link=="invalid":
            await event.reply("❗Invalid link")
            return
        elif not link:
            new_event = await ask_media_OR_url(event, chat_id, user_id, [command, "stop"], "Send Video or URL", 120, "video/", True)
            if new_event and new_event not in ["cancelled", "stopped"]:
                link = await get_url_from_message(new_event)
            else:
                return
        metadata_event = await ask_text_event(chat_id, user_id, event, 120, "Send MetaData", message_hint="🔷`a` Is For Audio & `s` Is For Subtitle\n🔷 Send In The Format As Shown Below:\n\n`a:0-AudioLanguage-AudioTitle` (To Change Audio Number 1 Metadata)\n`s:0-SubLanguage-SubTitle` (To Change Subtitle Number 1 Metadata)\n\ne.g. `a:1-eng-nik66bots` (To Change Audio Number 2 Metadata)")
        if not metadata_event:
            return
        custom_metadata_list = str(metadata_event.message.message).split('\n')
        custom_metadata = []
        for m in custom_metadata_list:
            mdata = str(m).strip().split('-')
            LOGGER.info(mdata)
            try:
                sindex = str(mdata[0]).strip().lower()
                mlang =  str(mdata[1]).lower()
                mtilte = str(mdata[2])
                custom_metadata.append([f'-metadata:s:{sindex}', f"language={mlang}", f'-metadata:s:{str(sindex)}', f"title={mtilte}"])
            except Exception as e:
                await metadata_event.reply(f"❗Invalid Metadata, Error: {str(e)}")
                return
        user_name = get_username(event)
        user_first_name = event.message.sender.first_name
        process_status = ProcessStatus(user_id, chat_id, user_name, user_first_name, event, Names.changeMetadata, custom_file_name, custom_metadata=custom_metadata)
        task = {}
        task['process_status'] = process_status
        task['functions'] = []
        if type(link)==str:
                task['functions'].append(["Aria", Aria2.add_aria2c_download, [link, process_status, False, False, False, False]])
        else:
            task['functions'].append(["TG", [link]])
        await get_thumbnail(process_status, [command, "pass"], 120)
        create_task(add_task(task))
        await update_status_message(event)
        return


###############------Change_index------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/changeindex', func=lambda e: user_auth_checker(e)))
async def _change_index(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        command = '/changeindex'
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        link, custom_file_name = await get_link(event)
        if link=="invalid":
            await event.reply("❗Invalid link")
            return
        elif not link:
            new_event = await ask_media_OR_url(event, chat_id, user_id, [command, "stop"], "Send Video or URL", 120, "video/", True)
            if new_event and new_event not in ["cancelled", "stopped"]:
                link = await get_url_from_message(new_event)
            else:
                return
        index_event = await ask_text_event(chat_id, user_id, event, 120, "Send index", message_hint="🔷`a` Is For Audio & `s` Is For Subtitle\n🔷 Send In The Format As Shown Below:\n\n`a-3-1-2` (To Change Audio Index In 3rd, 1st and 2nd order)\n`s-2-1` (To Change Subtitle Index In 2nd and 1st order)")
        if not index_event:
            return
        custom_index_list = str(index_event.message.message).split('\n')
        custom_index = []
        for m in custom_index_list:
            mdata = str(m).strip().split('-')
            LOGGER.info(mdata)
            try:
                stream = str(mdata[0]).strip().lower()
                mdata.pop(0)
                for s in mdata:
                    s = int(s.strip())-1
                    custom_index.append("-map")
                    custom_index.append(f"0:{stream}:{s}")
                custom_index+= [f"-disposition:{stream}:0", "default"]
            except Exception as e:
                await index_event.reply(f"❗Invalid index, Error: {str(e)}")
                return
        user_name = get_username(event)
        user_first_name = event.message.sender.first_name
        process_status = ProcessStatus(user_id, chat_id, user_name, user_first_name, event, Names.changeindex, custom_file_name, custom_index=custom_index)
        task = {}
        task['process_status'] = process_status
        task['functions'] = []
        if type(link)==str:
                task['functions'].append(["Aria", Aria2.add_aria2c_download, [link, process_status, False, False, False, False]])
        else:
            task['functions'].append(["TG", [link]])
        await get_thumbnail(process_status, [command, "pass"], 120)
        create_task(add_task(task))
        await update_status_message(event)
        return


###############------Leech_File------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/leech', func=lambda e: user_auth_checker(e)))
async def _leech_file(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        link, custom_file_name = await get_link(event)
        if link=="invalid":
            await event.reply("❗Invalid link")
            return
        elif not link:
            new_event = await ask_url(event, chat_id, user_id, ["/leech", "stop"], "Send Link", 120, True)
            if new_event and new_event not in ["cancelled", "stopped"]:
                link = await get_url_from_message(new_event)
            else:
                return
        user_name = get_username(event)
        user_first_name = event.message.sender.first_name
        process_status = ProcessStatus(user_id, chat_id, user_name, user_first_name, event, Names.leech, custom_file_name)
        task = {}
        task['process_status'] = process_status
        task['functions'] = []
        if type(link)==str:
                task['functions'].append(["Aria", Aria2.add_aria2c_download, [link, process_status, False, False, False, False]])
        else:
            task['functions'].append(["TG", [link]])
        await get_thumbnail(process_status, ["/leech", "pass"], 120)
        create_task(add_task(task))
        await update_status_message(event)
        return


###############------mirror_File------###############
@TELETHON_CLIENT.on(events.NewMessage(incoming=True, pattern='/mirror', func=lambda e: user_auth_checker(e)))
async def _mirror_file(event):
        chat_id = event.message.chat.id
        user_id = event.message.sender.id
        if user_id not in get_data():
                await new_user(user_id, SAVE_TO_DATABASE)
        link, custom_file_name = await get_link(event)
        if link=="invalid":
            await event.reply("❗Invalid link")
            return
        elif not link:
            new_event = await ask_url(event, chat_id, user_id, ["/mirror", "stop"], "Send Link", 120, True)
            if new_event and new_event not in ["cancelled", "stopped"]:
                link = await get_url_from_message(new_event)
            else:
                return
        user_name = get_username(event)
        user_first_name = event.message.sender.first_name
        process_status = ProcessStatus(user_id, chat_id, user_name, user_first_name, event, Names.mirror, custom_file_name)
        task = {}
        task['process_status'] = process_status
        task['functions'] = []
        if type(link)==str:
                task['functions'].append(["Aria", Aria2.add_aria2c_download, [link, process_status, False, False, False, False]])
        else:
            task['functions'].append(["TG", [link]])
        await get_thumbnail(process_status, ["/mirror", "pass"], 120)
        create_task(add_task(task))
        await update_status_message(event)
        return