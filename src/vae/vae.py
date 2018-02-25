# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 MIT Probabilistic Computing Project

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import numpy as np
import tensorflow as tf

# The TensorFlow implementation is based on:
#   https://github.com/hwalsuklee/tensorflow-mnist-VAE

def gaussian_MLP_encoder(x, n_hidden, n_output, keep_prob, reuse=None):
    """Gaussian MLP as encoder q(Z|X; \phi)."""
    with tf.variable_scope('gaussian_MLP_encoder', reuse=reuse):
        # Initializers.
        w_init = tf.contrib.layers.variance_scaling_initializer()
        b_init = tf.constant_initializer(0.)
        # 1st hidden layer.
        w0 = tf.get_variable('w0',
            [x.get_shape()[1], n_hidden], initializer=w_init)
        b0 = tf.get_variable('b0', [n_hidden], initializer=b_init)
        h0 = tf.matmul(x, w0) + b0
        h0 = tf.nn.elu(h0)
        h0 = tf.nn.dropout(h0, keep_prob)
        # 2nd hidden layer.
        w1 = tf.get_variable('w1',
            [h0.get_shape()[1], n_hidden], initializer=w_init)
        b1 = tf.get_variable('b1', [n_hidden], initializer=b_init)
        h1 = tf.matmul(h0, w1) + b1
        h1 = tf.nn.tanh(h1)
        h1 = tf.nn.dropout(h1, keep_prob)
        # Output layer.
        wo = tf.get_variable('wo',
            [h1.get_shape()[1], n_output * 2], initializer=w_init)
        bo = tf.get_variable('bo', [n_output * 2], initializer=b_init)
        gaussian_params = tf.matmul(h1, wo) + bo
        # The mean parameter is unconstrained.
        mean = gaussian_params[:, :n_output]
        # The standard deviation must be positive: parametrize with a
        # softplus and add a small epsilon for numerical stability.
        stddev = 1e-6 + tf.nn.softplus(gaussian_params[:, n_output:])
    return (mean, stddev)


def bernoulli_MLP_decoder(z, n_hidden, n_output, keep_prob, reuse=None):
    """Bernoulli MLP as decoder p(X|Z; \theta)."""
    with tf.variable_scope('bernoulli_MLP_decoder', reuse=reuse):
        # Initializers.
        w_init = tf.contrib.layers.variance_scaling_initializer()
        b_init = tf.constant_initializer(0.)
        # 1st hidden layer.
        w0 = tf.get_variable('w0',
            [z.get_shape()[1], n_hidden], initializer=w_init)
        b0 = tf.get_variable('b0', [n_hidden], initializer=b_init)
        h0 = tf.matmul(z, w0) + b0
        h0 = tf.nn.tanh(h0)
        h0 = tf.nn.dropout(h0, keep_prob)
        # 2nd hidden layer.
        w1 = tf.get_variable('w1',
            [h0.get_shape()[1], n_hidden], initializer=w_init)
        b1 = tf.get_variable('b1', [n_hidden], initializer=b_init)
        h1 = tf.matmul(h0, w1) + b1
        h1 = tf.nn.elu(h1)
        h1 = tf.nn.dropout(h1, keep_prob)
        # Output layer-mean.
        wo = tf.get_variable('wo',
            [h1.get_shape()[1], n_output], initializer=w_init)
        bo = tf.get_variable('bo', [n_output], initializer=b_init)
        x_recon = tf.sigmoid(tf.matmul(h1, wo) + bo)
    return x_recon


