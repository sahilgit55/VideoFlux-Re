from config.config import Config
from telethon import TelegramClient
from telethon.sessions import StringSession
from pyrogram import Client as PyrogramClient
from bot_helper.Others.Helper_Functions import get_video_duration
from bot_helper.Telegram.Fast_Telethon import upload_file, download_file
from bot_helper.Database.User_Data import get_data
from time import time
from telethon.tl.types import DocumentAttributeVideo
from bot_helper.Process.Running_Process import check_running_process
from bot_helper.Others.Names import Names
from os.path import isdir, getsize
from os import makedirs
from bot_helper.FFMPEG.FFMPEG_Processes import FFMPEG
from bot_helper.Rclone.Rclone_Upload import upload_single_drive
from os.path import exists
from bot_helper.Others.Helper_Functions import verify_rclone_account


def create_direc(direc):
    if not isdir(direc):
        makedirs(direc)
    return

async def check_size_limit():
        size = 2097151000
        if Telegram.TELETHON_USER_CLIENT:
                user = await Telegram.TELETHON_USER_CLIENT.get_me()
                if user.premium:
                    size = 4194304000
        return size

async def get_split_size(user_id):
    if get_data()[user_id]['upload_tg']:
            if get_data()[user_id]['split']=='2GB':
                split_size = 2097151000
            else:
                split_size = await check_size_limit()
            return split_size
    else:
        return False


LOGGER = Config.LOGGER


