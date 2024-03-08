# A Multi-Feature Telegram Bot


### Configuration
To configure this bot add the environment variables stated below. Or add them in [sample_config.env](./sample_config.env) and change the name to `config.env`. Or add the environment variable `CONFIG_FILE_URL` and put config.env direct url in it.
- `API_ID` - (Required)Get it by creating an app on [https://my.telegram.org](https://my.telegram.org)
- `API_HASH` - (Required)Get it by creating an app on [https://my.telegram.org](https://my.telegram.org)
- `TOKEN` - (Required)Get it by creating a bot on [https://t.me/BotFather](https://t.me/BotFather)
- `OWNER_ID` - (Required)Numerical User ID of bot owner
- `SUDO_USERS` - (Required)Numerical User IDs of sudo users separated by space.
- `AUTH_GROUP_ID` - (Optional)Numerical chat id of group, required if you want to use pyrogram download/upload in group.
- `RESTART_NOTIFY_ID` - (Optional)Numerical user id of user or chat id of group/channel to notify on bot start, set it False if you don't want notification on start.
- `AUTO_SET_BOT_CMDS` - (Required)Set True if you want bot to setup its commands by itself otherwise set it False.
- `RUNNING_TASK_LIMIT` - (Required)Number Of Concurrent Tasks.
- `UNFINISHED_PROGRESS_STR` - (Required)Unfinished progress bar string value.
- `FINISHED_PROGRESS_STR` - (Required)Finished progress bar string value.
- `UPDATE_PACKAGES` - (Optional)Set True if you want to update the packages.
- `UPSTREAM_REPO` - (Optional)Your github repository link, if your repo is private add https://username:{githubtoken}@github.com/{username}/{reponame} format.
- `UPSTREAM_BRANCH` - (Optional)Upstream branch for update.
- `TIMEZONE` - (Optional)Timezone for clock time in status. Default is `Asia/Kolkata`.
- `SAVE_TO_DATABASE` - (Required)Set value True if you want to use MongoDB Database else False.
- `MONGODB_URI` - (Optional*)MongoDB URL to save data, only required when SAVE_TO_DATABASE's value is True.
- `Use_Session_String` - (Required)Set value True if you want to use Telegram user session string to upload 4GB file to telegram else False.
- `Session_String` - (Optional*)Telethon Session String, only required when Use_Session_String's value is True.

### Commands
```
compress - Compress Video
merge - Merge Video
watermark - Add Watermark To Video
convert - Convert Video
hardmux - Hardmux Video
softmux - Softmux Video
softremux - Softremux Video
gensample - Generate Sample Video
genss - Generate Screenshots
changemetadata - Change Video Metadata
changeindex - Change Index Or Remove Stream
savewatermark - Save Watermark Image
savethumb - Save Static Thumbnail
saveconfig - Save Rclone Config
tasklimit - Change Task Limit
status - Check Process Status
log - Get Log Message
logs - Get Log File
renew - Renew Storage
resetdb - Reset Database
changeconfig - Change Bot Config
clearconfigs - Restore To Default Config
addsudo - Add Sudo User
delsudo - Delete Sudo User
checksudo - Check Sudo Users
time - Get Bot Uptime
stats - Get Stats
speedtest - SpeedTest
settings - Settings Section
restart - Restart Bot
herokurestart - Restart Heroku Dyno
```



### Copyright & License
- Copyright &copy; 2023 &mdash; [Nik66](https://github.com/sahilgit55)
- Licensed under the terms of the [GNU General Public License Version 3 &dash; 29 June 2007](./LICENSE)