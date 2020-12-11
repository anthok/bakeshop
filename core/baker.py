import json
import logging
import sys
import shutil
import os
import subprocess
import shlex
import datetime
import core.utils as utils
import time
import glob

logger = logging.getLogger()

class Baker(object):
  """docstring for BakeshopConfig"""
  def __init__(self, json_data):
    self.json_data = json_data
    self.img_name = self.json_data['IMG_NAME']
    self.fillings = self.json_data['fillings']
    self.stage_dir = os.path.join('pi-gen','stage-bakeshop')
    self.deploy_path = os.path.join('pi-gen','deploy')
    self.work_path = os.path.join('pi-gen','work')
    if 'output_dir' in self.json_data.keys():
      self.artifacts = self.json_data['output_dir']
    else:
      self.artifacts = "artifacts"

  def prep(self):
    logger.info("Preping recipe")
    stage_2_dir = os.path.join('pi-gen','stage2')
    stage_4_dir = os.path.join('pi-gen','stage4')
    utils.remove_files(self.json_data,'skip_stage','SKIP')
    utils.remove_files(self.json_data,'skip_image','SKIP_IMAGE')
    utils.unhide_files(self.json_data,'skip_image','EXPORT_IMAGE')
    utils.unhide_files(self.json_data, 'skip_noobs','EXPORT_NOOBS')
    if os.path.exists(self.stage_dir):
      shutil.rmtree(self.stage_dir)
    folder_name = "{}-{}".format(time.strftime("%Y-%m-%d"), self.img_name)
    img_work_path = os.path.join(self.work_path, folder_name, 'stage-bakeshop')
    if os.path.isdir(img_work_path):
      shutil.rmtree(img_work_path)
    os.makedirs(self.stage_dir)
    shutil.copy(os.path.join(stage_4_dir,'EXPORT_IMAGE'),os.path.join(self.stage_dir,'EXPORT_IMAGE'))
    shutil.copy(os.path.join(stage_4_dir ,'prerun.sh'),os.path.join(self.stage_dir,'prerun.sh'))
    utils.create_files(self.json_data,'skip_stage','SKIP')
    utils.create_files(self.json_data,'skip_image','SKIP_IMAGE')
    utils.hide_files(self.json_data,'skip_image','EXPORT_IMAGE')
    utils.hide_files(self.json_data,'skip_noobs','EXPORT_NOOBS')
    
  def preheat(self):
    logger.info("Preheating")
    for filling in self.fillings:
      filling_name = filling['name']
      run_priority = filling['run_priority']
      filling_path = os.path.join('fillings',filling_name)

      if 'git_url' in filling.keys():
        git_url = filling['git_url']
        if not (git_url.startswith('https://') or git_url.startswith('git@')):
          logger.error("{}: Url {} does not start with git@ or https".format(filling_name, git_url))
          sys.exit()
        if 'git_tag' in filling.keys():
          git_tag = filling['git_tag']
        else:
          git_tag = None
        if 'ssh_key' in filling.keys():
          ssh_key = filling['ssh_key']
          if ssh_key.startswith('~/'):
            ssh_key = os.path.expanduser(ssh_key)
        else:
          ssh_key = None
        utils.pull_repo(filling_path, git_url, git_tag, ssh_key)
  
      logger.info("{}: Checking filling directory".format(filling_name))
      if(os.path.isdir(filling_path)):
        logger.info("{}: Filling directory exists".format(filling_name))
        if(utils.validate_fillings(filling_path)):
          logger.info("{}: Filling dir validated".format(filling_name))
          run_priority_length = (len(str(filling['run_priority'])))
          if(run_priority_length == 1):
            shutil.copytree(filling_path,os.path.join(self.stage_dir,"{:02d}-{}".format(run_priority,filling_name)))
          elif(run_priority_length == 2):
            shutil.copytree(filling_path,os.path.join(self.stage_dir,"{}-{}".format(run_priority,filling_name)))
          else:
            logger.error("Run priority {} is invalid".format(filling))
          logger.info("{}: Copied filling to pi-gen stage".format(filling_name))
        else:
          logger.error("{}: Filling dir failed validation".format(filling_path))
          sys.exit()
      else:
        logger.error("{}: Filling directory does not exist".format(filling_name))
        sys.exit()

    with open('pi-gen-config','w+') as config_file:
      for key in self.json_data:
        if(key != 'fillings' and key != 'skip_stage' and key != 'skip_image' and key != 'skip_noobs' and self.json_data[key] != ""):
          if(isinstance(self.json_data[key],int)):
            config_file.write("{}={}\n".format(key,self.json_data[key]))
          elif(isinstance(self.json_data[key],str)):
            config_file.write("{}=\"{}\"\n".format(key,self.json_data[key]))
          else:
            logger.error("Config value {} for key {} is neither an int or str".format(self.json_data[key],key))

  def bake(self):
    logger.info("Baking your recipe")
    if not os.path.exists(self.deploy_path):
      os.mkdir(self.deploy_path)
    os.chdir('pi-gen')
    cmd = 'sudo ./build.sh -c ../pi-gen-config'
    process = subprocess.Popen(shlex.split(cmd),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    for line in iter(process.stdout.readline, b''):
      logger.warning(line.decode().rstrip())
    os.chdir('../')

  def package(self):
    logger.info("Packaging artifacts")
    folder_name = "{}-deploy-{}".format(self.img_name,time.strftime("%Y%m%d-%H%M%S"))
    image_folder= os.path.join(self.artifacts,folder_name)
    if not os.path.exists(self.artifacts):
      os.mkdir(self.artifacts)
    os.mkdir(image_folder)
    shutil.make_archive(folder_name, 'zip', self.deploy_path)
    shutil.move("{}.zip".format(folder_name), image_folder)
    logger.info("Image location: {}".format(image_folder))
    if os.path.exists(self.deploy_path):
      shutil.rmtree(self.deploy_path)

  def clean(self):
    logger.info("Cleaning bakeshop stage from pi-gen")
    with open ('/proc/mounts', 'r') as mounts:
      for mount in mounts:
        for point in ('devpts', 'sysfs', 'udev', 'proc', 'mnt'):
          if point in mount and self.work_path in mount:
            logger.info(subprocess.call(["umount", mount.split(" ")[1]]))

    if os.path.exists(self.work_path):
      dirlist=glob.glob("{}/*{}/{}".format(self.work_path, self.img_name, 'stage-bakeshop'))
      for directory in dirlist:
        logger.info("Cleaning {}".format(directory))
        try:
          shutil.rmtree(directory)
        except PermissionError:
          logger.error("Permission error while cleaning - pi-gen bug. Try rebooting...")
        except Exception as e:
          logger.error(e)
    if os.path.exists(self.stage_dir):
      shutil.rmtree(self.stage_dir)
    if os.path.exists(self.deploy_path):
      shutil.rmtree(self.deploy_path)
    
