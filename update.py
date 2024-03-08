from logging import StreamHandler, INFO, basicConfig, error as log_error, info as log_info
from logging.handlers import RotatingFileHandler
from os import environ
from os.path import exists
from subprocess import run as srun, call as scall
from requests import get
from dotenv import load_dotenv, dotenv_values


def dw_file_from_url(url, filename):
        r = get(url, allow_redirects=True, stream=True)
        with open(filename, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=1024 * 10):
                        if chunk:
                                fd.write(chunk)
        return

if exists("Logging.txt"):
    with open("Logging.txt", "r+") as f_d:
        f_d.truncate(0)

basicConfig(
    level=INFO,
    format="%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler(
            "Logging.txt", maxBytes=50000000, backupCount=10, encoding="utf-8"
        ),
        StreamHandler(),
    ],
)

if not exists('./userdata/botconfig.env'):
    CONFIG_FILE_URL = environ.get("CONFIG_FILE_URL", False)
    if CONFIG_FILE_URL and str(CONFIG_FILE_URL).startswith("http"):
        log_info(f"⏺Updater: Downloading Config File From URL {CONFIG_FILE_URL}")
        dw_file_from_url(CONFIG_FILE_URL, "config.env")
    if exists('config.env'):
        log_info(f"⏺Updater: Importing Config File")
        load_dotenv('config.env')
else:
    log_info(f"⏺Updater: Importing Bot Config File")
    env_dict = dict(dotenv_values("./userdata/botconfig.env"))
    for key in env_dict:
        environ[key] = str(env_dict[key])


UPDATE_PACKAGES = environ.get('UPDATE_PACKAGES', 'False')
if UPDATE_PACKAGES.lower() == 'true':
    log_info(f"⏺Updater: Updating Packages")
    scall("pip install -r requirements.txt", shell=True)

UPSTREAM_REPO = environ.get('UPSTREAM_REPO', '')
if len(UPSTREAM_REPO) == 0:
   UPSTREAM_REPO = None

UPSTREAM_BRANCH = environ.get('UPSTREAM_BRANCH', '')
if len(UPSTREAM_BRANCH) == 0:
    UPSTREAM_BRANCH = 'master'

if UPSTREAM_REPO is not None:
    if exists('.git'):
        srun(["rm", "-rf", ".git"])
        log_info(f"⏺Updater: Clearing .git")
        
    log_info(f"⏺Updater: Updating From Github")
    update = srun([f"git init -q \
                     && git config --global user.email nik66x@gmail.com \
                     && git config --global user.name nik66 \
                     && git add . \
                     && git commit -sm update -q \
                     && git remote add origin {UPSTREAM_REPO} \
                     && git fetch origin -q \
                     && git reset --hard origin/{UPSTREAM_BRANCH} -q"], shell=True)

    UPSTREAM_REPO_URL = (UPSTREAM_REPO[:8] if UPSTREAM_REPO[:8] and UPSTREAM_REPO[:8].endswith('/') else UPSTREAM_REPO[:7]) + UPSTREAM_REPO.split('@')[1] if '@github.com' in UPSTREAM_REPO else UPSTREAM_REPO    
    if update.returncode == 0:
        log_info(f'✅Successfully updated with latest commit from {UPSTREAM_REPO_URL}')
    else:
        log_error(f'❗Something went wrong while updating, check {UPSTREAM_REPO_URL} if valid or not!')