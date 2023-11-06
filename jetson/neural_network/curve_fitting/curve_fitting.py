# TensorFlow and tf.keras
import tensorflow as tf

# Helper libraries
import numpy as np
import matplotlib.pyplot as plt

import os, sys
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]

print(tf.__version__)

def data_create(curve_type='sin', total=10, random_err=1):
    if curve_type == 'sin':
        x = np.linspace(0, 2 * 2, total)     # 5 cycle at top "np.random.randint(1, 5)"
        y = np.sin(np.pi * x) * total + (np.random.ranf()-0.5) * random_err
    elif curve_type == 'straight':
        x_1 = np.linspace(0, total//2, int(total*0.4))
        y_1 = x_1 + np.random.randn(int(total*0.4)) * random_err
        x_2 = np.linspace(total//2, total, int(total*0.6))
        y_2 = total - x_2 + np.random.randn(int(total*0.6)) * random_err
        x = np.append(x_1, x_2)
        y = np.append(y_1, y_2)
    return x, y

def model_create():
    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.Dense(1, input_shape=(1, ), activation='relu'))
    model.add(tf.keras.layers.Dense(128, activation='relu'))
    model.add(tf.keras.layers.Dense(1024, activation='relu'))
    #model.add(tf.keras.layers.Dropout(0.2))
    model.add(tf.keras.layers.Dense(1))
    return model

def main():
    x, y = data_create(curve_type='sin', total=200, random_err=5)
    #x, y = data_create(curve_type='straight', total=200, random_err=1)

    model = model_create()
    model.compile(optimizer='adam', loss='mse')
    model.fit(x, y, epochs=5000)
    model.save(os.path.join(py_dir, 'model'))

    fig = plt.figure(figsize=(10,10))
    plt.scatter(x, y, c='r')
    plt.plot(x, model.predict(x))
    
    plt.xlabel('x - label', fontdict={'color':'red', 'size':20})
    plt.ylabel('y - label', fontdict={'color':'green', 'size':20})
    plt.xticks(size=20)
    plt.yticks(size=20)
    fig.savefig('curve.png', facecolor='white')


if __name__ == '__main__':
    main()
