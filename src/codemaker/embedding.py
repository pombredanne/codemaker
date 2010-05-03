"""Utility to find local structure preserving low dimensional embeddings"""

import theano
from pynnet.layers.autoencoder import Autoencoder
from pynnet.trainers import get_updates
import numpy as np

def compute_embedding(data, target_dim, epochs=100, batch_size=100,
                      learning_rate=0.01):
    """Learn an embedding of data into a vector space of target_dim

    Current implementation: only minize the reconstruction error of a simple
    autoencoder

    TODO: stack several wide-band autoencoders with a sparsity penalty + input
    corruption during pre-training + add a local structure preservation penalty
    to the overall cost expression such as the one described in the Parametric
    t-SNE paper by Maarten 2009.

    """
    data = np.atleast_2d(data)
    data = np.asanyarray(data, dtype=theano.config.floatX)
    n_samples, n_features = data.shape

    ae = Autoencoder(data.shape[1], target_dim, tied=False, noise=0.0)
    x = theano.tensor.fmatrix('x')
    ae.build(x)
    train = theano.function(
        [ae.input], ae.cost,
        updates=get_updates(ae.pre_params, ae.cost, learning_rate))
    encode = theano.function([ae.input], ae.output)

    n_batches = n_samples / batch_size
    for e in xrange(epochs):
        print "reshuffling data"
        shuffled = data.copy()
        np.random.shuffle(shuffled)

        print "training..."
        err = np.zeros(n_batches)
        for b in xrange(n_batches):
            batch_input = shuffled[b * batch_size:(b + 1) * batch_size]
            err[b] = train(batch_input).mean()
        print "epoch %d: err: %0.3f" % (e, err.mean())

    return encode(data), encode





