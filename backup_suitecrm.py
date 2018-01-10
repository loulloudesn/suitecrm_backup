#!/usr/bin/env python3

import subprocess
import smtplib
import tarfile
import string
import time
import sys
import os


DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASS = ''
DB_NAME = 'suitecrm_db'
CRM_INSTALL_DIR = '/var/www/html/suitecrm/'
GD_REMOTE = 'remote:Backups/suitecrm'
ARCHIVE_PREFIX = 'op_suitecrm'

exit_code = 0
error_msg = ''

MAIL_USER = '<EMAIL_ACCOUNT_USERNAME>'
MAIL_PWD = '<EMAIL_ACCOUNT_PASSWORD>'
MAIL_FROM = 'SuiteCRM Backup Service'
MAIL_TO = '<RECIPIENT_EMAIL>'
MAIL_SUBJECT = 'SuiteCRM Backup Failed'


def assert_tools():
    global exit_code
    # Check pre-requisites

    # Assert that Rclone is installed
    exists = is_tool('rclone')
    if not exists:
        error_msg = 'Rclone is not installed'
        print(error_msg)
        send_email(MAIL_SUBJECT, error_msg)
        exit_code = 1
        return exit_code


def backup():
    global exit_code

    timestamp = time.strftime('%Y%m%d%I%M')

    # Compress files to a single archive
    tmp_archive = '/tmp/' + ARCHIVE_PREFIX + '-' + timestamp + '.tar.gz'

    print('Archiving all backup files to', tmp_archive)
    tar = tarfile.open(tmp_archive, "w:gz")
    tar.add(CRM_INSTALL_DIR)

    db_dumpfile = '/tmp/database_' + timestamp + '.gz'	
    # Dump MySQL database
    print ('Getting database (mysql) dump')
    p = subprocess.Popen("mysqldump -u %s -h %s -e --opt -c %s | gzip -c > %s" % (DB_USER,DB_HOST,DB_NAME,db_dumpfile), shell=True)
    p.communicate() 

    exit_code = p.returncode

    if (exit_code == 0):
        print ('Database dump copleted')
        tar.add(db_dumpfile)
    else:
        error_msg = 'Could not get database (mysql) dump'
        print (error_msg)
        send_email(MAIL_SUBJECT, error_msg)

    tar.close()
	
    exit_code = upload_to_gdrive(tmp_archive)
    if (exit_code != 0):
        send_email(MAIL_SUBJECT, error_msg)

    # Last steo - if no error was caught, then do cleanup
    if (exit_code == 0):
        # Do cleanup here
        print('Cleaning Up temporary archive')
        os.remove(tmp_archive)


    return exit_code


def upload_to_gdrive(archive):
    global exit_code
    global error_msg
    print('Copying ' + archive + ' to remote ' + GD_REMOTE)
    returncode = subprocess.call(
        'rclone mkdir remote:' + GD_REMOTE, shell=True)

    if (returncode != 0):
        error_msg = 'Could not create remote Google Drive directory'
        print(error_msg)
        return returncode

    returncode = subprocess.call(
        'rclone copy ' + archive + ' ' + GD_REMOTE, shell=True)

    if (returncode != 0):
        error_msg = 'Could not copy archive to remote Google Drive directory'
        print(error_msg)
        return returncode

    return returncode


def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""

    # from whichcraft import which
    from shutil import which

    return which(name) is not None


def send_email(subject, body):
    TO = MAIL_TO if type(MAIL_TO) is list else [MAIL_TO]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (MAIL_FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(MAIL_USER, MAIL_PWD)
        server.sendmail(MAIL_FROM, TO, message)
        server.close()
        print('successfully sent the mail')
    except:
        print('failed to send mail')


if __name__ == "__main__":
    assert_tools()

    if (exit_code != 1):
        backup()

    sys.exit(exit_code)
