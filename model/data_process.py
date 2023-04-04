import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage
import multiprocessing as mp
import os
import cv2
import torch
import torchvision


def read_alphabets(alphabet_directory_path, alphabet_directory_name):
    """
    Reads all the characters from a given alphabet_directory
    """
    datax = []
    datay = []
    characters = os.listdir(alphabet_directory_path)
    for character in characters:
        images = os.listdir(alphabet_directory_path + character + '/')
        for img in images:
            image = cv2.resize(
                cv2.imread(alphabet_directory_path + character + '/' + img),
                (28, 28)
            )
            # 不数据增广
            datax.append((image))
            datay.append((alphabet_directory_name + '_' + character))
    #             #rotations of image 旋转继续宁data augmentation
    #             rotated_90 = ndimage.rotate(image, 90)
    #             rotated_180 = ndimage.rotate(image, 180)
    #             rotated_270 = ndimage.rotate(image, 270)
    #             #data augmentation 将旋转后的数据训练集，并赋予相应标签
    #             datax.extend((image, rotated_90, rotated_180, rotated_270))

    #             datay.extend((
    #                 alphabet_directory_name + '_' + character + '_0',
    #                 alphabet_directory_name + '_' + character + '_90',
    #                 alphabet_directory_name + '_' + character + '_180',
    #                 alphabet_directory_name + '_' + character + '_270'
    #             ))

    return np.array(datax), np.array(datay)


def read_images(base_directory):
    """
    Reads all the alphabets from the base_directory
    Uses multithreading to decrease the reading time drastically
    """
    datax = None
    datay = None
    # multi_process, do not work on windows
    #     pool = mp.Pool(mp.cpu_count())
    #     results = [pool.apply(read_alphabets,
    #                           args=(
    #                               base_directory + '/' + directory + '/', directory,
    #                               )) for directory in os.listdir(base_directory)]
    #     pool.close()
    results = [read_alphabets(base_directory + '/' + directory + '/', directory,
                              ) for directory in os.listdir(base_directory)]
    for result in results:
        if datax is None:
            datax = result[0]
            datay = result[1]
        else:
            datax = np.vstack([datax, result[0]])
            datay = np.concatenate([datay, result[1]])
    return datax, datay


def read_mini(directory_path):
    """
    read mini_imagenet
    """
    datax = []
    datay = []
    dirs = os.listdir(directory_path)
    for dir in dirs:
        images = os.listdir(directory_path + dir + '/')
        for img in images:
            image = cv2.imread(directory_path + dir + '/' + img)
#             image = cv2.cvtColor(directory_path + dir + '/' + img,
#                                  cv2.COLOR_BAYER_BG2BGR)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            datax.append((image))
            datay.append((directory_path + dir))
    return np.array(datax), np.array(datay)

def read_mini_images(directory):
    datax = None
    datay = None
    datax, datay = read_mini(directory)
    return datax, datay


def extract_sample(n_way, n_support, n_query, datax, datay):
    """
    Picks random sample of size n_support+n_querry, for n_way classes
    Args:
      n_way (int): number of classes in a classification task
      n_support (int): number of labeled examples per class in the support set
      n_query (int): number of labeled examples per class in the query set
      datax (np.array): dataset of images
      datay (np.array): dataset of labels
    Returns:
      (dict) of:
        (torch.Tensor): sample of images. Size (n_way, n_support+n_query, (dim))
        (int): n_way
        (int): n_support
        (int): n_query
    """
    sample = []
    # 随机抽取n_way个标签类别，每个标签有20张图
    K = np.random.choice(np.unique(datay), n_way, replace=False)
    for cls in K:
        # 拿出每个标签内的20张图, 即，只拿出 标签==随机抽取的cls中的标签 的那20张
        # datay == cls 是一个77120 * 1的矩阵，其中只有标签相等位置为True，会被拿出，python语法！！
        datax_cls = datax[datay == cls]
        # 随机打乱
        perm = np.random.permutation(datax_cls)
        # 取前support set中每类图片数+query set每类图片数 张图片，分别作为se和qe
        sample_cls = perm[:(n_support+n_query)]
        # sample是一个五维数组，第一维可以理解为目前class的数量
        sample.append(sample_cls)
    sample = np.array(sample)
    sample = torch.from_numpy(sample).float()
    # 将维度打乱为e.g.8个task [8, 10, 3, 28, 28], but why?
    sample = sample.permute(0,1,4,2,3)
    return({
      'images': sample,
      'n_way': n_way,
      'n_support': n_support,
      'n_query': n_query,
      'class_name': K
      })

def display_sample(sample):
    """
    Displays sample in a grid
    Args:
      sample (torch.Tensor): sample of images to display
    """
    # need 4D tensor to create grid, currently 5D
    sample_4D = sample.view(sample.shape[0]*sample.shape[1],*sample.shape[2:])
    # make a grid
    # 每行10张图片
    out = torchvision.utils.make_grid(sample_4D, nrow=sample.shape[1])
    plt.figure(figsize = (16,7))
    plt.imshow(out.permute(1, 2, 0).numpy().astype(np.uint8) / 255)
    plt.savefig('test')
    return out.permute(1, 2, 0).numpy().astype(np.uint8) / 255

def display_support_query(sam):
    support = sam['n_support']
    query = sam['n_query']
    sam_support = sam['images'][:, :support]
    sam_query = sam['images'][:, support:]
    print(sam['class_name'])
    support_4D = sam_support.reshape(sam_support.shape[0] * sam_support.shape[1],
                              *sam_support.shape[2:])
    out_support = torchvision.utils.make_grid(support_4D, nrow = sam_support.shape[1])
    query_4D = sam_query.reshape(sam_query.shape[0] * sam_query.shape[1],
                             *sam_query.shape[2:])
    out_query = torchvision.utils.make_grid(query_4D, nrow = sam_query.shape[1])
    print('draw_success')
    # fig = plt.figure(figsize=(16, 7))
    # ax1 = fig.add_subplot(1, 2, 1)
    # ax2 = fig.add_subplot(1, 2, 2)
    # ax1.imshow(out_support.permute(1, 2, 0).numpy().astype(np.uint8))
    # ax2.imshow(out_query.permute(1, 2, 0).numpy().astype(np.uint8))
    return out_support, out_query

# 输出预测的label名
def label_predicted_transfer(output, sample):
    y_hat = output['y_hat']
    y_hat = y_hat.cpu()
    y_hat = y_hat.numpy()
    class_names = sample['class_name']
    labels = []
    # 以y_hat的每一行为索引,找出预测结果对应的label名
    for indice in y_hat:
        for string in class_names[indice]:
            # 分割出最后一个/后的字段,即label名
            label = string.split('/')[-1]
            labels.append(label)
    labels = np.array(labels)
    labels = labels.reshape(5, 5)
    return labels

# 输出本次正确的类名
def label_transfer(sample):
    class_names = sample['class_name']
    labels = []
    for string in class_names:
        label = string.split('/')[-1]
        labels.append(label)
    labels = np.array(labels)
    return labels