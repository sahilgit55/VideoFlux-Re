from bot_helper.Database.DB_Handler import Database
from config.config import Config

#////////////////////////////////////Variables////////////////////////////////////#
if Config.SAVE_TO_DATABASE:
    db = Database()
    save_id = Config.SAVE_ID
DATA = Config.DATA
LOGGER = Config.LOGGER
TASK_LIMIT = Config.RUNNING_TASK_LIMIT


#////////////////////////////////////Task_Limit////////////////////////////////////#

###############------Return_Task_Limit------###############
def get_task_limit():
    return TASK_LIMIT

def change_task_limit(new_limit):
    global TASK_LIMIT
    TASK_LIMIT = new_limit
    return


#////////////////////////////////////Database////////////////////////////////////#

###############------Return_Database------###############
def get_data():
    return DATA

###############------New_User------###############
async def new_user(user_id, dbsave):
        DATA[user_id] = {}
        DATA[user_id]['watermark'] = {}
        DATA[user_id]['watermark']['position'] = '5:5'
        DATA[user_id]['watermark']['size'] = '15'
        DATA[user_id]['watermark']['crf'] = '23'
        DATA[user_id]['watermark']['use_queue_size'] = False
        DATA[user_id]['watermark']['queue_size'] = '9999'
        DATA[user_id]['watermark']['use_crf'] = False
        DATA[user_id]['watermark']['encode'] = True
        DATA[user_id]['watermark']['encoder'] = 'libx265'
        DATA[user_id]['watermark']['preset'] = 'ultrafast'
        DATA[user_id]['watermark']['map_audio'] = True
        DATA[user_id]['watermark']['copy_sub'] = True
        DATA[user_id]['watermark']['map'] = True
        DATA[user_id]['watermark']['sync'] = False
        DATA[user_id]['softmux'] = {}
        DATA[user_id]['softmux']['preset'] = 'ultrafast'
        DATA[user_id]['softmux']['use_crf'] = False
        DATA[user_id]['softmux']['crf'] = '23'
        DATA[user_id]['softmux']['sub_codec'] = 'copy'
        DATA[user_id]['softmux']['map_audio'] = False
        DATA[user_id]['softmux']['map_sub'] = False
        DATA[user_id]['softmux']['map'] = False
        DATA[user_id]['softmux']['encode'] = False
        DATA[user_id]['softmux']['encoder'] = 'libx265'
        DATA[user_id]['softremux'] = {}
        DATA[user_id]['softremux']['preset'] = 'ultrafast'
        DATA[user_id]['softremux']['use_crf'] = False
        DATA[user_id]['softremux']['crf'] = '23'
        DATA[user_id]['softremux']['sub_codec'] = 'copy'
        DATA[user_id]['softremux']['map_audio'] = False
        DATA[user_id]['softremux']['map_sub'] = False
        DATA[user_id]['softremux']['map'] = False
        DATA[user_id]['softremux']['encode'] = False
        DATA[user_id]['softremux']['encoder'] = 'libx265'
        DATA[user_id]['hardmux'] = {}
        DATA[user_id]['hardmux']['preset'] = 'ultrafast'
        DATA[user_id]['hardmux']['crf'] = '23'
        DATA[user_id]['hardmux']['encode_video'] = True
        DATA[user_id]['hardmux']['encoder'] = 'libx265'
        DATA[user_id]['hardmux']['use_queue_size'] = False
        DATA[user_id]['hardmux']['queue_size'] = '9999'
        DATA[user_id]['hardmux']['sync'] = False
        DATA[user_id]['compress'] = {}
        DATA[user_id]['compress']['preset'] = 'ultrafast'
        DATA[user_id]['compress']['crf'] = '23'
        DATA[user_id]['compress']['use_queue_size'] = False
        DATA[user_id]['compress']['sync'] = False
        DATA[user_id]['compress']['queue_size'] = '9999'
        DATA[user_id]['compress']['map_audio'] = True
        DATA[user_id]['compress']['map_sub'] = True
        DATA[user_id]['compress']['map'] = True
        DATA[user_id]['compress']['copy_sub'] = False
        DATA[user_id]['compress']['encoder'] = 'libx265'
        DATA[user_id]['compression'] = False
        DATA[user_id]['select_stream'] = False
        DATA[user_id]['stream'] = 'ENG'
        DATA[user_id]['split_video'] = False
        DATA[user_id]['split'] = '2GB'
        DATA[user_id]['upload_tg'] = True
        DATA[user_id]['rclone'] = False
        DATA[user_id]['rclone_config_link'] = False
        DATA[user_id]['drive_name'] = False
        DATA[user_id]['merge'] = {}
        DATA[user_id]['merge']['map_audio'] = True
        DATA[user_id]['merge']['map_sub'] = True
        DATA[user_id]['merge']['map'] = True
        DATA[user_id]['merge']['fix_blank'] = False
        DATA[user_id]['custom_thumbnail'] = False
        DATA[user_id]['convert_video'] = False
        DATA[user_id]['convert_quality'] = [720, 480]
        DATA[user_id]['convert'] = {}
        DATA[user_id]['convert']['preset'] = 'ultrafast'
        DATA[user_id]['convert']['use_crf'] = False
        DATA[user_id]['convert']['crf'] = '23'
        DATA[user_id]['convert']['map'] = True
        DATA[user_id]['convert']['encode'] = True
        DATA[user_id]['convert']['encoder'] = 'libx265'
        DATA[user_id]['convert']['copy_sub'] = False
        DATA[user_id]['convert']['use_queue_size'] = False
        DATA[user_id]['convert']['sync'] = False
        DATA[user_id]['convert']['queue_size'] = '9999'
        DATA[user_id]['convert']['convert_list'] = [720, 480]
        DATA[user_id]['custom_name'] = False
        DATA[user_id]['custom_metadata'] = False
        DATA[user_id]['metadata'] = "Nik66Bots"
        DATA[user_id]['detailed_messages'] = True
        DATA[user_id]['show_stats'] = True
        DATA[user_id]['show_botuptime'] = True
        DATA[user_id]['update_time'] = 7
        DATA[user_id]['ffmpeg_log'] = True
        DATA[user_id]['ffmpeg_size'] = True
        DATA[user_id]['ffmpeg_ptime'] = True
        DATA[user_id]['auto_drive'] = False
        DATA[user_id]['show_time'] = True
        DATA[user_id]['gen_ss'] = False
        DATA[user_id]['ss_no'] = 5
        DATA[user_id]['gen_sample'] = False
        DATA[user_id]['tgdownload'] = "Pyrogram"
        DATA[user_id]['tgupload'] = "Pyrogram"
        DATA[user_id]['multi_tasks'] = False
        DATA[user_id]['upload_all'] = True
        if dbsave:
            data = await db.save_data(str(DATA))
        else:
            data = True
        return data

