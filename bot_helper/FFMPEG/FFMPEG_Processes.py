from bot_helper.Database.User_Data import get_data
from json import loads
from bot_helper.Others.Helper_Functions import execute, get_video_duration, get_readable_time, delete_trash
from config.config import Config
from asyncio import create_subprocess_exec, sleep
from asyncio.subprocess import PIPE as asyncioPIPE
from os.path import isdir, exists, getsize, splitext, join
from os import makedirs, remove
from telethon.tl.types import DocumentAttributeVideo
from time import time
from math import ceil


def create_direc(direc):
    if not isdir(direc):
        makedirs(direc)
    return

def get_output_name(process_status):
    if process_status.file_name:
        return process_status.file_name
    else:
        return process_status.send_files[-1].split("/")[-1]


LOGGER = Config.LOGGER


###############------Run_Command------###############
async def run_process_command(command):
    print(command)
    try:
        process = await create_subprocess_exec(
            *command,
            stdout=asyncioPIPE,
            stderr=asyncioPIPE,
            )
        while True:
                    try:
                            async for line in process.stderr:
                                        line = line.decode('utf-8').strip()
                                        print(line)
                    except ValueError:
                            continue
                    else:
                            break
        await process.wait()
        return_code = process.returncode
        if return_code == 0:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


###############------Get_Sample_Video_Cut_Duration------###############
async def get_cut_duration(duration):
    if duration<60:
                return [1, duration-2]
    else:
        vmid = round(duration/2)-2
        vend = vmid+60
        if vend>duration:
            vend = duration-2
        return [vmid, vend]


###############------Get_ScreenShot_List------###############
async def gen_ss_list(duration, ss_no):
    value = round(duration/ss_no)
    ss_list = [5]
    ss = 5
    while True:
        ss = ss+value
        if len(ss_list)==ss_no:
            break
        if ss<duration:
            ss_list.append(ss)
        else:
            ss_list.append(duration-2)
            break
    return ss_list

###############------Generate_ScreenShot------###############
async def generate_screenshoot(ss_time, input_video, ss_name):
    command = [
        "ffmpeg",
        "-ss",
        str(ss_time),
        "-i",
        input_video,
        "-frames:v",
        "1",
        "-f",
        "image2",
        "-map",
        "0:v:0",
        "-y",
        ss_name
    ]
    return await run_process_command(command)


class FFMPEG:

###############------Split_Video------###############
    async def split_video_file(file, split_size, dirpath, event):
        success = []
        split_size = split_size-50000000
        try:
            size = getsize(file)
            parts = ceil(size/split_size)
            i=1
            start_time = 0
            while i <= parts:
                    file_name, extension = splitext(file)
                    parted_name = f"{str(file_name)}.part{str(i).zfill(3)}{str(extension)}"
                    create_direc(f"{dirpath}/split/")
                    out_path = join(f"{dirpath}/split/", parted_name)
                    command = ["ffmpeg", "-hide_banner", "-ss", str(start_time),
                                "-i", f"{str(file)}", "-fs", str(split_size), "-map", "0", "-map_chapters", "-1",
                                "-c", "copy", f"{out_path}"]
                    result = await run_process_command(command)
                    if not result:
                            await delete_trash(out_path)
                            command = ["ffmpeg", "-hide_banner", "-ss", str(start_time),
                                "-i", f"{str(file)}", "-fs", str(split_size), "-map_chapters", "-1",
                                "-c", "copy", out_path]
                            result = await run_process_command(command)
                            if not result:
                                    await event.reply(f"❗Could Not Split {str(file)}")
                                    return False
                    cut_duration = get_video_duration(out_path)
                    if cut_duration <= 4:
                            break
                    success.append(out_path)
                    start_time += cut_duration - 3
                    i = i + 1
            return success
        except Exception as e:
            await event.reply(f"❗Error While Splitting {str(file)}\n\n{str(e)}")
            LOGGER.info(str(e))
            return False

