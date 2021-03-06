import math
import os
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from xml.etree.ElementTree import Element, SubElement


# TODO : Convert to class from this for saving project name(to reuse).

def check_and_create_directory(paths):
    for path in paths:
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)


def delete_directory(paths):
    for path in paths:
        shutil.rmtree(path)


def delete_file(path):
    os.remove(path)


def delete_files(paths):
    for path in paths:
        delete_file(path)


def insert_label(origin, labels):
    for label in labels:
        try:
            if origin.index(label) == 0:
                pass
        except ValueError:
            origin.append(label)

    return origin


def insert_image_sets(origin, label, image_file_name):
    origin[label].append(image_file_name)
    return origin


def make_project_directory(path, project):
    PROJECT_TEMP_PATH = os.path.join(path, project)
    folders = ['data', 'models', 'models/model', 'models/model/eval', 'models/model/train', 'dataset']

    check_and_create_directory([path, PROJECT_TEMP_PATH])

    for folder in folders:
        os.mkdir(os.path.join(PROJECT_TEMP_PATH, folder))

    return PROJECT_TEMP_PATH


def make_datasets_directory(path, project, dataset):
    PROJECT_TEMP_PATH = os.path.join(path, project)
    print(dataset)
    if dataset is not None:
        folders = ['dataset/' + dataset, 'dataset/' + dataset + '/Annotations',
                   'dataset/' + dataset + '/JPEGImages', 'dataset/' + dataset + '/ImageSets',
                   'dataset/' + dataset + '/ImageSets/Main']

        for folder in folders:
            os.mkdir(os.path.join(PROJECT_TEMP_PATH, folder))


def write_file(file_path, data):
    with open(file_path, 'wb') as file:
        file.write(data)


def move_file(original, destination):
    shutil.move(original, destination)


def make_label_map(labels):
    rslt = ''

    for idx, val in enumerate(labels):
        rslt += 'item { \n id: ' + str(idx + 1) + '\n name: \'' + val + '\'\n}\n\n'

    return rslt.encode('utf-8')


def make_image_sets(files):
    result = ''

    for val in files:
        result += val + '\n'

    return result.encode('utf-8')


def make_image_data(dataset, image, __labels):
    annotation = Element('annotation')
    SubElement(annotation, 'folder').text = dataset
    SubElement(annotation, 'filename').text = image['name']
    SubElement(annotation, 'segmented').text = image['segmented']

    source = Element('source')
    SubElement(source, 'database').text = 'The VOC2008 Database'
    SubElement(source, 'annotaion').text = 'PASCAL VOC2008'
    SubElement(source, 'image').text = '아'

    size = Element('size')
    SubElement(size, 'width').text = str(image['w'])
    SubElement(size, 'height').text = str(image['h'])
    SubElement(size, 'depth').text = '3'

    annotation.append(source)
    annotation.append(size)

    for __object in image['objects']:
        object_data, __labels = make_image_object(__object, image['name'], __labels)
        annotation.append(object_data)

    return ET.tostring(annotation, encoding='UTF-8', method='xml'), __labels


def make_image_object(__object, __file_name, __labels):
    object_data = Element('object')
    SubElement(object_data, 'name').text = __object['label']
    SubElement(object_data, 'pose').text = __object['pose']
    SubElement(object_data, 'truncated').text = str(__object['truncated'])
    SubElement(object_data, 'occluded').text = str(__object['occluded'])
    SubElement(object_data, 'difficult').text = str(__object['difficult'])

    bndbox = Element('bndbox')
    x_min, x_max, y_min, y_max = get_bnd_box(__object['polygons'])
    SubElement(bndbox, 'xmin').text = str(x_min)
    SubElement(bndbox, 'xmax').text = str(x_max)
    SubElement(bndbox, 'ymin').text = str(y_min)
    SubElement(bndbox, 'ymax').text = str(y_max)

    object_data.append(bndbox)

    __labels = insert_image_sets(__labels, __object['label'], __file_name)

    return object_data, __labels


def make_train_and_val(files):
    total_count = len(files)
    train_count = math.trunc(total_count * 0.8)
    trains = []
    vals = []
    for idx, val in enumerate(files):
        if idx < train_count:
            trains.append(val)
        else:
            vals.append(val)

    return trains, vals


def get_bnd_box(polygons):
    x_min = y_min = sys.maxsize
    x_max = y_max = 0
    for polygon in polygons:
        if polygon[0] < x_min:
            x_min = polygon[0]
        elif polygon[0] > x_max:
            x_max = polygon[0]

        if polygon[1] < y_min:
            y_min = polygon[1]
        elif polygon[1] > y_max:
            y_max = polygon[1]
    return x_min, x_max, y_min, y_max


def uncompress_files(original, destination):
    with zipfile.ZipFile(original) as zips:
        extract_path = os.path.join(destination)
        zips.extractall(extract_path)


def compress_files(original, destination):
    empty_dirs = []
    with zipfile.ZipFile(destination, 'w') as zips:
        for folder, subfolders, files in os.walk(original):
            empty_dirs.extend([os.path.relpath(os.path.join(folder, dirs), original) for dirs in subfolders if
                               not os.listdir(os.path.join(folder, dirs))])
            for file in files:
                zips.write(os.path.join(folder, file),
                           os.path.relpath(os.path.join(folder, file), original),
                           compress_type=zipfile.ZIP_DEFLATED)
        for dirs in empty_dirs:
            zif = zipfile.ZipInfo(dirs + "/")
            zips.writestr(zif, '')

    return destination
