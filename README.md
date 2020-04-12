![Bakeshop Logo](https://i.imgur.com/dIB8opo.png)  
Bakeshop is an easy to use extensible wrapper for pi-gen that reduces the manual
overhead of generating raspberry pi images. Bakeshop uses a JSON based
configuration file called a recipe to define a pi-gen environment before image
build time. Bakeshop allows users to easily add N number of custom stages called
fillings into pi-gens image build process. Addtionally Bakeshops recipe JSON
has some custom configuration keys that allow users to skip stages or skip the
imaging process of a stage in bulk.

## Dependencies
Please read pi-gens installation guide before continuing. 

The following packages are required for pi-gen:
```bash
apt-get install coreutils quilt parted qemu-user-static debootstrap zerofree zip \
dosfstools bsdtar libcap2-bin grep rsync xz-utils file git curl
```

The following packages are required for Bakeshop:
```bash
apt-get install python3 python3-pip uuid-runtime
```
```bash
pip install -r requirements.txt
```
```bash
git clone --recursive git@github.com:anthok/bakeshop.git 
```

## Filling Directory Structure
Filling names can be named anything, however the contents of a particular
filling **must follow pi-gens standards**. Bakeshop uses strict checking to ensure 
only pi-gen related files are in the filling directory. The files/ directory can be used
to facilitate any other files that need to be incorporated into a filling.

When creating a filling the following directory structure must be met:
```
+--fillings
    |
    +--filling_name
    |             |
    |             +--00-debconf
    |             +--00-packages
    |             +--00-packages-nr
    |             +--01-run.sh
    |             \--files
    |                    |
    |                    \--any_addtional_files_you_need
    \--filling_name
                  |
                  +--00-debconf
                  +--00-packages
                  +--00-packages-nr
                  +--01-run.sh
                  \--files
                         |
                         \--any_addtional_files_you_need
```                
                

## Recipe File
Bakeshops recipe configuration file supports all configuration parameters
allowed by pi-gen. bakeshop does strict checking on the type value supplied for
each setting.  Please check pi-gens documentation of you are unsure of a particular
type value.

The Bakeshop team recommends using the following base recipe configuration for
lite images:
```
{
  "Images":
  [
    {
      "IMG_NAME": "pi-image",
      "DEPLOY_ZIP": 1,
      "HOSTNAME":"pi",
      "KEYBOARD_KEYMAP":"gb",
      "KEYBOARD_LAYOUT":"English (UK)",
      "TIMEZONE_DEFAULT":"Europe/London",
      "FIRST_USER_NAME":"pi",
      "FIRST_USER_PASS":"raspberry",
      "ENABLE_SSH":1,
      "STAGE_LIST":"stage0 stage1 stage2 stage-bakeshop",
      "skip_stage": ["stage3", "stage4", "stage5"],
      "skip_image": ["stage4", "stage5"],
      "fillings": [
        {
          "name": "filling0",
          "run_priority": 0
        },
        {
          "name": "filling1",
          "git_url": "git@gitlab.x.x:bakers/filling1.git",
          "git_tag": "1.0",
          "ssh_key": "~/.ssh/id_rsa",
          "run_priority": 1
        },
        {
          "name": "filling2",
          "run_priority": 2
        },
        {
          "name": "lastfilling3",
          "run_priority": 3
        }
      ]
    }
  ]
}
```

## Bakeshop recipe options
* `STAGE_LIST` 
A pi-gen specfic configuration option that allows the user to
specify the order in which stages should be executed. If you are buliding on
top of a rasbian lite image the Bakeshop team recommends leaving the STAGE_LIST
as is. If you are trying to build later stage, consult the pi-gen documentation
and reorder the stages accordingly.

* `skip_stage`
A Bakeshop specfic configuration which tells bakeshop which stages should be
skipped. For example: If you are building a rasbian lite image you can skip stages
3,4, and 5. This configuration tells Bakeshop to place the SKIP file in each of
the listed stages. See pi-gen documentation for more details on the SKIP file.

* `skip_image`
A Bakeshop specfic configuration which tells bakeshop which image creations
should be skipped. For example: If you are building a rasbian lite image you can
skip image building for stages 4, and 5. This configuration tells Bakeshop to
place the SKIP_IMAGE file in each of the listed stages. See pi-gen documentation for
more details on the SKIP_IMAGE file.

* `fillings`
A Bakeshop specfic configuration which specfies the fillings that are put into
bakeshops custom stage. Each filling is required to have a name and a run_priority.
  
  * `name`
  The filling name with the recipe must match the name in the fillings directory.
  
  * `run_priority`
  The run_priority specfies the order in which the recipe is run. Run_priority
  follows pi-gens naming convention to determine run order. Run_priority can range
  from 0-99. Other non-required filling options are defined below.

  * `git_url`
  Fetchs a filling from a git repoisitory. The repo will be pulled using git fetch if it does not exist locally on the system. If it exists locally the latest version of the filling will be pulled unless git_tag is populated. If an internet connection is not available Bakeshop will check the fillings directory to see if an older version of the filling exists.

  * `git_tag`
  Specifies which git tag to pull from. Git tags will be used to track versions of the filling.

  * `git_ssh_key`
  If you are using gitlab or authentication with github, git_ssh_key can be set to the path of an ssh key associated with a git repo. Password authentication is not supported. 



## How to run
```
sudo python3 bakeshop.py -r recipe/recipe.json {clean}
```

## Bakeshop Options
To run normally, simply run with -r option.
Clean option will clean the pi-gen work directory of old builds of the specfied recipes.
If a build is interrupted the work directory should be cleaned. 

## Output
Bakeshop archives any file/folder within pi-gens deploy/ directory and moves
the archive into bakeshops artifacts/ directory. This is useful when generating
custom images with encryption keys that should be backed up by the user. Depending
on the contents of fillings any other file a user decides to put in the deploy/
directory will be packaged into the final outputs archive. After the build of an
image is complete, bakeshop will delete the contents of pi-gens deploy/ directory.
All archives of images built by bakeshop will be stored if the artifacts/ directory
and never deleted.