###############------Send_ScreenShots------###############
    async def generate_ss(process_status, force_gen=False):
                if get_data()[process_status.user_id]['gen_ss'] or force_gen:
                        if not force_gen:
                                ss_n0 = get_data()[process_status.user_id]['ss_no']
                        else:
                                ss_n0 = 9
                        file_name = get_output_name(process_status)
                        process_status.update_process_message(f"📷Generating Screenshots\n`{str(file_name)}`\n{process_status.get_task_details()}")
                        input_video = f'{str(process_status.send_files[-1])}'
                        duration = get_video_duration(input_video)
                        ss_list = await gen_ss_list(duration, ss_n0)
                        sn0 = 1
                        for ss_time in ss_list:
                                ss_name = f"{process_status.dir}/screenshot_{str(time())}.jpg"
                                ssresult = await generate_screenshoot(ss_time, input_video, ss_name)
                                if ssresult and exists(ss_name):
                                        sscaption = f"📌 Position: {str(get_readable_time(ss_time))}\n📷 Screenshot: {str(sn0)}/{str(ss_n0)}"
                                        try:
                                                await process_status.event.client.send_file(process_status.chat_id, file=ss_name, allow_cache=False, reply_to=process_status.event.message, caption=sscaption)
                                        except Exception as e:
                                                LOGGER.info(str(e))
                                        remove(ss_name)
                                        sn0+=1
                                        await sleep(1)
                return

