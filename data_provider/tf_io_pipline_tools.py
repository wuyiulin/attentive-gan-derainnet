#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 19-3-1 上午10:41
# @Author  : Luo Yao
# @Site    : http://icode.baidu.com/repos/baidu/personal-code/Luoyao
# @File    : tf_io_pipline_tools.py
# @IDE: PyCharm
"""
Some tensorflow records io tools
"""
import os
import os.path as ops

import cv2
import numpy as np
import tensorflow as tf
import glog as log

from context import global_config

CFG = global_config.cfg


def int64_feature(value):
    """

    :return:
    """
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))


def bytes_feature(value):
    """

    :param value:
    :return:
    """
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def morph_process(image):
    """
    图像形态学变化
    :param image:
    :return:
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (5, 5))
    close_image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    open_image = cv2.morphologyEx(close_image, cv2.MORPH_OPEN, kernel)

    return open_image


def write_example_tfrecords(rain_images_paths, clean_images_paths, tfrecords_path):
    """
    write tfrecords
    :param rain_images_paths:
    :param clean_images_paths:
    :param tfrecords_path:
    :return:
    """
    _tfrecords_dir = ops.split(tfrecords_path)[0]
    os.makedirs(_tfrecords_dir, exist_ok=True)

    log.info('Writing {:s}....'.format(tfrecords_path))

    with tf.python_io.TFRecordWriter(tfrecords_path) as _writer:
        for _index, _rain_image_path in enumerate(rain_images_paths):

            # prepare rain image
            _rain_image = cv2.imread(_rain_image_path, cv2.IMREAD_COLOR)
            _rain_image = cv2.resize(_rain_image,
                                     dsize=(CFG.TRAIN.IMG_WIDTH, CFG.TRAIN.IMG_HEIGHT),
                                     interpolation=cv2.INTER_LINEAR)
            _rain_image_raw = _rain_image.tostring()

            # prepare clean image
            _clean_image = cv2.imread(clean_images_paths[_index], cv2.IMREAD_COLOR)
            _clean_image = cv2.resize(_clean_image,
                                      dsize=(CFG.TRAIN.IMG_WIDTH, CFG.TRAIN.IMG_HEIGHT),
                                      interpolation=cv2.INTER_LINEAR)
            _clean_image_raw = _clean_image.tostring()

            # prepare mask image
            _diff_image = np.abs(np.array(_rain_image, np.float32) - np.array(_clean_image, np.float32))
            _diff_image = _diff_image.sum(axis=2)

            _mask_image = np.zeros(_diff_image.shape, np.float32)

            _mask_image[np.where(_diff_image >= 50)] = 1.
            _mask_image = morph_process(_mask_image)
            _mask_image = _mask_image.tostring()

            _example = tf.train.Example(
                features=tf.train.Features(
                    feature={
                        'rain_image_raw': bytes_feature(_rain_image_raw),
                        'clean_image_raw': bytes_feature(_clean_image_raw),
                        'mask_image_raw': bytes_feature(_mask_image)
                    }))
            _writer.write(_example.SerializeToString())

    log.info('Writing {:s} complete'.format(tfrecords_path))

    return


def decode(serialized_example):
    """
    Parses an image and label from the given `serialized_example`
    :param serialized_example:
    :return:
    """
    features = tf.parse_single_example(
        serialized_example,
        # Defaults are not specified since both keys are required.
        features={
            'rain_image_raw': tf.FixedLenFeature([], tf.string),
            'clean_image_raw': tf.FixedLenFeature([], tf.string),
            'mask_image_raw': tf.FixedLenFeature([], tf.string)
        })

    # set image shape
    image_shape = tf.stack([CFG.TRAIN.IMG_HEIGHT, CFG.TRAIN.IMG_WIDTH, 3])

    # decode rain image
    rain_image = tf.decode_raw(features['rain_image_raw'], tf.uint8)
    rain_image = tf.reshape(rain_image, image_shape)

    # decode clean image
    clean_image = tf.decode_raw(features['clean_image_raw'], tf.uint8)
    clean_image = tf.reshape(clean_image, image_shape)

    # decode mask image
    mask_image = tf.decode_raw(features['mask_image_raw'], tf.float32)
    mask_image_shape = tf.stack([CFG.TRAIN.IMG_HEIGHT, CFG.TRAIN.IMG_WIDTH, 1])
    mask_image = tf.reshape(mask_image, mask_image_shape)

    return rain_image, clean_image, mask_image


def augment_for_train(rain_image, clean_image, mask_image):
    """

    :param rain_image:
    :param clean_image:
    :param mask_image:
    :return:
    """
    return rain_image, clean_image, mask_image


def augment_for_validation(rain_image, clean_image, mask_image):
    """

    :param rain_image:
    :param clean_image:
    :param mask_image:
    :return:
    """
    return rain_image, clean_image, mask_image


def normalize(rain_image, clean_image, mask_image):
    """
    Normalize the image data by substracting the imagenet mean value
    :param rain_image:
    :param clean_image:
    :param mask_image:
    :return:
    """

    if rain_image.get_shape().as_list()[-1] != 3 or clean_image.get_shape().as_list()[-1] != 3:
        raise ValueError('Input must be of size [height, width, C>0]')

    rain_image_fp = tf.cast(rain_image, dtype=tf.float32)
    clean_image_fp = tf.cast(clean_image, dtype=tf.float32)

    rain_image_fp = tf.subtract(tf.divide(rain_image_fp, tf.constant(127.5, dtype=tf.float32)),
                                tf.constant(1.0, dtype=tf.float32))
    clean_image_fp = tf.subtract(tf.divide(clean_image_fp, tf.constant(127.5, dtype=tf.float32)),
                                 tf.constant(1.0, dtype=tf.float32))

    return rain_image_fp, clean_image_fp, mask_image