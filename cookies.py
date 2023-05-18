import json
import os
import re
import shutil
import sqlite3
import sys

SUPPORTED_BROWSERS = [
    "firefox"
]


def delete_cookies(browser_specification, logger):
    """
    Delete cookies
    `browser_specification`: list of 4 elements [browser, profile, keyring, container]

    If `profile` is None, the last used profile will be used
    If `container` is "none", will be deleted only cookies that are not part of any container

    Example:
    This code will delete all the cookies from the container personal in Firefox last used profile
    ```
    delete_cookies(["firefox", None, None, "personal"])
    ```
    """
    if browser_specification is not None:
        browser_name, profile, keyring, container = _parse_browser_specification(
            *browser_specification)
        return delete_firefox_cookies(browser_name, profile, logger,
                                    keyring=keyring, container=container)


def delete_firefox_cookies(browser_name, profile=None, logger=None, *, keyring=None, container=None):
    """Delete Firefox cookies"""
    logger.info('Extracting cookies from firefox')
    if not sqlite3:
        logger.warning('Cannot extract cookies from firefox without sqlite3 support. '
                       'Please use a python interpreter compiled with sqlite3 support')
        return False

    if profile is None:
        search_root = _firefox_browser_dir()
    elif _is_path(profile):
        search_root = profile
    else:
        search_root = os.path.join(_firefox_browser_dir(), profile)

    cookie_database_path = _find_most_recently_used_file(
        search_root, 'cookies.sqlite', logger)
    if cookie_database_path is None:
        raise FileNotFoundError(
            f'could not find firefox cookies database in {search_root}')
    logger.debug(f'Extracting cookies from: "{cookie_database_path}"')

    container_id = None
    if container not in (None, 'none'):
        containers_path = os.path.join(os.path.dirname(
            cookie_database_path), 'containers.json')
        if not os.path.isfile(containers_path) or not os.access(containers_path, os.R_OK):
            raise FileNotFoundError(
                f'could not read containers.json in {search_root}')
        with open(containers_path) as containers:
            identities = json.load(containers).get('identities', [])
        container_id = next((context.get('userContextId') for context in identities if container in (
            context.get('name'),
            _try_call(lambda: re.fullmatch(
                r'userContext([^\.]+)\.label', context['l10nID']).group())
        )), None)
        if not isinstance(container_id, int):
            raise ValueError(
                f'could not find firefox container "{container}" in containers.json')

    cursor = None
    try:
        # cursor = _open_database_copy(cookie_database_path, tmpdir)
        cursor = _open_database(cookie_database_path)
        if isinstance(container_id, int):
            logger.debug(
                f'Only deleting cookies from firefox container "{container}", ID {container_id}')
            cursor.execute(
                'DELETE FROM moz_cookies WHERE originAttributes LIKE ? OR originAttributes LIKE ?',
                (f'%userContextId={container_id}', f'%userContextId={container_id}&%'))
        elif container == 'none':
            logger.debug(
                'Only deleting cookies not belonging to any container')
            cursor.execute(
                'DELETE FROM moz_cookies WHERE NOT INSTR(originAttributes,"userContextId=")')
        else:
            cursor.execute(
                'DELETE FROM moz_cookies')
        cursor.connection.commit()
        deleted_cookie_count = cursor.connection.total_changes
        logger.info(f'Deleted {deleted_cookie_count} cookies from firefox')
        return deleted_cookie_count
    finally:
        if cursor is not None:
            cursor.connection.close()


def _firefox_browser_dir():
    if sys.platform in ('cygwin', 'win32'):
        return os.path.expandvars(R'%APPDATA%\Mozilla\Firefox\Profiles')
    elif sys.platform == 'darwin':
        return os.path.expanduser('~/Library/Application Support/Firefox')
    return os.path.expanduser('~/.mozilla/firefox')


def _open_database(database_path):
    # cannot open sqlite databases if they are already in use (e.g. by the browser)
    conn = sqlite3.connect(database_path)
    return conn.cursor()


def _find_most_recently_used_file(root, filename, logger):
    # if there are multiple browser profiles, take the most recently used one
    i, paths = 0, []
    for curr_root, dirs, files in os.walk(root):
        for file in files:
            i += 1
            logger.info(
                f'Searching for "{filename}": {i: 6d} files searched\r')
            if file == filename:
                paths.append(os.path.join(curr_root, file))
    return None if not paths else max(paths, key=lambda path: os.lstat(path).st_mtime)


def _is_path(value):
    return os.path.sep in value


def _parse_browser_specification(browser_name, profile=None, keyring=None, container=None):
    if browser_name not in SUPPORTED_BROWSERS:
        raise ValueError(f'unsupported browser: "{browser_name}"')
    if profile is not None and _is_path(_expand_path(profile)):
        profile = _expand_path(profile)
    return browser_name, profile, keyring, container


def _expand_path(s):
    """Expand shell variables and ~"""
    return os.path.expandvars(os.path.expanduser(s))


def _try_call(*funcs, expected_type=None, args=[], kwargs={}):
    for f in funcs:
        try:
            val = f(*args, **kwargs)
        except (AttributeError, KeyError, TypeError, IndexError, ValueError, ZeroDivisionError):
            pass
        else:
            if expected_type is None or isinstance(val, expected_type):
                return val
