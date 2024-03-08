from bot_helper.Others.Names import Names
from bot_helper.Database.User_Data import get_data
from re import escape
from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE as asyncioPIPE




###############------Upload_To_Drive------###############
async def upload_drive(process_status):
                        total_files = len(process_status.send_files)
                        files = process_status.send_files
                        r_config = f'./userdata/{str(process_status.user_id)}_rclone.conf'
                        q = 1
                        for i in range(total_files):
                                filename = files[i].split("/")[-1]
                                status = f"{Names.STATUS_UPLOADING} [{str(i+1)}/{str(total_files)}]"
                                drive_name = get_data()[process_status.user_id]['drive_name']
                                command =  [ "rclone",
                                                                "copy",
                                                                f"--config={r_config}",
                                                                f'{str(files[i])}',
                                                                f'{drive_name}:/',
                                                                "-f",
                                                                "- *.!qB",
                                                                "--buffer-size=1M",
                                                                "-P",
                                                        ]
                                search_command =  [
                                                "rclone",
                                                "lsjson",
                                                f"--config={r_config}",
                                                f'{drive_name}:/',
                                                "--files-only",
                                                "-f",
                                                f"+ {escape(filename)}",
                                                "-f",
                                                "- *",
                                        ]
                                rclone_process = await create_subprocess_exec(
                                                                                                                *command,
                                                                                                                stdout=asyncioPIPE,
                                                                                                                stderr=asyncioPIPE,
                                                                                                                )
                                try:
                                        upload_result = await process_status.rclone__update_status(rclone_process, filename, search_command, files[i], r_config, drive_name, status)
                                        if not upload_result:
                                                await process_status.event.reply("🔒Task Cancelled By User")
                                                break
                                except Exception as e:
                                        await process_status.event.reply(f"❌Error While Uploading {str(filename)} To Drive\n\n{str(e)}")
                                q+=1
                        return


###############------Upload_Single_File_Drive------###############
async def upload_single_drive(process_status, file, status, r_config, drive_name, filename):
                        command =  [ "rclone",
                                                        "copy",
                                                        f"--config={r_config}",
                                                        f'{str(file)}',
                                                        f'{drive_name}:/',
                                                        "-f",
                                                        "- *.!qB",
                                                        "--buffer-size=1M",
                                                        "-P",
                                                ]
                        search_command =  [
                                        "rclone",
                                        "lsjson",
                                        f"--config={r_config}",
                                        f'{drive_name}:/',
                                        "--files-only",
                                        "-f",
                                        f"+ {escape(filename)}",
                                        "-f",
                                        "- *",
                                ]
                        rclone_process = await create_subprocess_exec(
                                                                                                        *command,
                                                                                                        stdout=asyncioPIPE,
                                                                                                        stderr=asyncioPIPE,
                                                                                                        )
                        try:
                                await process_status.rclone__update_status(rclone_process, filename, search_command, file, r_config, drive_name, status)
                        except Exception as e:
                                await process_status.event.reply(f"❌Error While Uploading {str(filename)} To Drive\n\n{str(e)}")
                        return