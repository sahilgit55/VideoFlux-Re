from os.path import getsize
from bot_helper.Others.Names import Names
from bot_helper.Process.Running_Process import check_running_process
from aiofiles import open as aio_open
from config.config import Config
from asyncio import sleep as asynciosleep


LOGGER = Config.LOGGER


class FfmpegStatus:
    def __init__(self, process, log_file, input_file, output_file, duration):
        self.process = process
        self.name = input_file.split("/")[-1]
        self.log_file = log_file
        self.input_file = input_file
        self.input_file_size = getsize(input_file)
        self.output_file = output_file
        self.duration = duration
        self.process_logs = []
        self.returncode = False
    
    def input_size(self):
        return self.input_file_size
    
    def save_log(self, line):
        self.process_logs.append(line)
        return
    
    def output_size(self):
        try:
            return getsize(self.output_file)
        except:
            return 0
    
    def type(self):
        return Names.ffmpeg
    
    
    async def logger(self, process_id, process_dir, command):
        LOGGER.info(f'Starting FFMPEG Log Saver: {process_id}')
        async with aio_open(f"{process_dir}/FFMPEG_LOG.txt", "a+", encoding="utf-8") as f:
                    await f.write(f'{str(command)}\n')
        while True:
                try:
                    async for line in self.process.stderr:
                            if not check_running_process(process_id):
                                    break
                            line = line.decode('utf-8').strip()
                            print(line)
                            async with aio_open(f"{process_dir}/FFMPEG_LOG.txt", "a+", encoding="utf-8") as f:
                                        await f.write(f'{str(line)}\n')
                except ValueError:
                        continue
                else:
                        break
                
        LOGGER.info(f'FFMPEG Log Saver Completed : {process_id}')
        if check_running_process(process_id):
            await self.process.wait()
            self.returncode = self.process.returncode
            LOGGER.info(f'FFMPEG Return Code : {self.returncode}')
        return