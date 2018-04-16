#####################################################################################################################
'''
similar search_query implementation
'''
#####################################################################################################################

import tensorflow as tf
import numpy as np
import random
import time
import matplotlib.pyplot as plt

# from tensorflow.examples.tutorials.mnist import input_data

tf.set_random_seed(2017)  # reproducibility

# mnist = input_data.read_data_sets("MNIST_data/", one_hot=True)
data = np.loadtxt("query-probability.csv", delimiter=",", dtype=np.float32)

N = len(data)

train_x_data = data[0:(N*0.8), 0:-1]
train_y_data = tf.one_hot(indices=data[0:(N*0.8), [-1]], depth=3)
test_x_data = data[(N*0.8):, 0:-1]
test_y_data = tf.one_hot(indices=data[(N*0.8):, 0:-1], depth=3)

# parameters
learning_rate = 0.001
training_epochs = 10
batch_size = 100
hidden_parameter_1 = 6
hidden_parameter_2 = 8

# input place holders
X = tf.placeholder(tf.float32, [None, 4])
Y = tf.placeholder(tf.float32, [None, 3])

# dropout (keep_prob) rate  0.7 on training, but should be 1 for testing
keep_prob = tf.placeholder(tf.float32)

#####################################################################################################################
# weights & bias for nn layers
W1 = tf.get_variable("W1", shape=[4, hidden_parameter_1],
                     initializer=tf.contrib.layers.xavier_initializer())
b1 = tf.Variable(tf.random_normal([hidden_parameter_1]))
L1 = tf.nn.relu(tf.matmul(X, W1) + b1)
L1 = tf.nn.dropout(L1, keep_prob=keep_prob)

W2 = tf.get_variable("W2", shape=[hidden_parameter_1, hidden_parameter_2],
                     initializer=tf.contrib.layers.xavier_initializer())
b2 = tf.Variable(tf.random_normal([hidden_parameter_2]))
L2 = tf.nn.relu(tf.matmul(L1, W2) + b2)
L2 = tf.nn.dropout(L2, keep_prob=keep_prob)

W3 = tf.get_variable("W3", shape=[hidden_parameter_2, hidden_parameter_2],
                     initializer=tf.contrib.layers.xavier_initializer())
b3 = tf.Variable(tf.random_normal([hidden_parameter_2]))
L3 = tf.nn.relu(tf.matmul(L2, W3) + b3)
L3 = tf.nn.dropout(L3, keep_prob=keep_prob)

W4 = tf.get_variable("W4", shape=[hidden_parameter_2, hidden_parameter_1],
                     initializer=tf.contrib.layers.xavier_initializer())
b4 = tf.Variable(tf.random_normal([hidden_parameter_1]))
L4 = tf.nn.relu(tf.matmul(L3, W4) + b4)
L4 = tf.nn.dropout(L4, keep_prob=keep_prob)

W5 = tf.get_variable("W5", shape=[hidden_parameter_1, 3],
                     initializer=tf.contrib.layers.xavier_initializer())
b5 = tf.Variable(tf.random_normal([3]))
hypothesis = tf.matmul(L4, W5) + b5

#####################################################################################################################

# define cost/loss & optimizer
cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=hypothesis, labels=Y))
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)

# initialize
sess = tf.Session()
sess.run(tf.global_variables_initializer())


def next_batch(num, _data, _labels):
    # Return a total of `num` random samples and labels.
    idx = np.arange(0, len(_data))
    np.random.shuffle(idx)
    idx = idx[:num]
    data_shuffle = [_data[i] for i in idx]
    labels_shuffle = [_labels[i] for i in idx]

    return np.asarray(data_shuffle), np.asarray(labels_shuffle)


print('Learning Started')
begin_time = time.time()

# train my model
for epoch in range(training_epochs):
    avg_cost = 0
    total_batch = int(N / batch_size)

    for i in range(total_batch):
        batch_xs, batch_ys = next_batch(batch_size, train_x_data, train_y_data)
        feed_dict = {X: batch_xs, Y: batch_ys, keep_prob: 0.7}
        c, _ = sess.run([cost, optimizer], feed_dict=feed_dict)
        avg_cost += c / total_batch

    print('Epoch:', '%02d' % (epoch + 1), 'cost =', '{:.6f}'.format(avg_cost))

print('Learning Finished')
end_time = time.time()

print('begin_time: ', end=' ')
print(begin_time)
print('end_time: ', end=' ')
print(end_time)
print('running time: ', end=' ')
print(end_time - begin_time)

# Test model and check accuracy
correct_prediction = tf.equal(tf.argmax(hypothesis, 1), tf.argmax(Y, 1))
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
print('Accuracy:', sess.run(accuracy, feed_dict={X: test_x_data, Y: test_y_data, keep_prob: 1}))
