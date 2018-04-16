import tensorflow as tf
from Model import Model
import time
import numpy
import string
import random
class NeuralNetwork:
    def BuildAndTrainModel(self, dataTable, steps, print_step, alpha, beta):
        # alpha : constant used in gradient descent, which represents how much to descend at each step
        # beta  : constant associated with the number of nodes in hidden layer. The larger beta represents the fewer nodes
        self.initializeModel(dataTable, beta)
        self.trainModelAndPrintResult(dataTable, steps, print_step, alpha)

    def initializeModel(self, dataTable, beta):
        searchList = dataTable.searchList
        self.constructW2VDict(dataTable)
        W2VDict = self.W2VDict
        s = Model.s
        s[2] = 2
        s[1] = max(int(len(searchList) / (beta * (s[0] + s[2]))), 1)
        print("layer size :", s)
        self.x_data = []
        self.y_data = []
        
        for search in searchList:
            x = [[0] for i in range(s[0]+1)]
            x[0] = [1]
            x[W2VDict[search.x.word] + 1] = [1]
            self.x_data.append(x)
            self.y_data.append(search.y)
        for i in range(len(s)-1):
            Model.theta[i] = numpy.random.random((s[i+1], s[i]+1)).tolist()
            
    def trainModelAndPrintResult(self, dataTable, steps, print_step, alpha):
        start_time = time.time()
        searchList = dataTable.searchList
        m = len(searchList)
        s = Model.s
        x_data = self.x_data
        y_data = self.y_data

        theta0_data = [Model.theta[0]]
        theta1_data = [Model.theta[1]]
        
        theta0 = tf.Variable(theta0_data)   # size : s[1] * (s[0]+1)
        theta1 = tf.Variable(theta1_data)   # size : s[2] * (s[1]+1)
        
        theta0 = tf.concat([theta0 for i in range(m)], 0)
        theta1 = tf.concat([theta1 for i in range(m)], 0)
        
        x = tf.placeholder(tf.float32, name = "x", shape = (m, s[0]+1, 1))      # size : m * (s[0] + 1) * 1
        y = tf.placeholder(tf.float32, name = "y", shape = (m, s[2], 1))      # size : m * s[2] * 1
        
        a = tf.sigmoid(-tf.matmul(theta0, x))                               # size : m * s[1] * 1
        bias_unit = [[[1]] for i in range(m)]                               # size : m * 1 * 1
        a = tf.concat([bias_unit, a], 1)                                    # size : m * (s[1] + 1) * 1
        h = tf.sigmoid(-tf.matmul(theta1, a), name = "h")                   # size : m * s[2] * 1
        J = -tf.reduce_sum(y * tf.log(tf.clip_by_value(h, 1e-8, 1.))
                   + (1 - y) * tf.log(tf.clip_by_value(1 - h, 1e-8, 1.))) / m   # scalar
        optimizer = tf.train.GradientDescentOptimizer(alpha)
        train = optimizer.minimize(J)
        
        sess = tf.Session()
        init = tf.global_variables_initializer()
        sess.run(init)
        
        running_time = - time.time()
        print("Step :\t", str(0), "\ttime : ", time.time() - start_time)
        for step in range(steps):
            sess.run(train, {x: x_data, y: y_data})
        
            if (step + 1) % print_step == 0:
                print("step :\t", str(step + 1), "\ttime : ", time.time() - start_time)
                print("step :",step + 1, " J :", sess.run(J, {x: x_data, y: y_data}))
        
        print("Done! Time : ", time.time() - start_time)
        running_time += time.time()
        
        Model.theta[0] = sess.run(theta0)
        Model.theta[1] = sess.run(theta1)
        
        [y_result, h_result, J_result] = sess.run([y, h, J], {x : x_data, y : y_data})
        print("\nx\ty\th")
        for i in range(len(searchList)):
            print(searchList[i].x.word, "=", x_data[i], "\t", ' '.join(map(str, y_result[i])), "\t", ' '.join(map(str, h_result[i])))
        print("J :", J_result)
        print("total running time :", running_time)
        
    def constructW2VDict(self, dataTable):  # Word2Vec Dictionary
        self.W2VDict = dict()
        W2VDict = self.W2VDict
        i = -1
        for search in dataTable.searchList:
            word = search.x.word
            if (not (word in W2VDict)):
                i += 1
                W2VDict[word] = i
        Model.s[0] = len(W2VDict)

 
class DataTable:
    def randomGenerate(self, num_example, length, example_inflate = 1, chars = string.ascii_uppercase + string.digits):
        # num_example : number of different examples, example_inflate : represents how many duplicate of each inputs are there
        for i in range(num_example):
            x = ''.join(random.choice(chars) for _ in range(length))
            y = [[0], [1]]
            random.shuffle(y)
            for j in range(example_inflate):
                self.add(x, y)
    def add(self, word, y):
        self.searchList.append(Search(Query(word), y))
    def __init__(self):
        self.searchList = []
        
class Search:
    def __init__(self, x, y):
        self.x = x
        self.y = y
class Query:
    def __init__(self, word):
        self.word = word
        
dataTable = DataTable()
dataTable.randomGenerate(num_example = 500, length = 3, example_inflate = 10)
NN = NeuralNetwork()
NN.constructW2VDict(dataTable)
NN.BuildAndTrainModel(dataTable, 200, 10, 2, 2)