class VariationalAutoEncoder(object):

    def __init__(self, dim_x, dim_z, n_hidden, save_dir, rng):
        # Attributes from constructor.
        self.dim_x = dim_x
        self.dim_z = dim_z
        self.n_hidden = n_hidden
        self.save_dir = save_dir
        self.rng = rng
        # Derived attributes.
        self.save_path = os.path.join(self.save_dir, 'model.ckpt')
        self.dataset = np.zeros((0, self.dim_x))
        # Define autoencoder nodes.
        self.x = None
        self.keep_prob = None
        self.z = None
        self.x_recon = None
        self.marginal_likelihood = None
        self.neg_marginal_likelihood = None
        self.KL_divergence = None
        self.loss = None
        # Define optimization nodes.
        self.learn_rate = None
        self.train_op = None
        # Define probe nodes.
        self.z_probe = None
        self.x_probe = None
        # Build the autoencoder nodes.
        self.built_autoencoder = None
        self.build_autoencoder()
        # Build the optimization nodes.
        self.built_optimizer = None
        self.build_optimizer()
        # Build probe nodes.
        self.built_probes = None
        self.build_probes()
        # Initialize the global state.
        self.initialized = None
        self.initialize_graph()

    def build_autoencoder(self):
        assert not self.built_autoencoder
        # Input placeholders.
        self.x = tf.placeholder(tf.float32, shape=[None, self.dim_x])
        self.keep_prob = tf.placeholder(tf.float32)
        # Encoding (sample by re-parameterization technique).
        mu, sigma = gaussian_MLP_encoder(self.x, self.n_hidden,
            self.dim_z, self.keep_prob)
        self.z = mu + sigma * tf.random_normal(tf.shape(mu), 0, 1, tf.float32)
        # Decoding (clip values to stay binary).
        x_recon_raw = bernoulli_MLP_decoder(self.z, self.n_hidden, self.dim_x,
            self.keep_prob)
        self.x_recon = tf.clip_by_value(x_recon_raw, 1e-8, 1-1e-8)
        # Marginal likelihood.
        ml = self.x*tf.log(self.x_recon) + (1-self.x) * tf.log(1-self.x_recon)
        marginal_likelihood_sums = tf.reduce_sum(ml, 1)
        self.marginal_likelihood = tf.reduce_mean(marginal_likelihood_sums)
        self.neg_marginal_likelihood = -self.marginal_likelihood
        # KL divergence.
        kl = tf.square(mu) + tf.square(sigma) \
            - tf.log(1e-8 + tf.square(sigma)) - 1
        KL_divergence_sums = .5 * tf.reduce_sum(kl, 1)
        self.KL_divergence = tf.reduce_mean(KL_divergence_sums)
        # ELBO and loss.
        self.ELBO = self.marginal_likelihood - self.KL_divergence
        self.loss = -self.ELBO
        # Report the VAE nodes are built.
        self.built_autoencoder = True

    def build_optimizer(self):
        assert not self.built_optimizer
        assert self.built_autoencoder
        self.learn_rate = tf.placeholder(tf.float32)
        optimizer = tf.train.AdamOptimizer(self.learn_rate)
        self.train_op = optimizer.minimize(self.loss)
        # Report the optimizer nodes are built.
        self.built_optimizer = True

    def build_probes(self):
        assert not self.built_probes
        assert self.built_autoencoder
        self.z_probe = tf.placeholder(tf.float32, shape=[None, self.dim_z])
        self.x_probe = bernoulli_MLP_decoder(self.z_probe, self.n_hidden,
            self.dim_x, 1.0, reuse=True)
        # Report the probes nodes are built.
        self.built_probes = True

    def initialize_graph(self):
        assert not self.initialized
        assert self.built_autoencoder
        assert self.built_optimizer
        assert self.built_probes
        if not os.path.exists(self.save_dir):
            with tf.Session() as sess:
                sess.run(tf.global_variables_initializer(),
                    feed_dict={self.keep_prob: 0.9},
                )
                os.mkdir(self.save_dir)
                saver = tf.train.Saver()
                saver.save(sess, self.save_path)
                print 'Model saved in path: %s' % (self.save_path,)
        self.initialized = True

    def incorporate(self, dataset):
        assert np.shape(dataset)[1] == self.dim_x
        self.dataset = np.concatenate((self.dataset, dataset), axis=0)

    def train_autoencoder(self, batch_size, learn_rate):
        assert self.initialized
        n_samples = self.get_num_samples()
        num_batches = int(n_samples/batch_size)
        indexes = self.rng.permutation(n_samples)
        dataset = self.dataset[indexes]
        with tf.Session() as sess:
            saver = tf.train.Saver()
            saver.restore(sess, self.save_path)
            print 'Model restored from %s' % (self.save_path,)
            for i in xrange(num_batches):
                print '\rbatch %d / %d' % (i, num_batches),
                import sys; sys.stdout.flush()
                # Prepare the mini-batch.
                batch_xs = self.get_batch_xs(dataset, batch_size, n_samples, i)
                # Run ADAM optimization on the mini-batch.
                _u, total_loss, loss_likelihood, loss_divergence = sess.run(
                    (self.train_op,
                        self.loss,
                        self.neg_marginal_likelihood,
                        self.KL_divergence
                    ),
                    feed_dict={
                        self.x: batch_xs,
                        self.keep_prob: 0.9,
                        self.learn_rate: learn_rate
                })
            saver = tf.train.Saver()
            saver.save(sess, self.save_path)
            print 'Model saved in path: %s' % (self.save_path,)
        return (total_loss, loss_likelihood, loss_divergence)

    def get_batch_xs(self, train_data, batch_size, n_samples, i):
        offset = (i * batch_size) % (n_samples)
        batch_xs = train_data[offset:(offset + batch_size),:]
        return batch_xs

    def get_num_samples(self):
        return np.shape(self.dataset)[0]

    def run_x_reconstruct(self, x_probe):
        assert self.initialized
        with tf.Session() as sess:
            saver = tf.train.Saver()
            saver.restore(sess, self.save_path)
            print 'Model restored from %s' % (self.save_path,)
            return sess.run(self.x_recon,
                feed_dict={self.x: x_probe, self.keep_prob: 1})

    def run_z_encode(self, x_probe):
        assert self.initialized
        with tf.Session() as sess:
            saver = tf.train.Saver()
            saver.restore(sess, self.save_path)
            print 'Model restored from %s' % (self.save_path,)
            return sess.run(self.z,
                feed_dict={self.x: x_probe, self.keep_prob: 1})

    def run_x_decode(self, z_probe):
        assert self.initialized
        with tf.Session() as sess:
            saver = tf.train.Saver()
            saver.restore(sess, self.save_path)
            print 'Model restored from %s' % (self.save_path,)
            return sess.run(self.x_probe,
                feed_dict={self.z_probe: z_probe, self.keep_prob: 1})

    def to_metadata(self):
        metadata = dict()
        metadata['dim_x'] = self.dim_x
        metadata['dim_z'] = self.dim_z
        metadata['n_hidden'] = self.n_hidden
        metadata['save_dir'] = self.save_dir
        metadata['factory'] = ('cgpm.vae', 'VariationalAutoEncoder')
        return metadata

    @classmethod
    def from_metadata(cls, metadata, rng=None):
        rng = rng or np.random.RandomState(2)
        return cls(
            metadata['dim_x'],
            metadata['dim_z'],
            metadata['n_hidden'],
            metadata['save_dir'],
            rng
        )
