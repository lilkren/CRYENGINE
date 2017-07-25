#!python3
"""
This script combines the required engine and project files into a single directory.
It also creates .pak files from the asset directory and writes an appropriate system.cfg.
"""
import os
import shutil
import stat
import fnmatch
import subprocess
import cryrun, cryproject
import ctypes

def run(project_file):
    # Path to the project file as created by the launcher - engine and project path are derivable from this.
    project = cryproject.load(project_file)
    project_title = project['info']['name']

    # "\\\\?\\" is added to make sure copying doesn't crash on Windows because the path gets too long for some files.
    # This is a requirement to copy the Mono folder on Windows.
    long_path_prefix = "\\\\?\\" if os.name == "nt" else ""

    # The path the folder that contains the .cryproject file.
    project_path = os.path.dirname(project_file)
    project_path_long = long_path_prefix + project_path

    # The path to the engine that is being used by the project.
    engine_path = cryrun.get_engine_path()
    engine_path_long = long_path_prefix + engine_path

    # Path to which the game is to be exported.
    export_path = os.path.join(project_path, '{}_package'.format(project_title))
    export_path_long = long_path_prefix + export_path

    print("Packaging project " + project_title)
    print("Building to: " + export_path);

    task_list = []

    if os.path.exists(export_path):
        task_list.append(("Deleting previous build...", delete_previous_build, export_path_long))

    task_list.append(("Packaging custom engine assets...", package_engine_assets, engine_path, export_path))
    task_list.append(("Copying default engine assets...", copy_engine_assets, engine_path_long, export_path_long))
    task_list.append(("Copying engine binaries...", copy_engine_binaries, engine_path_long, export_path_long, os.path.join('bin', 'win_x64')))

    if cryproject.is_managed(project):
        task_list.append(("Copying mono files...", copy_mono_files, engine_path_long, export_path_long))

    task_list.append(("Copying game binaries...", copy_plugins, project, project_path, export_path))
    task_list.append(("Packaging game assets...", package_assets, project, engine_path, project_path, export_path))
    task_list.append(("Cleaning up temp folders...", delete_temp_folders, engine_path_long, project_path_long))
    task_list.append(("Creating config files...", create_config, project, project_file, export_path))

    i = 0
    count = len(task_list)
    for task in task_list:
        description = task[0]
        print(description)
        set_title("{}% {}".format(int(get_percentage(i, count)), description))
        task[1](*task[2:])
        i += 1

    set_title("100% Build packaged successfully")
    print("Build packaged successfully")
    print("Press Enter to exit")
    input()

def delete_previous_build(export_path):
    """
    Deletes the folder found at export_path, and properly handles deleting
    read-only files.
    """
    if os.path.exists(export_path):
        shutil.rmtree(export_path, onerror = on_rm_error)
def delete_temp_folders(engine_path, project_path):
    delete_temp_engine_folder(engine_path)
    delete_temp_assets_folder(project_path)

def delete_temp_engine_folder(engine_path):
    temp_dir = os.path.abspath(os.path.join(engine_path, os.pardir, "_rc_PC"))
    if os.path.exists(temp_dir):
        os.chmod(temp_dir, stat.S_IWRITE)
        shutil.rmtree(temp_dir, onerror = on_rm_error)

def delete_temp_assets_folder(project_path):
    temp_dir = os.path.abspath(os.path.join(project_path, os.pardir, "_rc_PC_pure"))
    if os.path.exists(temp_dir):
        os.chmod(temp_dir, stat.S_IWRITE)
        shutil.rmtree(temp_dir, onerror = on_rm_error)

def on_rm_error(func, path, exc_info):
    """
    Clears the read-only flag of the file at path, and unlinks it.
    :param func: The function that raised the exception.
    :param path: The path of the file that couldn't be removed.
    :param exc_info: The exception information returned by sys.exc_info().
    """
    os.chmod( path, stat.S_IWRITE )
    os.unlink( path )

