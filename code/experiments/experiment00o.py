#!/usr/bin/env python

"""
Use PCA filters and optimize marginals.
"""

import sys

sys.path.append('./code')

from numpy import *
from numpy.random import randn
from models import ISA, ICA, Distribution, MoGaussian
from transforms import LinearTransform, WhiteningTransform
from tools import preprocess, Experiment, mapp

mapp.max_processes = 8
Distribution.VERBOSITY = 1

from numpy import round, sqrt, eye
from numpy.linalg import svd

patch_size = '8x8'
num_data = 50000
noise_level = None

def main(argv):
	seterr(invalid='raise', over='raise', divide='raise')

	# start experiment
	experiment = Experiment()



	### DATA HANDLING

	# load data, log-transform and center data
	data = load('data/vanhateren.{0}.1.npz'.format(patch_size))['data']
	data = preprocess(data, noise_level=noise_level)

#	data_test = load('data/vanhateren.{0}.0.npz'.format(patch_size))['data']
#	data_test = preprocess(data_test, noise_level=noise_level)[:, :10000]
	
	# apply discrete cosine transform and remove DC component
	dct = LinearTransform(dim=int(sqrt(data.shape[0])), basis='DCT')

#	mog = MoGaussian(20)
#	mog.train(dct(data)[:1], max_iter=100)
#	print mog.evaluate(dct(data_test)[:1])

	# remove DC component
	data = dct(data)[1:]

	# PCA whitening
	wt = WhiteningTransform(data, symmetric=False)
	data = wt(data)

#	print wt.logjacobian()
#	return 0



	### MODEL DEFINITION

	# create ICA model
	ica = ISA(data.shape[0])
	ica.initialize(method='laplace')
	ica.A = eye(data.shape[0])



	### TRAIN MODEL

	# optimize marginals
	ica.train(data[:, :num_data],
		max_iter=20,
		train_prior=True,
		train_basis=False,
		method='lbfgs')



	### EVALUATE MODEL

	data_test = load('data/vanhateren.{0}.0.npz'.format(patch_size))['data']
	data_test = preprocess(data_test, noise_level=noise_level)[:, :10000]
	data_test = wt(dct(data_test)[1:])

	print 'training: {0:.4f} [bit/pixel]'.format(ica.evaluate(data))
	print 'test: {0:.4f} [bit/pixel]'.format(ica.evaluate(data_test))


#	# save results
#	experiment.save('results/experiment00o/experiment00o.{0}.{1}.xpck')

	return 0



if __name__ == '__main__':
	sys.exit(main(sys.argv))
