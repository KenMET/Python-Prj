# TensorFlow and tf.keras
import tensorflow as tf

# Helper libraries
import numpy as np
import matplotlib.pyplot as plt
import random

import os, sys
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]

print(tf.__version__)

mnist = tf.keras.datasets.mnist
(train_images, train_lables), (test_images, test_lables) = mnist.load_data()

train_images = train_images / 255.0
test_images = test_images / 255.0

fig = plt.figure(figsize=(10,10))
for i in range(25):
    ax = plt.subplot(5, 5, i+1)
    plt.xticks([])
    plt.yticks([])
    plt.grid(False)
    plt.imshow(train_images[i], cmap=plt.cm.gray)
    ax.xaxis.label.set_color('green')
    plt.xlabel(train_lables[i])
fig.savefig('train.png', transparent=True)

model = tf.keras.models.Sequential()
model.add(tf.keras.layers.Flatten(input_shape=(28, 28)))
model.add(tf.keras.layers.Dense(128, activation='relu'))
model.add(tf.keras.layers.Dropout(0.2))
model.add(tf.keras.layers.Dense(10, activation='softmax'))

#loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

model.fit(train_images, train_lables, epochs=5)

model.summary()

test_loss, test_acc = model.evaluate(test_images,  test_lables, verbose=2)
print ('Test accuracy: ', test_acc)

model.save(os.path.join(py_dir, 'model'))


##########################################################################
def get_label_color(val1, val2):
    if val1 == val2:
        return 'green'
    else:
        return 'red'

model = tf.keras.models.load_model(os.path.join(py_dir, 'model'))
model.summary()

predictions = model.predict(test_images)
prediction_digits = np.argmax(predictions, axis=1)

fig = plt.figure(figsize=(10,10))
for i in range(25):
    ax = plt.subplot(5, 5, i+1)
    plt.xticks([])
    plt.yticks([])
    plt.grid(False)
    image_index = random.randint(0, len(prediction_digits))
    plt.imshow(test_images[image_index], cmap=plt.cm.gray)
    ax.xaxis.label.set_color(get_label_color(prediction_digits[image_index], test_lables[image_index]))
    plt.xlabel('Predicted: %d'%(prediction_digits[image_index]))
fig.savefig('test.png', transparent=True)
