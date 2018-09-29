from config import get_config

import tensorflow as tf
import numpy as np
import argparse
import cv2

import model
import util

# Configuration
config, _ = get_config()

np.random.seed(config.seed)
tf.set_random_seed(config.seed)


parser = argparse.ArgumentParser()
parser.add_argument('--src_image', type=str, default='./sample.png')
parser.add_argument('--dst_image', type=str, default='./sample-upscaled.png')
args = parser.parse_args()


def get_img(path):
    return cv2.imread(path, cv2.IMREAD_COLOR)[..., ::-1]  # BGR to RGB


def main():
    # load src image
    src_img = get_img(args.src_image)

    # gpu config
    gpu_config = tf.GPUOptions(allow_growth=True)
    tf_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False, gpu_options=gpu_config)

    with tf.Session(config=tf_config) as sess:
        rcan_model = model.RCAN(sess=sess,
                                batch_size=config.batch_size,
                                img_scaling_factor=config.image_scaling_factor,
                                n_res_blocks=config.n_res_blocks,
                                n_res_groups=config.n_res_groups,
                                res_scale=config.res_scale,
                                n_filters=config.filter_size,
                                kernel_size=config.kernel_size,
                                activation=config.activation,
                                use_bn=config.use_bn,
                                reduction=config.reduction,
                                optimizer=config.optimizer,
                                lr=config.lr,
                                lr_decay=config.lr_decay,
                                lr_decay_step=config.lr_decay_step,
                                momentum=config.momentum,
                                beta1=config.beta1,
                                beta2=config.beta2,
                                opt_eps=config.opt_epsilon,
                                tf_log=config.summary,
                                )

        # Initializing
        sess.run(tf.global_variables_initializer())

        # Load model & Graph & Weights
        ckpt = tf.train.get_checkpoint_state(config.summary)
        if ckpt and ckpt.model_checkpoint_path:
            rcan_model.saver.restore(sess, ckpt.model_checkpoint_path)
        else:
            raise OSError("[-] No checkpoint file found")

        # feed_dict
        feed = {
            rcan_model.x_lr: np.reshape(src_img, (1,) + rcan_model.lr_img_size),  # (1, 96, 96, 3)
            rcan_model.lr: config.lr,  # dummy
        }

        # get result
        output = sess.run(rcan_model.output, feed_dict=feed)
        output = np.reshape(output, (1,) + rcan_model.hr_img_size)  # (1, 384, 384, 3)

        # save result
        util.save_image(output, (1, 1), args.dst_image)


if __name__ == "__main__":
    main()
