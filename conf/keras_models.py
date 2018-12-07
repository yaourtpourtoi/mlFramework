from keras.models import Sequential
from keras.layers import *
from keras.optimizers import *
from keras.regularizers import l2
from theano.tensor import lt

def example(num_inputs, num_outputs):
    """
    Example Keras model
    """
    model = Sequential()
    model.add(
        Dense(
            10, kernel_initializer="glorot_normal", activation="relu", input_dim=num_inputs))
    model.add(Dense(num_outputs, kernel_initializer="glorot_uniform", activation="softmax"))
    model.compile(
        loss="categorical_crossentropy",
        optimizer=Adam(),
        metrics=[
            "categorical_accuracy",
        ])
    return model


def smhtt_simple(num_inputs, num_outputs):
    model = Sequential()
    model.add(
        Dense(
            100, kernel_initializer="glorot_normal", activation="tanh",
            input_dim=num_inputs))
    model.add(Dense(num_outputs, kernel_initializer="glorot_normal", activation="softmax"))
    model.compile(loss="mean_squared_error", optimizer=Nadam(), metrics=[])
    return model


def smhtt_mt(num_inputs, num_outputs):
    model = Sequential()
    model.add(
        Dense(
            300, kernel_initializer="glorot_normal", activation="tanh",
            kernel_regularizer=l2(1e-4),
            input_dim=num_inputs))
    model.add(
        Dense(
            300, kernel_initializer="glorot_normal", activation="tanh",
            kernel_regularizer=l2(1e-4)))
    model.add(
        Dense(
            300, kernel_initializer="glorot_normal", activation="tanh",
            kernel_regularizer=l2(1e-4)))
    model.add(
        Dense(
            num_outputs, kernel_initializer="glorot_normal", activation="softmax"))
    model.compile(loss="mean_squared_error", optimizer=Adam(), metrics=['accuracy'])
    return model


def smhtt_et(num_inputs, num_outputs):
    model = Sequential()
    model.add(
        Dense(
            1000, kernel_initializer="glorot_normal", activation="tanh",
            kernel_regularizer=l2(1e-4),
            input_dim=num_inputs))
    model.add(
        Dense(
            num_outputs, init="glorot_normal", activation="softmax"))
    model.compile(loss="mean_squared_error", optimizer=Nadam(), metrics=[])
    return model


def smhtt_tt(num_inputs, num_outputs):
    model = Sequential()
    model.add(
        Dense(
            300, kernel_initializer="glorot_normal", activation="tanh",
            kernel_regularizer=l2(1e-4),
            input_dim=num_inputs))
    model.add(
        Dense(
            300, kernel_initializer="glorot_normal", activation="tanh",
            kernel_regularizer=l2(1e-4)))
    model.add(
        Dense(
            300, kernel_initializer="glorot_normal", activation="tanh",
            kernel_regularizer=l2(1e-4)))
    model.add(
        Dense(
            num_outputs, kernel_initializer="glorot_normal", activation="softmax"))
    model.compile(loss="mean_squared_error", optimizer=Nadam(), metrics=[])
    return model


def smhtt_legacy(num_inputs, num_outputs):
    model = Sequential()
    model.add(
        Dense(
            300,
            kernel_initializer="glorot_normal",
            activation="relu",
            kernel_regularizer=l2(1e-4),
            input_dim=num_inputs))
    model.add(
        Dense(
            300,
            kernel_initializer="glorot_normal",
            activation="relu",
            kernel_regularizer=l2(1e-4)))
    model.add(
        Dense(
            300,
            kernel_initializer="glorot_normal",
            activation="relu",
            kernel_regularizer=l2(1e-4)))
    model.add(
        Dense(
            num_outputs,
            kernel_initializer="glorot_normal",
            activation="softmax"))
    model.compile(
        loss="mean_squared_error",
        optimizer=Adam(),
        metrics=[])
    return model

def smhtt_dropout(num_inputs, num_outputs):
    model = Sequential()

    for i, nodes in enumerate([200] * 2):
        if i == 0:
            model.add(Dense(nodes, input_dim=num_inputs))
        else:
            model.add(Dense(nodes))
        # model.add(BatchNormalization(axis=1))
        model.add(Activation("relu"))
        model.add(Dropout(0.5))

    model.add(Dense(num_outputs))
    model.add(Activation("softmax"))

    model.compile(loss="mean_squared_error", optimizer=Nadam(), metrics=['categorical_accuracy'])
    return model

def smhtt_dropout_tensorflow(input_placeholder, keras_model):
    weights = {}
    for layer in keras_model.layers:
        print("Layer: {}".format(layer.name))
        for weight, array in zip(layer.weights, layer.get_weights()):
            print("    weight, shape: {}, {}".format(weight.name,
                                                     np.array(array).shape))
            weights[weight.name] = np.array(array)

    w1 = tf.get_variable('w1', initializer=weights['dense_1/kernel:0'])
    b1 = tf.get_variable('b1', initializer=weights['dense_1/bias:0'])
    w2 = tf.get_variable('w2', initializer=weights['dense_2/kernel:0'])
    b2 = tf.get_variable('b2', initializer=weights['dense_2/bias:0'])
    w3 = tf.get_variable('w3', initializer=weights['dense_3/kernel:0'])
    b3 = tf.get_variable('b3', initializer=weights['dense_3/bias:0'])

    l1 = tf.nn.relu(tf.add(b1, tf.matmul(input_placeholder, w1)))
    l2 = tf.nn.relu(tf.add(b2, tf.matmul(l1, w2)))
    l3 = tf.nn.softmax(tf.add(b3, tf.matmul(l2, w3)))
    return l3
    
