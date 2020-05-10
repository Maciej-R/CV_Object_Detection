from tensorflow.keras.applications.resnet_v2 import ResNet101V2
from tensorflow.keras.preprocessing import image as tf_image
from tensorflow.keras.applications.resnet_v2 import decode_predictions, preprocess_input
from tensorflow.keras.layers import Input

import numpy as np
import piexif.helper
import os
import tensorflow as tf
from threading import Thread
import DB


class Tagger:
    """
    This class is designed for image classification featuring ML and pretrained CNN model ResNet.
    """

    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

    input_image_size = (400, 400, 3)
    input_tensor = Input(shape=input_image_size)

    model = ResNet101V2(weights='imagenet', include_top=True, input_tensor=input_tensor)

    @staticmethod
    def set_meta_tag(file_path, comment):
        """
        Function sets label to an UserComment tag [EXIF metadata] of an image.

        :param file_path: Path to the file,
        :param comment: Value of a label
        """
        exif_dict = piexif.load(file_path)
        user_comment = piexif.helper.UserComment.dump(str(str(comment)))
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = user_comment
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, file_path)

    @staticmethod
    def tag_file(file_name):
        """
        This method classifies one given image.
        :param file_name: Path to the file, that should be classified.
        :return: Tags as list of strings
        """

        f = open('labels.txt', 'w+')

        res = []
        if file_name.endswith('.jpeg') or file_name.endswith('.jpg'):

            # preprocess an image
            img = tf_image.load_img(file_name, target_size=Tagger.input_image_size[:2])
            img = tf_image.img_to_array(img)
            img = np.expand_dims(img, axis=0)
            img = preprocess_input(img)
            # apply NN and make a prediction
            predictions = Tagger.model.predict(img)
            # decode the results into a list of tuples (class, description, probability)
            # (one such list for each sample in the batch)

            translated_predictions = decode_predictions(predictions, top=2)[0]

            if float(translated_predictions[0][2]) - float(translated_predictions[1][2]) <= 0.08:
                res = [translated_predictions[0][1], translated_predictions[1][1]]
                tf.keras.backend.print_tensor(Tagger.model.layers[-1].output)
            else:
                res = [translated_predictions[0][1]]

        f.close()
        return res

    @staticmethod
    def tag_dir(dir_path='./images', set_meta=False, file_log=False, nimgs=25):
        """
        Use ML to classify your images. Sets 1 or multi labels
        .jpg or .jpeg taken into account
        :param nimgs: Number of images per thread
        :param file_log: Create output file LABELS.TXT with labels
        :param set_meta: Set meta-tag with labeled class
        :param dir_path: Path to the directory where images for classification are located. Default: test_image_set file
        :return: Tuple: 1) list of strings with labels, tuples for multilabel; 2) names of tagged files
        """

        def thread_function(files_range, result):
            """Function for operations being executed inside a thread.

            :param files_range: Set on which files actions should be performed.
            :return:
            """
            if file_log:
                f = open('labels.txt', 'w+')
            i = 0

            for file_name in files_range:
                if file_name.endswith('.jpeg') or file_name.endswith('.jpg'):
                    img_path = dir_path + file_name
                    # preprocess an image
                    img = tf_image.load_img(img_path, target_size=Tagger.input_image_size[:2])
                    img = tf_image.img_to_array(img)
                    img = np.expand_dims(img, axis=0)
                    img = preprocess_input(img)

                    # apply NN and make a prediction
                    predictions = Tagger.model.predict(img)
                    # decode the results into a list of tuples (class, description, probability)
                    # (one such list for each sample in the batch)
                    i += 1
                    translated_predictions = decode_predictions(predictions, top=2)[0]
                    if float(translated_predictions[0][2]) <= 0.05:
                        result.append("")
                        if set_meta:
                            Tagger.set_meta_tag(img_path, 'none')
                        if file_log:
                            f.write(str(i) + '.  ' + str(file_name) + ' ' * 5 + '->  none\n')
                    else:
                        if float(translated_predictions[0][2]) - float(translated_predictions[1][2]) <= 0.08:
                            result.append((str(translated_predictions[0][1]), str(translated_predictions[1][1])))
                            if set_meta:
                                Tagger.set_meta_tag(img_path,
                                                    translated_predictions[0][1] + ', ' +
                                                    translated_predictions[1][1])
                            if file_log:
                                f.write(str(i) + '.  ' + str(file_name) + ' ' * 5 + '->  ' + str(
                                    translated_predictions[0][1]) + ', '
                                        + str(translated_predictions[1][1]) + '\n')
                        else:
                            result.append(str(translated_predictions[0][1]))
                            if set_meta:
                                Tagger.set_meta_tag(img_path, translated_predictions[0][1])
                            if file_log:
                                f.write(str(i) + '.  ' + str(file_name) + ' ' * 5 + '->  ' + str(
                                    translated_predictions[0][1]) + '\n')
            if file_log:
                f.close()
        #END thread_function

        if dir_path[-1] != '/':
            dir_path = dir_path + '/'

#       All files of proper format that are not included in database
        files = [name for name in os.listdir(dir_path) if
                 os.path.isfile(os.path.join(dir_path, name)) and (name.endswith('.jpeg') or name.endswith('.jpg'))
                 and not DB.DataBase.exists(pth=os.path.join(dir_path, name))]
        nfiles = len(files)

#       Number of threads to run, floor of float result - last thread handles any additional
        nthreads = nfiles // nimgs
#       nimgs > nfiles
        if nthreads == 0:
            nthreads = 1
#       Threads' function argument to handle results
        res = [[] for i in range(nthreads)]
#       Files' ranges for threads
        fargs = list()
        for i in range(nthreads):
            start = i * nimgs
#           Last thread handles additional files
            if i == nthreads - 1:
                fargs.append(files[start:])
            else:
                end = (i + 1) * nimgs - 1
                fargs.append(files[start:end])

#       Execute tasks
        thrds = [Thread(target=thread_function, args=[fargs[i], res[i]]) for i in range(nthreads)]
        for t in thrds:
            t.start()

        for t in thrds:
            t.join()

#       Threads' results to one list
        result = list()
        for r in res:
            for tags in r:
                result.append(tags)

        return result, files


if __name__ == "__main__":
    print(Tagger.tag_dir('images', False, False))
    #Tagger.tag_file("./images/example_01.jpg")