def get_percentage(index, count):
    return (100.0 / count) * index

def set_title(title):
    if not title:
        title = "Building..."

    #using the kernel32 should be better, but in case it's not working it can switch to using system().
    try:
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        if kernel32:
            kernel32.SetConsoleTitleW(u"{}".format(title))
    except:
        system("title {}".format(title))

def copy_engine_binaries(engine_path, export_path, rel_dir):
    """
    Copy a directory to its corresponding location in the export directory.
    :param engine_path: Current location of the files (project_path or engine_path).
    :param export_path: Path to which the binaries should be exported.
    :param rel_dir: Path of the directory to copy, relative to *source_dir*.
    """
    copypaths = []

    excludes = ['imageformats**',
                'ToolkitPro*',
                'platforms**',
                'Qt*',
                'mfc*',
                'CryGame*',
                'CryEngine.*.dll*',
                'Sandbox*',
                'ShaderCacheGen*',
                'icu*',
                'python27*',
                'LuaCompiler*',
                'Editor**',
                'PySide2*',
                'shiboken*',
                'crashrpt*',
                'CrashSender*',
                '*.pdb',
                '*.mdb',
                '*.ilk',
                '*.exp',
                '*.lib',
                '*.xml',
                '*.ipdb',
                '*.iobj',
                'CryQt*',
                '_CryQt*',
                '*.pyd'
                ]

    pwd = os.getcwd()
    os.chdir(engine_path)
    for root, _, filenames in os.walk(rel_dir):
        for filename in filenames:
            copypaths.append(os.path.normpath(os.path.join(root, filename)))
    os.chdir(pwd)

    for path in copypaths:
        excluded = False
        for pattern in excludes:
            excluded = fnmatch.fnmatch(path, os.path.join(rel_dir, pattern))
            if excluded:
                break
        if excluded:
            continue
        destpath = os.path.normpath(os.path.join(export_path, path))
        if not os.path.exists(os.path.dirname(destpath)):
            os.makedirs(os.path.dirname(destpath))
        shutil.copy(os.path.join(engine_path, path), destpath)


def copy_mono_files(engine_path, export_path):
    """
    Copy mono directory and CRYENGINE C# libraries to export path.
    """
    input_bindir = os.path.join(engine_path, 'bin')
    output_bindir = os.path.join(export_path, 'bin')

    shutil.copytree(os.path.join(input_bindir, 'common'), os.path.join(output_bindir, 'common'))

    for csharp_file in os.listdir(os.path.join(input_bindir, 'win_x64')):
        # We've already copied the non-C# libraries, so skip them here.
        if not fnmatch.fnmatch(csharp_file, 'CryEngine.*.dll'):
            continue
        shutil.copyfile(os.path.join(input_bindir, 'win_x64', csharp_file),
                        os.path.join(output_bindir, 'win_x64', csharp_file))

def run_command(command, silent=True):
    # Filter empty commands and convert the command to a string.
    command = list(filter(bool, command))
    command_str = ("".join("{} ".format(e) for e in command)).strip()

    # Using check_output here makes the command execute silently,
    # while still having the option to print the output in case of an error.
    try:
        if silent:
            subprocess.check_output(command_str)
        else:
            subprocess.check_call(command_str)
    except subprocess.CalledProcessError as e:
        if not e.returncode == 0:
            print("Encountered and error while running command '{}'!".format(command_str))
            print(e.output)
            return False

    return True

