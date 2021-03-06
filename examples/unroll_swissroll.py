"""Train an encoder to extract a 2D swissroll manifold from higher dim data"""
import numpy as np
import pylab as pl
import time

from codemaker.datasets import swissroll
from codemaker.embedding import SDAEmbedder
from codemaker.evaluation import Neighbors, local_match, pairwise_distances

try:
    import mdp
except ImportError:
    mdp = None

pl.clf()

n_features = 30
n_samples = 1000

print "Generating embedded swissroll with n_features=%d and n_samples=%d" % (
    n_features, n_samples)

data, manifold = swissroll.load(
    n_features=n_features,
    n_samples=n_samples,
    n_turns=1.2,
    radius=1.,
    hole=False,
)
score_manifold_data = local_match(
    data, manifold, query_size=50, ratio=1, seed=0)
print "kNN score match manifold/data:", score_manifold_data

# build model to extract the manifold and learn a mapping / encoder to be able
# to reproduce this on test data
embedder = SDAEmbedder((n_features, 10, 2),
                       noise=0.1,
                       reconstruction_penalty=1.0,
                       embedding_penalty=0.1,
                       sparsity_penalty=0.0,
                       learning_rate=0.1, seed=0)

# use the randomly initialized encoder to measure the baseline
code = embedder.encode(data)
score_code_data = local_match(data, code, query_size=50, ratio=1, seed=0)
print "kNN score match after pre-training code/data:", score_code_data
fig = pl.figure(1)
_, _, corr = pairwise_distances(data, code, ax=fig.add_subplot(3, 1, 1),
                                title="random")
print "Pairwise distances correlation:", corr

print "Training encoder to unroll the embedded data..."
start = time.time()
embedder.pre_train(data, slice_=slice(None, None), epochs=1000, batch_size=100)
print "done in %ds" % (time.time() - start)

# evaluation of the quality of the embedding by comparing kNN queries from the
# original (high dim) data and the low dim code on the one hand, and from the
# ground truth low dim manifold and the low dim code on the other hand

code = embedder.encode(data)
score_code_data = local_match(data, code, query_size=50, ratio=1, seed=0)
print "kNN score match after pre-training code/data:", score_code_data
_, _, corr = pairwise_distances(data, code, ax=fig.add_subplot(3, 1, 2),
                                title="pre-training")
print "Pairwise distances correlation:", corr

# fine tuning
print "Fine tuning encoder to unroll the embedded data..."
start = time.time()
embedder.fine_tune(data, epochs=1000, batch_size=5)
print "done in %ds" % (time.time() - start)

code = embedder.encode(data)
score_code_data = local_match(data, code, query_size=50, ratio=1, seed=0)
print "kNN score match after fine-tuning code/data:", score_code_data
_, _, corr = pairwise_distances(data, code, ax=fig.add_subplot(3, 1, 3),
                                title="fine tuning")
print "Pairwise distances correlation:", corr


if mdp is not None:
    # unroll the same data with HLLE
    print "Comptuting projection using Hessian LLE model..."
    start = time.time()
    hlle_code = mdp.nodes.HLLENode(15, output_dim=2)(data)
    print "done in %ds" % (time.time() - start)

    score_hlle_code_data = local_match(
        data, hlle_code, query_size=50, ratio=1, seed=0)
    print "kNN score match hlle_code/data:", score_hlle_code_data


pl.figure(2)
# plot the 2d projection of the first two axes
colors = manifold[:, 0]
sp = pl.subplot(221)
sp.scatter(data[:, 0], data[:, 1], c=colors)
sp.set_title("2D Projection of the high dim data")

# plot the unrolled manifold embedded in the data
sp = pl.subplot(222)
sp.scatter(manifold[:, 0], manifold[:, 1], c=colors)
sp.set_title("Original manifold embedded in data")

# plot the learned unrolled 2D embedding (not working yet)
sp = pl.subplot(223)
sp.scatter(code[:, 0], code[:, 1], c=colors)
sp.set_title("2D manifold recovery by codemaker")

if mdp is not None:
    # plot the unrolled 2D embedding computed by HLLE
    sp = pl.subplot(224)
    sp.scatter(hlle_code[:, 0], hlle_code[:, 1], c=colors)
    sp.set_title("2D manifold recovery by HLLE")

pl.show()

