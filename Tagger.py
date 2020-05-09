from tensorflow.keras.applications.resnet_v2 import ResNet50V2
from tensorflow.keras.preprocessing import image as tf_image
from tensorflow.keras.applications.resnet_v2 import decode_predictions, preprocess_input
from tensorflow.keras.layers import Input

import numpy as np
import piexif.helper
import os
import time


class Tagger:

    #os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

    input_image_size = (400, 400, 3)
    input_tensor = Input(shape=input_image_size)

    model = ResNet50V2(weights='imagenet', include_top=True, input_tensor=input_tensor)

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

        f = open('labels.txt', 'w+')

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
            #TODO co to za próg 0.08?
            if float(translated_predictions[0][2]) - float(translated_predictions[1][2]) <= 0.08:
                res = [translated_predictions[0][1], translated_predictions[1][1]]
            else:
                res = [translated_predictions[0][1]]

        f.close()
        return res


    @staticmethod
    def tag_dir(directory):

        f = open('labels.txt', 'w+')
        i = 0

        time_start = time.time()
        for file_name in os.listdir(directory):
            if file_name.endswith('.jpeg') or file_name.endswith('.jpg'):
                img_path = directory + file_name
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
                if float(translated_predictions[0][2]) - float(translated_predictions[1][2]) <= 0.08:
                    print(file_name + " few labels have been found:  " + str([i[1] for i in translated_predictions]))

                    #Tagger.set_meta_tag(img_path, translated_predictions[0][1] + ', ' + translated_predictions[1][1])
                    f.write(
                        str(i) + '.  ' + str(file_name) + ' ' * 5 + '->  ' + str(translated_predictions[0][1]) + ', '
                        + str(translated_predictions[1][1]) + '\n')
                else:
                    print(file_name + " one label has been found:  " + str(translated_predictions[0][1]))
                    #Tagger.set_meta_tag(img_path, translated_predictions[0][1])
                    f.write(
                        str(i) + '.  ' + str(file_name) + ' ' * 5 + '->  ' + str(translated_predictions[0][1]) + '\n')
        f.close()
        print("Time: " + str(time.time() - time_start))


if __name__ == "__main__":

    Tagger.tag_file("images\\example_01.jpg")