def package_engine_assets(engine_path, export_path):
    """
    Runs the Resource Compiler on the engine assets following the
    instructions of rcjob_release_engine_assets.xml. Outputs the
    .pak files in the Engine folder of the build.
    """

    rc_path = os.path.join(engine_path, "Tools", "rc", "rc.exe")
    rc_job_path = os.path.join(engine_path, "Tools", "CryVersionSelector", "rc_jobs", "rcjob_release_engine_assets.xml")

    if os.path.isfile(rc_path) and os.path.isfile(rc_job_path):
        pwd = os.getcwd()
        os.chdir(engine_path)
        rc_cmd = [  '"{}"'.format(rc_path),
                    '/job="{}"'.format(rc_job_path),
                    '/p=PC',
                    '/pak_root="{}"'.format(export_path),
                    '/IncludeShaderSource=1',
                    '/stripMetadata']
        run_command(rc_cmd)
        os.chdir(pwd)
    else:
        if not os.path.isfile(rc_path):
            print("Unable to package the engine assets with the resource compiler because '{}' is missing!".format(rc_path))
        else:
            print("Unable to package the engine assets with the resource compiler because '{}' is missing!".format(rc_job_path))

def copy_engine_assets(engine_path, export_path):
    """
    Copy the engine assets, making sure to avoid .cryasset.pak files.
    If the engine assets have already been packaged this function will
    not overwrite them.
    """
    if not os.path.exists(os.path.join(export_path, 'engine')):
        os.makedirs(os.path.join(export_path, 'engine'))

    for pakfile in os.listdir(os.path.join(engine_path, 'engine')):
        srcpath = os.path.join(engine_path, 'engine', pakfile)
        dstpath = os.path.join(export_path, 'engine', pakfile)

        if pakfile.endswith('.cryasset.pak') or not pakfile.endswith('.pak'):
            continue

        # If package_engine_assets has already copied a .pak file of the same name, don't overwrite it.
        if os.path.isfile(dstpath):
            continue

        shutil.copyfile(srcpath, dstpath)

def package_assets(project, engine_path, project_path, export_path):
    """
    Runs the Resource Compiler on the game assets following the
    instructions of rcjob_release_game_assets.xml. Outputs the
    .pak files in the Assets folder of the build that's specified
    in the project file.
    """
    rc_path = os.path.join(engine_path, "Tools", "rc", "rc.exe")
    rc_job_path = os.path.join(engine_path, "Tools", "CryVersionSelector", "rc_jobs", "rcjob_release_game_assets.xml")

    if os.path.isfile(rc_path) and os.path.isfile(rc_job_path):
        asset_dir = cryproject.asset_dir(project)
        pwd = os.getcwd()
        os.chdir(project_path)
        rc_cmd = [  '"{}"'.format(rc_path),
                    '/job="{}"'.format(rc_job_path),
                    '/p=PC',
                    '/pak_root="{}"'.format(export_path),
                    '/TargetHasEditor=0',
                    '/game="{}"'.format(asset_dir),
                    '/stripMetadata']
        run_command(rc_cmd)
        os.chdir(pwd)
    else:
        if not os.path.isfile(rc_path):
            print("Unable to package the game assets with the resource compiler because '{}' is missing!".format(rc_path))
        else:
            print("Unable to package the game assets with the resource compiler because '{}' is missing!".format(rc_job_path))

def create_config(project, project_file, export_path):
    # Change the extension of the cryproject file so it won't show all the cryproject option on right-click.
    game_extension = ".crygame"
    project_name = os.path.splitext(os.path.basename(project_file))[0] + game_extension

    shutil.copyfile(project_file, os.path.join(export_path, project_name))

    with open(os.path.join(export_path, 'system.cfg'), 'w') as fd:
        fd.write('sys_project={}\n'.format(project_name))


def copy_plugins(project, project_path, export_path):
    """
    Copies all .dll files that belong to the plugins of the project.
    """
    plugins = cryproject.plugins_list(project)
    for plugin in plugins:
        path = plugin.get("path")

        if path == None:
            continue

        if not path.endswith(".dll"):
            continue

        src_file = os.path.join(project_path, path)
        dst_file = os.path.join(export_path, path)
        if os.path.isfile(src_file):
            shutil.copyfile(src_file, dst_file)
        else:
            print("Failed to copy plugin file '" + path + "'!")
            print(src_file)
