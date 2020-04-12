import os
import json
import logging
import re
import shutil
import sys
import jsonschema
import requests
from git import Repo
from git import Git
from git import InvalidGitRepositoryError
from git import RemoteProgress
from pathlib import Path

logger = logging.getLogger()

def create_files(json, skip_type, file_name):
  if(skip_type in json.keys()):
    for stage in json[skip_type]:
      skip_file = os.path.join('pi-gen',stage,file_name)
      try:
        Path(skip_file).touch()
      except FileExistsError:
        logger.warn("File {} already exists".format(skip_file))
        pass

def remove_files(json, skip_type, file_name):
  try:
    if(skip_type in json.keys()):
      for stage in json[skip_type]:
        skip_file = os.path.join('pi-gen',stage,file_name)
        if os.path.exists(skip_file):
          os.remove(skip_file)
  except Exception as e:
    logger.warn(e)
    pass

def hide_files(json, skip_type, file_name):
  try:
    if(skip_type in json.keys()):
      for stage in json[skip_type]:
        hide_file = os.path.join('pi-gen',stage,file_name)
        rename_file = os.path.join('pi-gen',stage,'.{}'.format(file_name))
        if os.path.exists(hide_file):
          os.rename(hide_file, rename_file)
  except Exception as e:
    logger.warn(e)
    pass

def unhide_files(json, skip_type, file_name):
  try:
    if(skip_type in json.keys()):
      for stage in json[skip_type]:
        hide_file = os.path.join('pi-gen',stage,file_name)
        rename_file = os.path.join('pi-gen',stage,'.{}'.format(file_name))
        if os.path.exists(rename_file):
          os.rename(rename_file, hide_file)
  except Exception as e:
    logger.warn(e)
    pass

def recipe_exists(parser, arg):
  fname = arg.split("/")[-1]
  file_path = os.path.join("recipes", fname)
  if not arg.startswith("http://") and not arg.startswith("https://"):
    file_path = arg
  else:
    try:
      if arg.startswith("http://"):
        r = requests.get(arg)
        with open(file_path, 'w') as fp:
          fp.write(r.text)
      if arg.startswith("https://"):
        r = requests.get(arg, verify=True)
        with open(file_path, 'w') as fp:
          fp.write(r.text)
    except Exception as e:
      logger.error("Error while getting recipe {}".format(e))
      logger.info("Checking if local verion exists")
      if not os.path.exists(file_path):
        logger.error("Recipe does not exist locally.")
        sys.exit()
      else:
        logger.info("Local version of {} exists".format(fname))
  if os.path.exists(file_path):
    with open(file_path) as json_file:
      json_data = json.load(json_file)
    return json_data
  else:
    logger.error("The file {} does not exist!".format(file_path))
    sys.exit()

def validate_fillings(dir_path):
  file_type_list = ('run.sh','run-chroot.sh','debconf', 'packages', 'packages-nr','patches')
  dir_listing = os.listdir(dir_path)
  if len(dir_listing) < 1:
    logging.error("{}: No pi-gen files in directory".format(dir_path))
    return False
  for obj in dir_listing:
    if obj in ('files'):
      break
    else:
      for i, file_types in enumerate(file_type_list):
        if obj.endswith(file_types):
          if re.match('^([0-9][0-9])-{}$'.format(file_types), obj):
            break
          else:
            logging.error("{}: {} is not in a recognized pi-gen format".format(dir_path, obj))
            return False
        if i == len(file_type_list):
          logging.error("{}: {} is not in a recognized pi-gen format".format(dir_path, obj))
          return False
  return True

def check_tag(repo, tag):
  try:
    if tag:
      repo.remotes.origin.pull(tag)
      repo.git.checkout(tag)
    else:
      repo.remotes.origin.pull()
  except Exception as e:
    logger.error("Error pulling tag {}".format(e))

def pull_repo(filling_path, url, tag=None, ssh_key=None):
  logger.info("Attempting to pull repo: If hanging check connectivity")
  if not os.path.exists(filling_path):
    os.mkdir(filling_path)
  try: 
    repo = Repo(filling_path)
    if ssh_key:
      git_ssh_cmd = 'ssh -i {}'.format(os.path.abspath(ssh_key))
      os.environ['GIT_SSH_COMMAND'] = git_ssh_cmd
      repo.remotes.origin.pull()
    check_tag(repo, tag)
  except InvalidGitRepositoryError as e:
    logger.info("Directory is not a git repo. Cloning...")
    try:
      if ssh_key:
        git_ssh_cmd = 'ssh -i {}'.format(os.path.abspath(ssh_key))
        repo = Repo.clone_from(url=url, to_path=filling_path, env={'GIT_SSH_COMMAND': git_ssh_cmd})
      else:
        repo = Repo.clone_from(url=url, to_path=filling_path) 
      check_tag(repo, tag)
    except Exception as e:
      logger.warning("Failed to pull repo {}".format(e))
      logger.warning("Checking local copy of filling. Filling might not be latest version.")
  except Exception as e:
    logger.warning("Failed to pull repo: {}".format(e))
    logger.warning("Checking local copy of filling. Filling might not be latest version.")

def validate_bakeshop_json(json):

  recipe_schema = {
      "type": "object",
      "properties": {
        "IMG_NAME":{"type": "string"},
        "APT_PROXY":{"type": "string"},
        "BASE_DIR":{"type": "string"},
        "WORK_DIR":{"type": "string"},
        "DEPLOY_DIR":{"type": "string"},
        "DEPLOY_ZIP":{"type": "number"},
        "USE_QUEMU":{"type": "string"},
        "LOCALE_DEFAULT":{"type": "string"},
        "HOSTNAME":{"type": "string"},
        "KEYBOARD_KEYMAP":{"type": "string"},
        "KEYBOARD_LAYOUT":{"type": "string"},
        "TIMEZONE_DEFAULT":{"type": "string"},
        "FIRST_USER_NAME":{"type": "string"},
        "FIRST_USER_PASS":{"type": "string"},
        "WPA_ESSID":{"type": "string"},
        "WPA_PASSWORD":{"type": "string"},
        "WPA_COUNTRY":{"type": "string"},
        "ENABLE_SSH":{"type": "number"},
        "STAGE_LIST":{"type": "string"},
        "skip_image":{"type": "array"},
        "skip_stage":{"type": "array"},
        "skip_noobs":{"type": "array"},
        "output_dir":{"type": "string"},
        "offline_mode":{"type": "number"},
        "fillings": {"type": "array"}
      },
      "required": ["IMG_NAME", "fillings"]
  }

  filling_schema = {
    "type": "object",
      "properties": {
        "name": {"type": "string"},
        "git_url": {"type": "string"},
        "git_tag": {"type": "string"},
        "ssh_key": {"type": "string"},
        "run_priority": {"type": "number"},
      },
      "required": ["name", "run_priority"]
  }

  try:
    jsonschema.validate(json, recipe_schema)
    for entry in json['fillings']:
      jsonschema.validate(entry, filling_schema)
    logger.info("Recipie JSON is valid")
    return(json)
  except jsonschema.exceptions.ValidationError as e:
    logger.error("Schema ValidationError {}".format(e.message))
    raise e 