###############------Save_Config------###############
async def saveoptions(user_id, dname, value, dbsave):
    try:
        if user_id not in DATA:
            DATA[user_id] = {}
            DATA[user_id][dname] = {}
            DATA[user_id][dname] = value
        else:
            DATA[user_id][dname] = value
        if dbsave:
            data = await db.save_data(str(DATA))
        else:
            data = True
        return data
    except Exception as e:
        LOGGER.info(e)
        return False

###############------Reset_Database------###############
async def resetdatabase(dbsave):
    try:
        DATA.clear()
        if dbsave:
            await db.save_data(str(DATA))
        return True
    except Exception as e:
        LOGGER.info(e)
        return False

###############------Save_Sub_Config------###############
async def saveconfig(user_id, dname, pos, value, dbsave):
    try:
        if user_id not in DATA:
            DATA[user_id] = {}
            DATA[user_id][dname] = {}
            DATA[user_id][dname][pos] = value
        else:
            DATA[user_id][dname][pos] = value
        if dbsave:
            data = await db.save_data(str(DATA))
        else:
            data = True
        return data
    except Exception as e:
        LOGGER.info(e)
        return False

###############------Save_Restart_IDs------###############
async def save_restart(chat_id, msg_id):
    try:
        if 'restart' not in DATA:
            DATA['restart'] = []
            DATA['restart'].append([chat_id, msg_id])
        else:
            DATA['restart'].append([chat_id, msg_id])
        await db.save_data(str(DATA))
        return
    except Exception as e:
        LOGGER.info(e)
        return False
    
###############------Clear_Restart_IDs------###############
async def clear_restart():
    try:
        DATA['restart'] = []
        await db.save_data(str(DATA))
        return
    except Exception as e:
        LOGGER.info(e)
        return False