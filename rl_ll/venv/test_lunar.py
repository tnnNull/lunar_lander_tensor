
import gym
import tensorflow as tf
import tensorflow.contrib.slim as slim
from tensorflow.python.saved_model import tag_constants
import numpy as np
#import matplotlib.pyplot as plt

try:
    xrange = xrange
except:
    xrange = range

env = gym.make('LunarLander-v2')

gamma = 0.99  # коэффициент дисконтирования


def discount_rewards(r):
    """ принимая на вход вектор выигришей,
    вернуть вектор дисконтированных выигрышей"""
    discounted_r = np.zeros_like(r)
    running_add = 0
    for t in reversed(xrange(0, r.size)):
        running_add = running_add * gamma + r[t]
        discounted_r[t] = running_add
    return discounted_r


class agent():
    def __init__(self, lr, s_size, a_size, h_size):
        # Ниже инициализирована feed-forward часть нейросети.
        # Агент оценивает состояние среды и совершает действие
        self.state_in = tf.placeholder(shape=[None, s_size], dtype=tf.float32)
        hidden = slim.fully_connected(self.state_in, h_size,
                                      biases_initializer=None, activation_fn=tf.nn.relu)
        hidden_2 = slim.fully_connected(hidden, h_size,
                                      biases_initializer=None, activation_fn=tf.nn.relu)
        self.output = slim.fully_connected(hidden_2, a_size,
                                           activation_fn=tf.nn.softmax, biases_initializer=None)
        self.chosen_action = tf.argmax(self.output, 1)  # выбор действия

        # Следующие 6 строк устанавливают процедуру обучения.
        # Нейросеть принимает на вход выбранное действие
        # и соответствующий выигрыш,
        # чтобы оценить функцию потерь и обновить веса модели.
        self.reward_holder = tf.placeholder(shape=[None], dtype=tf.float32)
        self.action_holder = tf.placeholder(shape=[None], dtype=tf.int32)

        self.indexes = tf.range(0,
                                tf.shape(self.output)[0]) * tf.shape(self.output)[1] + self.action_holder

        self.responsible_outputs = tf.gather(tf.reshape(self.output, [-1]),
                                             self.indexes)
        # функция потерь
        self.loss = -tf.reduce_mean(tf.log(self.responsible_outputs) *
                                    self.reward_holder)

        tvars = tf.trainable_variables()
        self.exported = tf.trainable_variables()
        self.gradient_holders = []
        for idx, var in enumerate(tvars):
            placeholder = tf.placeholder(tf.float32, name=str(idx) + '_holder')
            self.gradient_holders.append(placeholder)

        self.gradients = tf.gradients(self.loss, tvars)

        optimizer = tf.train.AdamOptimizer(learning_rate=lr)
        self.update_batch = optimizer.apply_gradients(zip(self.gradient_holders,
                                                          tvars))


tf.reset_default_graph()  # Очищаем граф tensorflow

myAgent = agent(lr=1e-2, s_size=8, a_size=4, h_size=64)  # Инициализируем агента
saver = tf.train.Saver()


total_episodes = 100  # Количество итераций обучения
max_ep = 999
i = 0

init = tf.global_variables_initializer()

# Запуск графа tensorflow
with tf.Session() as sess:
    sess.run(init)
    saver.restore(sess, "/home/vitaly/PycharmProjects/rl_ll/weights_to_test/model.ckpt")
    print("Model restored.")
    all_reward = 0
    while i < total_episodes:
        s = env.reset()

        running_reward = 0
        for j in range(max_ep):
            #env.render()
            # Выбрать действие на основе вероятностей, оцененных нейросетью
            a = np.argmax(sess.run(myAgent.output, feed_dict={myAgent.state_in: [s]}))
            s, r, d, n = env.step(a)
            running_reward += r
            if d:
                break
        print('At: ', i, ' from ', running_reward)
        all_reward+=running_reward
        i+=1
print("-----Mean reward: ", all_reward / total_episodes, ' from episode ', i, '/',total_episodes)
