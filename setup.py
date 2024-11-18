#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) RVBUST, Inc - All rights reserved.

from builtins import dict
import os
import shutil
import platform
from distutils.core import setup
from Cython.Build import cythonize
import subprocess
import glob
import concurrent.futures
import fnmatch
from datetime import datetime
import pathlib


class Setup:

    def __init__(self,
                 exclude_pack_patterns,
                 software_name,
                 software_version,
                 software_description,
                 encrypt_dir_path='') -> None:
        self.m_exclude_pack_patterns = exclude_pack_patterns
        self.m_exclude_compile_patterns = ["main.py", "__init__.py"]

        self.m_software_version = software_version
        self.m_software_name = software_name
        self.m_software_description = software_description
        self.m_encrypt_dir_path = encrypt_dir_path

        self.m_bin_dir = 'bin'
        self.m_data_dir = 'data'
        self.m_install_dir = "opt"
        self.m_package_dir = "pacakageExec"
        self.m_build_dir = "buildExec"
        self.m_user = 'rvbust'

        self._init()

    def _init(self):
        self.m_all_path_dict = dict()
        self.m_current_dir_path = os.path.dirname(__file__)
        self.m_exclude_pack_patterns.append(os.path.basename(__file__))
        self.m_current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        self.m_user_dir_path = f'/home/{self.m_user}'
        self.m_package_dir_path = os.path.join(self.m_current_dir_path, self.m_package_dir)
        self.m_build_dir_path = os.path.join(self.m_current_dir_path, self.m_build_dir)
        self.m_deb_file_path = f'{self.m_current_dir_path}/{self.m_software_name}_{self.m_software_version}_{datetime.now().strftime("%Y%m%d")}_{platform.machine()}.deb'

        self.m_actual_install_dir_path = os.path.join('/', os.path.join(self.m_install_dir, self.m_software_name))
        self.m_pack_install_dir_path = os.path.join(
            self.m_current_dir_path,
            os.path.join(self.m_package_dir, os.path.join(self.m_install_dir, self.m_software_name)))

        if len(self.m_data_dir) > 0:
            self.m_actual_data_dir_path = os.path.join(self.m_actual_install_dir_path, self.m_data_dir)
            self.m_link_data_path = os.path.join(os.path.join(self.m_user_dir_path, 'Documents'), self.m_software_name)
        else:
            self.m_actual_data_dir_path = ''
            self.m_link_data_path = ''

    def _createDesktopExec(self):
        try:
            if len(self.m_bin_dir) > 0:
                source_bin_dir_path = os.path.join(self.m_current_dir_path, self.m_bin_dir)
                desktop_files = glob.glob(os.path.join(source_bin_dir_path, '*.desktop'))
            else:
                desktop_files = []
            if len(desktop_files) > 0:
                actualDesktopFileDir = os.path.join(self.m_user_dir_path, 'Desktop')
                packDesktopFileDirPath = os.path.join(self.m_current_dir_path,
                                                      os.path.join(self.m_package_dir_path, actualDesktopFileDir[1:]))
                os.makedirs(packDesktopFileDirPath)
                shutil.copy(desktop_files[0], packDesktopFileDirPath)
                self.m_actual_desktop_file_path = os.path.join(actualDesktopFileDir, os.path.basename(desktop_files[0]))
            else:
                self.m_actual_desktop_file_path = ''
        except Exception as e:
            raise Exception(f"创建桌面图标出错: {e}")
        else:
            print("创建桌面图标成功")

    def _createDEBIANFile(self):
        try:
            DebianDir = "DEBIAN"
            DebianDir = os.path.join(self.m_current_dir_path, os.path.join(self.m_package_dir_path, DebianDir))
            if os.path.exists(DebianDir) == False:
                os.makedirs(DebianDir)
            self._createDebianContolFile(os.path.join(DebianDir, "control"))
            self._createDebianPreinstFile(os.path.join(DebianDir, 'preinst'))
            self._createDebianPostinstFile(os.path.join(DebianDir, 'postinst'))
            self._createDebianPrermFile(os.path.join(DebianDir, 'prerm'))
            self._createDebianPostrmFile(os.path.join(DebianDir, 'postrm'))
        except Exception as e:
            raise Exception(f"创建DEBIN目录结构出错: {e}")
        else:
            print("创建DEBIN目录成功")

    def _createDebianContolFile(self, file):
        script_content = f"""
Package: {self.m_software_name.replace('_','-')}
Version: {self.m_software_version.replace('_','-')}
Section: base
Priority: optional
Architecture: all
Depends: python3
Maintainer: RVBUST <hr@rvbust.com>
Description: {self.m_software_description}
"""
        self._saveScriptFile(script_content, file)

    def _createDebianPreinstFile(self, file):
        script_content = f"""#!/bin/sh
echo "before installing..."
{self._createHandleeDataDirScript()}
"""
        self._saveScriptFile(script_content, file)

    def _createDebianPostinstFile(self, file):
        path_str_list = [self.m_actual_install_dir_path, '']
        if len(self.m_link_data_path) > 0:
            path_str_list[0] += f' {self.m_link_data_path}'
        if len(self.m_actual_desktop_file_path) > 0:
            path_str_list[0] += f' {self.m_actual_desktop_file_path}'

        if len(self.m_actual_data_dir_path) > 0 or len(self.m_actual_desktop_file_path) > 0:
            path_str_list[1] = f'chmod -R 777'
        if len(self.m_actual_data_dir_path) > 0:
            path_str_list[1] += f' {self.m_actual_data_dir_path}'
        if len(self.m_actual_desktop_file_path) > 0:
            path_str_list[1] += f' {self.m_actual_desktop_file_path}'

        script_content = f"""#!/bin/sh
echo "after installing..."
{self._mvDataDir(True)}
echo "create dataPath link"
{self._handleDataDirLink(True)}
chmod -R 755 {path_str_list[0]}
chown -R root:root {path_str_list[0]}
{path_str_list[1]}
"""
        self._saveScriptFile(script_content, file)

    def _createDebianPrermFile(self, file):
        script_content = f"""#!/bin/sh
echo "before removing..."
{self._createHandleeDataDirScript()}
"""
        self._saveScriptFile(script_content, file)

    def _createDebianPostrmFile(self, file):
        script_content = f"""#!/bin/sh
echo "after removing..."
{self._mvDataDir(True)}
echo "remove dataPath link"
{self._handleDataDirLink(False)}

if [ "$1" = "purge" ]; then
    rm -rf {self.m_actual_install_dir_path}
    echo "completely removed!"
fi
"""
        self._saveScriptFile(script_content, file)

    def _createHandleeDataDirScript(self):
        content = f"""
if [ -d {self.m_actual_data_dir_path} ]; then
    if [ "$1" = "upgrade" ] || [ "$1" = "install" ]; then
        echo "A new version software is about to be installed. Do you want to keep the previous data? (Y/n)"
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY]|'')
                echo 'Use the previous data!'
                {self._mvDataDir(False)}
                ;;
            *)
                echo 'Use default data.'
                rm -rf {self.m_actual_data_dir_path}
                ;;
        esac
    elif [ "$1" = "remove" ]; then
        {self._mvDataDir(False)}
    fi
fi
"""
        return content

    def _saveScriptFile(self, content, file):
        with open(file, "w") as f:
            f.write(content)
        self._run_command(['chmod', '+x', file])

    def _mvDataDir(self, opposite=False):
        script_content = ''
        if len(self.m_actual_data_dir_path) > 0:
            target_path = f'/opt/dataTmp_{self.m_current_time}'
            if opposite == False:
                mvStr = f'mv {self.m_actual_data_dir_path} {target_path}'
                script_content = f'''
if [ -d {self.m_actual_data_dir_path} ]; then
    echo "{mvStr}"
    {mvStr}
fi
'''
            else:
                mvStr = f'mv {target_path} {self.m_actual_data_dir_path}'
                script_content = f'''
if [ -d {target_path} ]; then
    mkdir -p {self.m_actual_data_dir_path}
    if [ -d {self.m_actual_data_dir_path} ]; then
        rm -rf {self.m_actual_data_dir_path}
    fi
    echo "{mvStr}"
    {mvStr}
fi
'''
        return script_content

    def _handleDataDirLink(self, create=True):
        if len(self.m_actual_data_dir_path) > 0:
            if create:
                return f'ln -s {self.m_actual_data_dir_path} {self.m_link_data_path}'
            else:
                return f'rm -rf {self.m_link_data_path}'
        else:
            return str()

    def _packExec(self):
        try:
            self._run_command(["dpkg-deb", "--build", self.m_package_dir_path, self.m_deb_file_path])
        except Exception as e:
            raise Exception(f"生成deb文件出错: {e}")
        else:
            print("生成deb文件成功")

    def _getPackDict(self, path):
        all_files_and_folders = os.listdir(path)
        if len(all_files_and_folders) > 0:
            files_list = []
            dirs_list = []
            for item in all_files_and_folders:
                if self._ignored(item, self.m_exclude_pack_patterns) == False:
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        dirs_list.append(item)
                    elif os.path.isfile(item_path):
                        files_list.append(item)
            if len(files_list) > 0:
                self.m_all_path_dict[path] = files_list
            for item in dirs_list:
                self._getPackDict(os.path.join(path, item))

    def _ignored(self, item, patterns):
        for pattern in patterns:
            if fnmatch.fnmatch(item, pattern):
                return True
        return False

    def _compileOrCopyFile(self):
        fileDealDict = dict()
        for key in self.m_all_path_dict.keys():
            packPath = key.replace(self.m_current_dir_path, self.m_pack_install_dir_path)
            if os.path.exists(packPath) == False:
                os.makedirs(packPath)

            if self._ignored(
                    key.replace(self.m_current_dir_path, str()).split("/")[-1],
                    self.m_exclude_compile_patterns) == True:
                for file in self.m_all_path_dict[key]:
                    fileDealDict[(key, file, packPath)] = False
            else:
                newPackPath = packPath
                package_path = key
                while "__init__.py" in self.m_all_path_dict.get(package_path, []):
                    package_path = os.path.dirname(package_path)
                    newPackPath = os.path.dirname(newPackPath)

                for file in self.m_all_path_dict[key]:
                    if self._ignored(file, self.m_exclude_compile_patterns) == False and file.endswith(".py"):
                        fileDealDict[(key, file, newPackPath)] = True
                    else:
                        fileDealDict[(key, file, packPath)] = False
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                futures = []
                for key, value in fileDealDict.items():
                    futures.append(executor.submit(self._dealSingleFile, key[0], key[1], key[2], value))
                doneResults, notDoneResults = concurrent.futures.wait(futures, timeout=None)
                for future in doneResults:
                    if future.exception() is not None:
                        raise future.exception()
        except Exception as e:
            raise e
        else:
            print('编译成功')

    def _dealSingleFile(self, fileDir, fileName, packPath, compileEnable):
        filePath = os.path.join(fileDir, fileName)
        if compileEnable:
            try:
                setup(
                    ext_modules=cythonize(
                        filePath,
                        build_dir=self.m_build_dir_path,
                        compiler_directives={"language_level": "3"},
                    ),
                    script_args=[
                        "build_ext",
                        "-b",
                        packPath,
                        "-t",
                        self.m_build_dir_path,
                        "-j",
                        "8",
                    ],
                )
            except Exception as e:
                raise Exception(f"编译{filePath}文件出错: {e}")
            finally:
                c_file = os.path.join(fileDir, fileName.split(".")[0] + ".c")
                if os.path.exists(c_file):
                    os.remove(c_file)
        else:
            shutil.copy(filePath, packPath)

    def _removePackageAndBuildDir(self):
        if os.path.exists(self.m_build_dir_path):
            shutil.rmtree(self.m_build_dir_path)
        if os.path.exists(self.m_package_dir_path):
            shutil.rmtree(self.m_package_dir_path)

    def _getPackFile(self):
        self._removePackageAndBuildDir()
        self.m_all_path_dict.clear()
        self._getPackDict(self.m_current_dir_path)
        for dir, fileList in self.m_all_path_dict.items():
            delFileList = []
            for file in fileList:
                if file.endswith(".c"):
                    filePath = os.path.join(dir, file)
                    print(f'remove {filePath}')
                    os.remove(filePath)
                    delFileList.append(file)
            for delFile in delFileList:
                self.m_all_path_dict[dir].remove(delFile)

    def _encrypt(self, encrypt=False):
        if encrypt and len(self.m_encrypt_dir_path) > 0:
            toolPath = f'{self.m_encrypt_dir_path}/SentinelTool'
            cfgxPath = f'{self.m_encrypt_dir_path}/Sentinel.cfgx'
            if os.path.exists(toolPath) and os.path.exists(cfgxPath):
                so_files = [x for x in pathlib.Path(self.m_package_dir_path).rglob("*.so") if x.is_file()]
                try:
                    encrypt_fileList = []
                    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                        futures = []
                        for file in so_files:
                            encrypt_file = str(file).replace('.so', '_encrypt.so')
                            encrypt_fileList.append(encrypt_file)
                            futures.append(
                                executor.submit(self._run_command, [toolPath, f'-c:{cfgxPath}', file, encrypt_file]))
                        doneResults, notDoneResults = concurrent.futures.wait(futures, timeout=None)
                        for future in doneResults:
                            if future.exception() is not None:
                                raise future.exception()
                except Exception as e:
                    for file in encrypt_fileList:
                        if os.path.exists(file):
                            os.remove(file)
                    raise Exception(f"加密文件出错: {e}")
                else:
                    canEncrypt = True
                    for encrypt_file in encrypt_fileList:
                        if pathlib.Path(encrypt_file).exists() == False:
                            print(f'{encrypt_file}未找到，加密失败')
                            canEncrypt = False
                            break
                    if canEncrypt:
                        for file in so_files:
                            if os.path.exists(file):
                                os.remove(file)

                        for encrypt_file in encrypt_fileList:
                            source_path = pathlib.Path(encrypt_file)
                            target_path = pathlib.Path(encrypt_file.replace('_encrypt.so', '.so'))
                            source_path.rename(target_path)
                        self.m_deb_file_path = f'{self.m_current_dir_path}/{self.m_software_name}_{self.m_software_version}__{datetime.now().strftime("%Y%m%d")}_{platform.machine()}_encrypted.deb'
                        print("加密文件成功")
                    else:
                        for encrypt_file in encrypt_fileList:
                            file_path = pathlib.Path(encrypt_file)
                            if file_path.exists():
                                file_path.unlink()
            else:
                print("不存在加密工具，取消加密文件")
        else:
            print("未加密文件")

    def _run_command(self, commandList):
        try:
            result = subprocess.run(commandList, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except Exception as e:
            raise e

    def compileAndPackExec(self, encrypt=False):
        try:
            self._getPackFile()  #获取打包文件
            self._compileOrCopyFile()  #编译或者复制文件
            self._encrypt(encrypt)  #加密.so文件
            self._createDesktopExec()  #创建桌面图标
            self._createDEBIANFile()  #创建DEBIAN目录结构
            self._packExec()  #打包deb文件
        except Exception as e:
            print(f"{e},打包终止")
        else:
            print('打包成功')
        finally:
            self._removePackageAndBuildDir()


if __name__ == "__main__":
    excludePackPatterns = [
        ".git*", '*.md', "__pycache__", "*.ui", "*.qrc", "*.deb", 'raw_data*', 'MvSdkLog', 'test', 'tmp', 'example',
        'dependencies', 'doc', 'model_source', "build", "data_jinlv_motoman", "data_rvbust_fanuc", "data_yutong_abb"
    ]
    # from src.common.software_config import software_name, software_main_version, software_sub_version, software_description
    software_name = 'Test'
    software_version = '1.0.0'
    software_description = '测试'

    my_setup = Setup(excludePackPatterns, software_name, software_version, software_description)
    my_setup.compileAndPackExec()
