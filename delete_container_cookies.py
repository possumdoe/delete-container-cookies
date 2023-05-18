#!/usr/bin/env python3

import logging
import argparse

from cookies import delete_cookies

parser = argparse.ArgumentParser(
    description="Firefox container's cookie deleter")

parser.add_argument("-b", "--browser", type=str, required=True)
parser.add_argument("-c", "--container", type=str)

if __name__ == "__main__":
    args = parser.parse_args()

    browser_specification = [args.browser, None, None, args.container]

    logging.getLogger().setLevel(logging.INFO)
    deleted_cookie_count = delete_cookies(browser_specification, logging.getLogger())
    print(f"Succesfully deleted {deleted_cookie_count} cookies.")