def smhtt_dropout_tanh(num_inputs, num_outputs):
    model = Sequential()

    for i, nodes in enumerate([200] * 2):
        if i == 0:
            model.add(Dense(nodes, kernel_regularizer=l2(1e-5), input_dim=num_inputs))
        else:
            model.add(Dense(nodes, kernel_regularizer=l2(1e-5)))
        model.add(Activation("tanh"))
        model.add(Dropout(0.3))

    model.add(Dense(num_outputs, kernel_regularizer=l2(1e-5)))
    model.add(Activation("softmax"))

    model.compile(loss="categorical_crossentropy", optimizer=Adam(lr=1e-4), metrics=['categorical_accuracy'])
    return model

def smhtt_dropout_tanh_tensorflow(input_placeholder, keras_model):
    weights = {}
    for layer in keras_model.layers:
        print("Layer: {}".format(layer.name))
        for weight, array in zip(layer.weights, layer.get_weights()):
            print("    weight, shape: {}, {}".format(weight.name,
                                                     np.array(array).shape))
            weights[weight.name] = np.array(array)

    w1 = tf.get_variable('w1', initializer=weights['dense_1/kernel:0'])
    b1 = tf.get_variable('b1', initializer=weights['dense_1/bias:0'])
    w2 = tf.get_variable('w2', initializer=weights['dense_2/kernel:0'])
    b2 = tf.get_variable('b2', initializer=weights['dense_2/bias:0'])
    w3 = tf.get_variable('w3', initializer=weights['dense_3/kernel:0'])
    b3 = tf.get_variable('b3', initializer=weights['dense_3/bias:0'])

    l1 = tf.tanh(tf.add(b1, tf.matmul(input_placeholder, w1)))
    l2 = tf.tanh(tf.add(b2, tf.matmul(l1, w2)))
    l3 = tf.nn.softmax(tf.add(b3, tf.matmul(l2, w3)))
    return l3    

def smhtt_dropout_selu(num_inputs, num_outputs):
    model = Sequential()

    for i, nodes in enumerate([200] * 2):
        if i == 0:
            model.add(Dense(nodes, kernel_regularizer=l2(1e-5), input_dim=num_inputs))
        else:
            model.add(Dense(nodes, kernel_regularizer=l2(1e-5)))
        model.add(Activation("selu"))
        model.add(Dropout(0.3))

    model.add(Dense(num_outputs, kernel_regularizer=l2(1e-5)))
    model.add(Activation("softmax"))

    model.compile(loss="categorical_crossentropy", optimizer=Adam(lr=1e-4), metrics=['categorical_accuracy'])
    return model

def smhtt_em(num_inputs, num_outputs):
    model = Sequential()
    model.add(
        Dense(
            300, kernel_initializer="glorot_normal", activation="relu",
            kernel_regularizer=l2(1e-4),input_dim=num_inputs) )
    model.add(
        Dense(
            300, kernel_initializer="glorot_normal", activation="relu",
            kernel_regularizer=l2(1e-4),input_dim=num_inputs) )
    model.add(
        Dense(
            300, kernel_initializer="glorot_normal", activation="relu",
            kernel_regularizer=l2(1e-4),input_dim=num_inputs) )
    model.add(
        Dense(
            num_outputs, kernel_initializer="glorot_normal", activation="softmax"))
    model.compile(loss="mean_squared_error", optimizer=Nadam(), metrics=[])
    return model

def smhtt_em_tensorflow(input_placeholder, keras_model):
    weights = {}
    for layer in keras_model.layers:
        print("Layer: {}".format(layer.name))
        for weight, array in zip(layer.weights, layer.get_weights()):
            print("    weight, shape: {}, {}".format(weight.name,
                                                     np.array(array).shape))
            weights[weight.name] = np.array(array)

    w1 = tf.get_variable('w1', initializer=weights['dense_1/kernel:0'])
    b1 = tf.get_variable('b1', initializer=weights['dense_1/bias:0'])
    w2 = tf.get_variable('w2', initializer=weights['dense_2/kernel:0'])
    b2 = tf.get_variable('b2', initializer=weights['dense_2/bias:0'])
    w3 = tf.get_variable('w3', initializer=weights['dense_3/kernel:0'])
    b3 = tf.get_variable('b3', initializer=weights['dense_3/bias:0'])
    w4 = tf.get_variable('w4', initializer=weights['dense_4/kernel:0'])
    b4 = tf.get_variable('b4', initializer=weights['dense_4/bias:0'])    

    l1 = tf.nn.relu(tf.add(b1, tf.matmul(input_placeholder, w1)))
    l2 = tf.nn.relu(tf.add(b2, tf.matmul(l1, w2)))
    l3 = tf.nn.relu(tf.add(b3, tf.matmul(l2, w3)))
    l4 = tf.nn.softmax(tf.add(b4, tf.matmul(l3, w4)))
    return l4
