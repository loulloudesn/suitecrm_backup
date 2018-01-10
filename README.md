# Description
A simple Python script that automates backing up a [SuiteCRM](https://suitecrm.com/) installation to a remote Google Drive

It assumes the existence of [Rclone](https://rclone.org/) tool

This script can be automated to run on specified intervals using a `crontab`

Failures are reported by sending an email to a configured account via Gmail SMTP

## Example
Execute `crontab -e` and add the following at the end

```bash
0 1 * * * /root/backup_scripts/backup_suitecrm.py > /var/log/backup.log
```


