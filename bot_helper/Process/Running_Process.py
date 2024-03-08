from asyncio import Lock

running_process = []
running_process_lock = Lock()

def check_running_process(process_id):
        if process_id in running_process:
            return True
        else:
            return False


async def append_running_process(process_id):
    async with running_process_lock:
        if process_id not in running_process:
            running_process.append(process_id)
            return True
        else:
            return False


async def remove_running_process(process_id):
    async with running_process_lock:
        if process_id in running_process:
            running_process.remove(process_id)
            return True
        else:
            return False