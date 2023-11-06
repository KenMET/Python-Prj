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

(train_data, train_labels), (test_data, test_labels) = tf.keras.datasets.imdb.load_data(num_words=10000)
print("Training entries: %d, labels: %d"%(len(train_data), len(train_labels)))

# 一个映射单词到整数索引的词典
word_list = tf.keras.datasets.imdb.get_word_index()
# 保留第一个索引
word_list = {k:(v+3) for k,v in word_list.items()}
word_list["<PAD>"] = 0
word_list["<START>"] = 1
word_list["<UNK>"] = 2  # unknown
word_list["<UNUSED>"] = 3

reverse_word_list = dict([(value, key) for (key, value) in word_list.items()])

def decode_review(text):
    return ' '.join([reverse_word_list.get(i, '?') for i in text])

#print (decode_review(train_data[2]))

# 使用 pad_sequences 函数来使长度标准化, 因为模型需要统一的输入
train_data = tf.keras.preprocessing.sequence.pad_sequences( train_data,
                                                            value=word_list["<PAD>"],
                                                            padding='post',
                                                            maxlen=256)
test_data = tf.keras.preprocessing.sequence.pad_sequences(  test_data,
                                                            value=word_list["<PAD>"],
                                                            padding='post',
                                                            maxlen=256)

vocab_size = 10000

model = tf.keras.Sequential()
# 第一层是嵌入（Embedding）层。该层采用整数编码的词汇表，并查找每个词索引的嵌入向量（embedding vector）。
# 这些向量是通过模型训练学习到的。向量向输出数组增加了一个维度。得到的维度为：(batch, sequence, embedding)。
model.add(tf.keras.layers.Embedding(vocab_size, 16))

# GlobalAveragePooling1D 将通过对序列维度求平均值来为每个样本返回一个定长输出向量。
# 这允许模型以尽可能最简单的方式处理变长输入。
model.add(tf.keras.layers.GlobalAveragePooling1D())

model.add(tf.keras.layers.Dense(32, activation='relu'))
# 最后一层与单个输出结点密集连接。使用 Sigmoid 激活函数，其函数值为介于 0 与 1 之间的浮点数，表示概率或置信度。
model.add(tf.keras.layers.Dense(1, activation='sigmoid'))
model.summary()

# 一般来说 binary_crossentropy 更适合处理概率——它能够度量概率分布之间的"距离"
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# 从原始训练数据中分离 10,000 个样本来创建一个验证集
x_val = train_data[:10000]
partial_x_train = train_data[10000:]
y_val = train_labels[:10000]
partial_y_train = train_labels[10000:]


# 以 512 个样本的 mini-batch 大小迭代 40 个 epoch 来训练模型
# 并监测来自验证集的 10,000 个样本上的损失值（loss）和准确率（accuracy）
history = model.fit(partial_x_train, partial_y_train,
                    epochs=40, batch_size=512,
                    validation_data=(x_val, y_val), verbose=1)

# 评估模型， 将返回两个值。损失值（loss）（一个表示误差的数字，值越低越好）与准确率（accuracy）。
results = model.evaluate(test_data,  test_labels, verbose=2)
print(results)

model.save(os.path.join(py_dir, 'model'))

# 创建一个准确率（accuracy）和损失值（loss）随时间变化的图表
history_dict = history.history
acc = history_dict['accuracy']
val_acc = history_dict['val_accuracy']
loss = history_dict['loss']
val_loss = history_dict['val_loss']

epochs = range(1, len(acc) + 1)

fig = plt.figure(figsize=(10,10))
# “bo”代表 "蓝点"
plt.plot(epochs, loss, 'bo', label='Training loss')
# b代表“蓝色实线”
plt.plot(epochs, val_loss, 'b', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
fig.savefig('model_accuracy_and_loss.png', facecolor='white')