class Telegram:
    TELETHON_CLIENT = TelegramClient(Config.NAME, Config.API_ID, Config.API_HASH)
    PYROGRAM_CLIENT = PyrogramClient(
    f"Pyrogram_{Config.NAME}",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.TOKEN)
    if Config.USE_SESSION_STRING=="True":
        TELETHON_USER_CLIENT = TelegramClient(StringSession(Config.SESSION_STRING), Config.API_ID, Config.API_HASH)
    else:
        TELETHON_USER_CLIENT = False
    
    async def upload_videos_on_telegram(process_status):
            total_files = len(process_status.send_files)
            files = process_status.send_files
            chat_id = process_status.chat_id
            caption = process_status.caption
            event = process_status.event
            process_id = process_status.process_id
            thumbnail = process_status.thumbnail if process_status.thumbnail else "./thumb.jpg"
            for i in range(total_files):
                start_time = time()
                duration = get_video_duration(files[i])
                filename = files[i].split("/")[-1]
                file_caption = f"**Name**: {filename}\n" + str(caption).strip() if caption else f"**Name**: {filename}"
                status = f"{Names.STATUS_UPLOADING} [{str(i+1)}/{str(total_files)}]"
                size_limit = await check_size_limit()
                file_size = getsize(files[i])
                if file_size>size_limit:
                        r_config = f'./userdata/{str(process_status.user_id)}_rclone.conf'
                        drive_name = get_data()[process_status.user_id]['drive_name']
                        if get_data()[process_status.user_id]['auto_drive'] and exists(r_config) and verify_rclone_account(r_config, drive_name):
                                await upload_single_drive(process_status, files[i], status, r_config, drive_name, filename)
                        else:
                            await event.reply(f"❌File Size Is Greater Than Telegram Upload Limit")
                            LOGGER.info(f"File Size: {file_size}, Limit: {size_limit}, Name: {filename}")
                elif file_size<=2097151000:
                        if get_data()[process_status.user_id]['tgupload']=="Telethon":
                                try:
                                    with open(files[i], "rb") as f:
                                        uploaded_file = await upload_file(
                                            client=Telegram.TELETHON_CLIENT,
                                            file=f,
                                            name=filename,
                                            check_data=process_id,
                                            progress_callback=lambda current,total: process_status.telegram_update_status(current,total, "Uploaded", filename, start_time, status, get_data()[process_status.user_id]['tgupload']))
                                    await Telegram.TELETHON_CLIENT.send_file(chat_id, file=uploaded_file, thumb=thumbnail, allow_cache=False, supports_streaming=True, caption=file_caption, reply_to=event.message, attributes=(DocumentAttributeVideo(duration, 0, 0),))
                                except Exception as e:
                                    if str(e)!="Cancelled":
                                        await event.reply(f"❗Telethon Error While Uploading File {filename}\n\nError: {str(e)}")
                        else:
                            if process_status.event.is_group and Config.AUTH_GROUP_ID:
                                        chat_id = Config.AUTH_GROUP_ID
                            try:
                                    uploaded_file = await Telegram.PYROGRAM_CLIENT.send_video(
                                                                                chat_id=chat_id,
                                                                                file_name=filename,
                                                                                video=files[i],
                                                                                caption=file_caption,
                                                                                supports_streaming=True,
                                                                                duration=duration,
                                                                                thumb=thumbnail,
                                                                                reply_to_message_id=event.message.id,
                                                                                progress=process_status.telegram_update_status,
                                                                                progress_args=("Uploaded", filename, start_time, status, get_data()[process_status.user_id]['tgupload'], Telegram.PYROGRAM_CLIENT))
                            except Exception as e:
                                    await event.reply(f"❗Pyrogram Upload Error: {str(e)}")
                else:
                    if Telegram.TELETHON_USER_CLIENT:
                            try:
                                with open(files[i], "rb") as f:
                                    uploaded_file = await upload_file(
                                        client=Telegram.TELETHON_USER_CLIENT,
                                        file=f,
                                        name=filename,
                                        check_data=process_id,
                                        progress_callback=lambda current,total: process_status.telegram_update_status(current,total, "Uploaded", filename, start_time, status, get_data()[process_status.user_id]['tgupload']))
                                await Telegram.TELETHON_USER_CLIENT.send_file(chat_id, file=uploaded_file, thumb=thumbnail, allow_cache=False, supports_streaming=True, caption=file_caption, reply_to=event.message.id, attributes=(DocumentAttributeVideo(duration, 0, 0),))
                            except Exception as e:
                                if str(e)!="Cancelled":
                                    await event.reply(f"❗Telethon User Error While Uploading File {filename}\n\nError: {str(e)}")
                    else:
                            await event.reply(f"❌File Size Is Greater Than Telegram Upload Limit")
                            LOGGER.info(f"File Size: {file_size}, Name: {filename}")
                if not check_running_process(process_id):
                        await event.reply("🔒Task Cancelled By User")
                        break
            return
        
    async def download_tg_file(process_status, variables, dw_index):
        start_time = time()
        status = f"{Names.STATUS_DOWNLOADING} [{dw_index}]"
        new_event = variables[0]
        try:
            file_name = new_event.message.file.name
            file_location = new_event.message.document
            file_id = new_event.message.id
        except:
            file_name = new_event.file.name
            file_location = new_event.document
            file_id = new_event.id
        create_direc(process_status.dir)
        download_location = f"{process_status.dir}/{file_name}"
        process_status.append_dw_files(file_name)
        if get_data()[process_status.user_id]['tgdownload']=="Telethon":
                try:
                    with open(download_location, "wb") as f:
                            await download_file(
                                client=Telegram.TELETHON_CLIENT, 
                                location=file_location, 
                                out=f,
                                check_data=process_status.process_id,
                                progress_callback=lambda current,total: process_status.telegram_update_status(current,total, "Downloaded", file_name, start_time, status, get_data()[process_status.user_id]['tgdownload']))
                except Exception as e:
                        if str(e)=="Cancelled":
                                await new_event.reply("🔒Task Cancelled By User")
                        else:
                            await new_event.reply(f"❗Telethon Download Error: {str(e)}")
                            LOGGER.info(str(e))
                        return False
        else:
            try:
                    if process_status.event.is_group and Config.AUTH_GROUP_ID:
                            chat_id = Config.AUTH_GROUP_ID
                    else:
                            chat_id = process_status.chat_id
                    await Telegram.PYROGRAM_CLIENT.download_media(
                                                                message=(await Telegram.PYROGRAM_CLIENT.get_messages(chat_id, file_id)),
                                                                file_name=download_location,
                                                                progress=process_status.telegram_update_status,
                                                                progress_args=("Downloaded", file_name, start_time, status, get_data()[process_status.user_id]['tgdownload'], Telegram.PYROGRAM_CLIENT))
                    if not check_running_process(process_status.process_id):
                                    await new_event.reply("🔒Task Cancelled By User")
            except Exception as e:
                    await new_event.reply(f"❗Pyrogram Download Error: {str(e)}\n\nChat: {chat_id}")
                    return False
        process_status.move_dw_file(file_name)
        return True
    
    async def upload_videos(process_status):
        if get_data()[process_status.user_id]['split_video']:
            split_size = await get_split_size(process_status.user_id)
            if split_size:
                send_files = process_status.send_files.copy()
                for output_file in process_status.send_files:
                    if getsize(output_file)>split_size:
                        send_files.remove(output_file)
                        file_name = str(output_file).split('/')[-1]
                        process_status.update_process_message(f"✂Splitting Video\n`{str(file_name)}`\n{process_status.get_task_details()}")
                        splitted_files = await FFMPEG.split_video_file(output_file, split_size, process_status.dir, process_status.event)
                        if splitted_files:
                            send_files += splitted_files
                process_status.replace_send_list(send_files)
                LOGGER.info(str(send_files))
        await Telegram.upload_videos_on_telegram(process_status)