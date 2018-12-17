import tensorflow as tf


class Inputs(object):
    def __init__(self, names, datatype=tf.float32, variable_scope="inputs"):
        self._names = names
        self._datatype = datatype
        self._variable_scope = variable_scope

        self._placeholders_list = []
        self._placeholders_dict = {}
        with tf.variable_scope(variable_scope):
            for name in names:
                placeholder = tf.placeholder(
                    dtype=self._datatype, shape=(None, ), name=name)
                self._placeholders_list.append(placeholder)
                self.placeholders_dict[name] = placeholder

            self._placeholders = tf.stack(self._placeholders_list, axis=1)

    @property
    def names(self):
        return self._names

    @names.setter
    def names(self, x):
        raise Exception('Variable can not be set.')

    @property
    def datatype(self):
        return self._datatype

    @datatype.setter
    def datatype(self, x):
        raise Exception('Variable can not be set.')

    @property
    def placeholders(self):
        return self._placeholders

    @placeholders.setter
    def placeholders(self, x):
        raise Exception('Variable can not be set.')

    @property
    def placeholders_dict(self):
        return self._placeholders_dict

    @placeholders_dict.setter
    def placeholders_dict(self, x):
        raise Exception('Variable can not be set.')

    @property
    def variable_scope(self):
        return self._variable_scope

    @variable_scope.setter
    def variable_scope(self, x):
        raise Exception('Variable can not be set.')
