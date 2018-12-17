import tensorflow as tf


class Outputs(object):
    def __init__(self, function, names, variable_scope="outputs"):
        self._names = names
        self._variable_scope = variable_scope

        if not function.shape[1] == len(names):
            raise Exception(
                'Shape of function does not match number of given names.')

        with tf.variable_scope(variable_scope):
            self._outputs_dict = {}
            for name, tensor in zip(names,
                                    tf.split(function, len(names), axis=1)):
                self._outputs_dict[name] = tf.identity(tensor, name=name)

    @property
    def names(self):
        return self._names

    @names.setter
    def names(self, x):
        raise Exception('Variable can not be set.')

    @property
    def variable_scope(self):
        return self._variable_scope

    @variable_scope.setter
    def variable_scope(self, x):
        raise Exception('Variable can not be set.')

    @property
    def outputs_dict(self):
        return self._outputs_dict

    @outputs_dict.setter
    def outputs_dict(self, x):
        raise Exception('Variable can not be set.')
