![Bakeshop Logo](https://i.imgur.com/dIB8opo.png)  
Bakeshop is an easy to use extensible wrapper for pi-gen that reduces the manual
overhead of generating raspberry pi images. Bakeshop uses a JSON based
configuration file called a recipe to define a pi-gen environment before image
build time. Bakeshop allows users to easily add N number of custom settings called
fillings into pi-gens image build process. A Bakeshop recipe incorporates all of
pi-gens configuration file settings plus additional custom configurations that
enable users to skip stages, skip the imaging process of a stage in bulk, pull
from git repositories, and define fillings to be used in a recipe.

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
git clone --recursive git@github.com:anthok/Bakeshop.git 
```

## Filling Directory Structure
A filling is a group of Raspberry Pi configuration settings that define particular
configurations a user wants to incorporate in a Bakeshop image. The Bakeshop
team recommends modularizing fillings so that they can be reused in future builds
i.e., A generic base filling can be used to install the same SSH keys on a Bakeshop
image every time a user wants to deploy an image. A more specific filling would
then be created to configure the raspberry pi image for the actions it is performing
(turning wifi off). Filling names can be named anything, however the contents of a
particular filling **must follow pi-gens standards**. Bakeshop uses strict checking
to ensure only pi-gen related files are in the filling directory. The files/ directory
can be used to facilitate any other files that need to be placed into a Bakeshop image
i.e., SSH public keys to be placed on the image.

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
**Please see the pi-gen documentation when determining what content should be placed in each
configuration file**
                

## Recipe File
A Bakeshop recipe defines the configuration of a Raspberry Pi image. Options in
uppercase represent pi-gen native options. Options in lowercase are Bakeshop
specific options. **Please read the pi-gen documentation to determine which options
are right for your Bakeshop build.** Bakeshops recipe configuration file
supports all configuration parameters allowed by pi-gen. Bakeshop does strict
checking on the type value supplied for each setting.

The Bakeshop team recommends using the following base recipe configuration for
lite images:
```
{
  "Images":
  [
    {
      "IMG_NAME": "pi-image",
      "DEPLOY_ZIP": 1,
      "RELEASE":"buster",
      "TARGET_HOSTNAME":"pi",
      "KEYBOARD_KEYMAP":"gb",
      "KEYBOARD_LAYOUT":"English (US)",
      "TIMEZONE_DEFAULT":"Europe/London",
      "FIRST_USER_NAME":"pi",
      "FIRST_USER_PASS":"raspberry",
      "ENABLE_SSH":1,
      "STAGE_LIST":"stage0 stage1 stage2 stage-Bakeshop",
      "skip_stage": ["stage2", "stage4", "stage5"],
      "skip_image": ["stage2", "stage3", "stage4", "stage5"],
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
The following are custom options integrated into building a Bakeshop image:

* `STAGE_LIST` 
A pi-gen specific configuration option that allows the user to
specify the order in which stages should be executed. If you are building on
top of a raspbian lite image the Bakeshop team recommends leaving the STAGE_LIST
as is. If you are trying to build a later stage, consult the pi-gen documentation
and reorder the stages accordingly.

* `skip_stage`
A Bakeshop specific configuration which tells Bakeshop which stages should be
skipped. For example: If you are building a raspbian lite image you can skip stages
3,4, and 5. This configuration tells Bakeshop to place the SKIP file in each of
the listed stages. See pi-gen documentation for more details on the SKIP file.

* `skip_image`
A Bakeshop specific configuration which tells Bakeshop which image creations
should be skipped. For example: If you are building a raspbian lite image you can
skip image building for stages 4, and 5. This configuration tells Bakeshop to
place the SKIP_IMAGE file in each of the listed stages. See pi-gen documentation for
more details on the SKIP_IMAGE file.

* `fillings`
A Bakeshop specific configuration which specifies the fillings that are put into
Bakeshops custom stage. Each filling is required to have a name and a run_priority.
  
  * `name`
  The filling name with the recipe must match the name in the fillings directory.
  
  * `run_priority`
  The run_priority specifies the order in which the recipe is run. Run_priority
  follows pi-gens naming convention to determine run order. Run_priority can range
  from 0-99.

  * `Optional Configurations`

    * `git_url`
    Fetches a filling from a git repository. The repo will be pulled using git fetch
    if it does not exist locally on the system. If it exists locally the latest version
    of the filling will be pulled unless git_tag is populated. If an internet connection
    is not available Bakeshop will check the fillings directory to see if an older
    version of the filling exists. **Pulling submodules is not supported through Bakeshop.
    The Bakeshop team recommends pulling a repo locally with its submodules and pointing
    Bakeshop to the local version rather than the remote version**

    * `git_tag`
    Specifies which git tag to pull from. Git tags should be used to track versions of
    fillings.

    * `git_ssh_key`
    If you are using gitlab or authentication with github, git_ssh_key can be set to the
    path of an ssh key associated with a git repo. Password authentication is not supported.

## How to run
```
sudo python3 Bakeshop.py -r recipe/recipe.json {clean}
```

## Bakeshop Options
Bakeshop does have a clean option to remove build directories from a specific recipe.
To clean a specific recipe, add the "clean" command. The clean option will attempt
to unmount mount points that pi-gen uses during the image build process. **This option
is experimental, it attempts to solve a problem discovered when building consecutive
images**. The clean option will also remove the pi-gen work directory of old builds
for the specified recipe. **If a build is interrupted for any reason, the work directory
should be cleaned.**

## Output
Bakeshop archives any file/folder within pi-gens deploy/ directory and moves
the archive into Bakeshops artifacts/ directory. This is useful when generating
custom images with encryption keys that should be backed up by the user. Depending
on the contents of fillings any other file a user decides to put in the deploy/
directory will be packaged into the final outputs archive. After the build of an
image is complete, Bakeshop will delete the contents of pi-gens deploy/ directory.
All archives of images built by Bakeshop will be stored if the artifacts/ directory
and never deleted.

## Known Issues
  * The Bakeshop team recognizes that this option might have to be run multiple times
    unmount pi-gen mount points. If unmount is still failing the end user may have to
    reboot their machine in order to unmount the mount points.

  * The Bakeshop team recognizes that if a Bakeshop image needs to be rebuilt due to
    configuration changes, the end user is responsible for manually removing configurations
    they don't wish to have the rebuilt image. The Bakeshop team recommend the end user 
    clean the stage and run the build again, however this can be time consuming. 

## Future Ideas
  * The Bakeshop team plans to build out a repository for both fillings and recipes that
    end users can pull from.