###############------Send_Sample_Video------###############
    async def gen_sample_video(process_status, force_gen=False):
        if get_data()[process_status.user_id]['gen_sample'] or force_gen:
                input_video = f'{str(process_status.send_files[-1])}'
                duration = get_video_duration(input_video)
                if duration>60:
                        file_name = get_output_name(process_status)
                        process_status.update_process_message(f"🎞Generating Sample Video\n`{str(file_name)}`\n{process_status.get_task_details()}")
                        sample_name = f"{process_status.dir}/sample_{file_name}"
                        vstart_time, vend_time = await get_cut_duration(duration)
                        if duration<180:
                                vframes = '750'
                        else:
                                vframes = '1500'
                        # cmd_sample = ["ffmpeg", "-ss", str(vstart_time), "-to",  str(vend_time), "-i", f"{input_video}","-c", "copy", '-y', f"{sample_name}"]
                        cmd_sample= ['ffmpeg', '-ss', f'{vstart_time}s', '-i', f"{input_video}", '-vframes', f'{vframes}', '-vsync', '1', '-async', '-1', '-acodec', 'copy', '-vcodec', 'copy', '-y', f"{sample_name}"]
                        sample_result = await run_process_command(cmd_sample)
                        if sample_result and exists(sample_name):
                                try:
                                        await process_status.event.client.send_file(process_status.chat_id, file=sample_name, allow_cache=False, reply_to=process_status.event.message, caption=f"🎞 Sample Video", thumb="sthumb.jpg", supports_streaming=True, attributes=(DocumentAttributeVideo(get_video_duration(sample_name), 0, 0),))
                                except Exception as e:
                                        LOGGER.info(str(e))
                                remove(sample_name)
                        else:
                                await process_status.event.reply(f'❌Failed To Generate Sample Video')
                else:
                        if force_gen:
                                await process_status.event.reply(f'❌Video Duration Must Be Greater Than 60 secs To Generate Sample')
        return
    ###############------Change_Metadata------###############
    async def change_metadata(process_status):
        if get_data()[process_status.user_id]['custom_metadata']:
                dl_loc = f'{str(process_status.send_files[-1])}'
                direc = f"{process_status.dir}/metadata/"
                create_direc(direc)
                output_meta = f"{direc}/{get_output_name(process_status)}"
                custom_metadata_title = get_data()[process_status.user_id]['metadata']
                process_status.update_process_message(f"🪀Changing MetaData\n{process_status.get_task_details()}")
                cmd_meta = ["ffmpeg", "-i", f"{dl_loc}", f"-metadata:s:a", f"title={custom_metadata_title}", f"-metadata:s:s", f"title={custom_metadata_title}", "-map", "0", "-c", "copy", '-y', f"{output_meta}"]
                met_result = await run_process_command(cmd_meta)
                if not met_result:
                        cmd_meta = ["ffmpeg", "-i", f"{dl_loc}", f"-metadata:s:a", f"title={custom_metadata_title}", "-map", "0", "-c", "copy", '-y', f"{output_meta}"]
                        met_result = await run_process_command(cmd_meta)
                if not met_result:
                        cmd_meta = ["ffmpeg", "-i", f"{dl_loc}", f"-metadata:s:s", f"title={custom_metadata_title}", "-map", "0", "-c", "copy", '-y', f"{output_meta}"]
                        met_result = await run_process_command(cmd_meta)
                if met_result:
                        await process_status.event.reply(f"✅Metadata Set Successfully")
                        caption = f"✅Metadata: {custom_metadata_title}\n" + caption if process_status.caption else ''
                        process_status.set_caption(caption)
                        process_status.append_send_files_loc(output_meta)
                        return
                else:
                        await process_status.event.reply(f"❗Failed To Set MetaData")
                        return
        else:
            return
    
    
    ###############------Select_Audio------###############
    async def select_audio(process_status):
                                        if get_data()[process_status.user_id]['select_stream']:
                                                language = get_data()[process_status.user_id]['stream']
                                                try:
                                                        get_streams = await execute(f"ffprobe -hide_banner -show_streams -print_format json '{str(process_status.send_files[-1])}'")
                                                        details = loads(get_streams)
                                                        print(details)
                                                        stream_data = {}
                                                        smsg = ''
                                                        for stream in details["streams"]:
                                                                # stream_name = stream["codec_name"]
                                                                stream_type = stream["codec_type"]
                                                                codec_long_name = stream['codec_long_name']
                                                                if stream_type in ("audio"):
                                                                        mapping = stream["index"]
                                                                        try:
                                                                                lang = stream["tags"]["language"]
                                                                        except:
                                                                                lang = mapping
                                                                        sname = f"{stream_type.upper()} - {str(lang).upper()} [{codec_long_name}]"
                                                                        stream_data[sname] = {}
                                                                        stream_data[sname]['index'] =mapping
                                                                        stream_data[sname]['language'] = str(lang).upper()
                                                                        smsg+= f'`{sname}`\n\n'
                                                        if len(stream_data)==0:
                                                                await process_status.event.reply("❗Failed To Find Audio Streams From Video")
                                                                return
                                                        elif len(stream_data)==1:
                                                                await process_status.event.reply("🔶Only One Audio Found In The Video So Skipping Audio Selection.")
                                                                return
                                                        else:
                                                                skeys = list(stream_data.keys())
                                                                for k in skeys:
                                                                        if stream_data[k]['language']==language:
                                                                                cstream = k
                                                                                stream_no = stream_data[cstream]['index']
                                                                                amap_options = f'0:a:{str(int(stream_no)-1)}'
                                                                                process_status.set_amap_options(amap_options)
                                                                                await process_status.event.reply(f'✅Audio Selected Successfully\n\n`{str(cstream)}`\n\n`STREAM NO: {str(stream_no)}`')
                                                                                caption = f"✅Audio: {str(cstream)}\n" + caption if process_status.caption else ''
                                                                                process_status.set_caption(caption)
                                                                                return
                                                                await process_status.event.reply(f'❗{language} Language Not Found In Video.')
                                                                return
                                                except Exception as e:
                                                        LOGGER.info(str(e))
                                                        await process_status.event.reply(f"❌Failed To Get Audio Streams From Video\n\n{str(e)}")
                                                        return
                                        else:
                                            return