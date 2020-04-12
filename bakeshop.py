#!/usr/bin/python3
import logging
import argparse
import sys
import os
from colorlog import ColoredFormatter

import core.baker as baker
import core.utils as utils

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
LOGFORMAT = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s"
formatter = ColoredFormatter(LOGFORMAT)
handler.setFormatter(formatter)
logger.addHandler(handler)

def main():
  if not os.geteuid() == 0:
    logger.error("Only root can run this script")
    sys.exit(1)

  shared_parser = argparse.ArgumentParser(add_help=False)
  shared_parser.add_argument('-r','--recipe', required=True, help='Path to json recipe config.', type=lambda x: utils.recipe_exists(parser, x))
  parser = argparse.ArgumentParser(parents=[shared_parser])
  subparsers = parser.add_subparsers(help='commands', dest="command")
  clean_group = subparsers.add_parser('clean', help='Cleans work dir for supplied recipe')
  args=parser.parse_args()

  logger.info("Starting Bakeshop")
  json = utils.validate_bakeshop_json(args.recipe)
  
  b = baker.Baker(json)
  if(args.command == 'clean'):
    b.clean()

  else:
    b.prep()
    b.preheat()
    b.bake()
    b.package()

if __name__ == "__main__":
    main()

