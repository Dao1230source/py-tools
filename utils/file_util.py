import imghdr
import os
import shutil
import tarfile

import PIL
from PIL import Image

PIL.Image.MAX_IMAGE_PIXELS = 933120000


def decompress_tar(decompress_dir: str, file_path: str) -> None:
    if tarfile.is_tarfile(file_path):
        with tarfile.open(file_path) as t:
            members = t.getmembers()
            for m in members:
                base_name = os.path.basename(file_path)
                f_name = base_name[:base_name.index('.')]
                _, format_name = os.path.splitext(m.db_profile_name)
                m.db_profile_name = f'{f_name}{format_name}'
                t.extract(m, decompress_dir)


def decompress_tar_batch(un_dir: str, file_paths: [str]) -> None:
    for f in file_paths:
        decompress_tar(un_dir, f)


def decompress(compressed_files_dir, decompressed_dir, file_format='tar.gz'):
    tar_gz_files = get_specified_files(compressed_files_dir, lambda x: x.endswith(file_format))
    decompress_tar_batch(decompressed_dir, tar_gz_files)


def files_filter(specified_files: [str], file_path: str, filter_func: callable) -> [str]:
    """
    获取符合过滤条件的文件
    :param specified_files:
    :param file_path:
    :param filter_func: 过滤函数，待处理的参数是 文件的basename
    (file_base_name) -> bool
    :return:
    """
    file_base_name = os.path.basename(file_path)
    if filter_func(file_base_name):
        specified_files.append(os.path.abspath(file_path))
    return specified_files


def get_specified_files(file_dir: str, filter_func: callable) -> [str]:
    specified_files = []
    if not os.path.exists(file_dir):
        return specified_files
    if os.path.isfile(file_dir):
        return files_filter(specified_files, file_dir, filter_func)
    # os.listdir 无法获取 D:\user\downloads下文件列表，可能是权限问题
    files = os.listdir(file_dir)
    for f in files:
        f = os.path.join(file_dir, f)
        if os.path.isfile(f):
            specified_files = files_filter(specified_files, f, filter_func)
        elif os.path.isdir(f):
            specified_files.extend(get_specified_files(f, filter_func))
    return specified_files


def remove_files(file_paths: [str]):
    for f in file_paths:
        if os.path.exists(f):
            if os.path.isfile(f):
                os.remove(f)
            if os.path.isdir(f):
                shutil.rmtree(f)


def empty_dir(_dir: str):
    if os.path.exists(_dir):
        files = os.listdir(_dir)
        remove_files(files)


def move_files_to(file_paths: [str], target_dir: str):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    for f in file_paths:
        shutil.move(f, target_dir)


def compress_image(source_file, target_file=None, target_size=1024, step=10, quality=80):
    """不改变图片尺寸压缩到指定大小
    :param source_file: 压缩源文件
    :param target_file: 压缩文件保存地址
    :param target_size: 压缩目标，KB
    :param step: 每次调整的压缩比率
    :param quality: 初始压缩比率
    :return: 压缩文件地址，压缩文件大小
    """
    if not os.path.exists(source_file):
        return None, 0
    source_file_dir = os.path.dirname(source_file)
    source_file_base_name = os.path.basename(source_file)
    source_file_name, ext_format = os.path.splitext(source_file_base_name)
    source_file_name = source_file_name.replace("'", "")
    print('source_file_name', source_file_name)
    # 图片实际类型与名称后缀类型不符
    source_real_format = imghdr.what(source_file)
    if ext_format != source_real_format:
        print('source_real_format', source_real_format)
        ext_format = '.' + source_real_format
        new_source_file = os.path.join(source_file_dir, source_file_name + ext_format)
        im: Image = Image.open(source_file)
        im.save(new_source_file)
        source_file = new_source_file
        print('source_real_format:{}'.format(source_file))
    file_size_b = os.path.getsize(source_file)
    target_file_size_b = target_size * 1024
    # 如果小于目标尺寸，return
    if file_size_b <= target_file_size_b and str(ext_format).lower() in ('.png',):
        return source_file, file_size_b
    if not ext_format:
        ext_format = '.jpg'
    # PIL.Image 不是jpg的，全部转为jpg处理
    if str(ext_format).lower() not in ('.jpg', '.jpeg'):
        im: Image = Image.open(source_file)
        im = im.convert('RGB')
        ext_format = '.jpg'
        source_file = os.path.join(source_file_dir, source_file_name + ext_format)
        im.save(source_file)
        print('png格式转为jpg，source_file：{}'.format(source_file))
    file_size_b = os.path.getsize(source_file)
    if file_size_b <= target_file_size_b:
        return source_file, file_size_b
    if not target_file:
        target_file = os.path.join(source_file_dir, source_file_name + '_compressed' + ext_format)
    im: Image = Image.open(source_file)
    while file_size_b > target_file_size_b:
        im.save(target_file, quality=quality, optimize=True)
        if quality - step < 0:
            break
        quality -= step
        file_size_b = os.path.getsize(target_file)
        # print(quality, file_size_b)
    return target_file, file_size_b
