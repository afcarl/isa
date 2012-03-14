#!/usr/bin/env python

"""
Train overcomplete ICA on van Hateren image patches.
"""

import sys

sys.path.append('./code')

from models import ISA, MoGaussian, StackedModel, ConcatModel, Distribution
from tools import preprocess, Experiment, mapp, imsave, imformat, stitch
from transforms import LinearTransform, WhiteningTransform
from numpy import seterr, sqrt, dot, load

# controls parallelization
mapp.max_processes = 8

# controls how much information is printed during training
Distribution.VERBOSITY = 2

# PS, OC, TI, FI, LP, SC
parameters = [
	# complete models
	['8x8',   1,   5, 10, True, False],
	['16x16', 1,   5, 10, True, False],

	# overcomplete models
	['8x8',   2, 100, 50, True, False],
	['16x16', 2, 100, 50, True, False],

	# overcomplete models with Laplace marginals
	['8x8',   2, 100, 50, False, False],
	['16x16', 2, 100, 50, False, False],

	# initialize with sparse coding
	['8x8',   2,   0, 50, True, True],
	['16x16', 2,   0, 50, True, True],
]

def main(argv):
	if len(argv) < 2:
		print 'Usage:', argv[0], '<param_id>'
		print
		print '  {0:>3} {1:>7} {2:>5} {3:>5} {4:>5} {5:>5} {6:>5}'.format(
			'ID', 'PS', 'OC', 'TI', 'FI', 'LP', 'SC')

		for id, params in enumerate(parameters):
			print '  {0:>3} {1:>7} {2:>5} {3:>5} {4:>5} {5:>5} {6:>5}'.format(id, *params)

		print
		print '  ID = parameter set'
		print '  PS = patch size'
		print '  OC = overcompleteness'
		print '  TI = number of training iterations'
		print '  FI = number of fine-tuning iterations'
		print '  LP = optimize marginal distributions'
		print '  SC = initialize with sparse coding'

		return 0

	seterr(invalid='raise', over='raise', divide='raise')

	# start experiment
	experiment = Experiment(server='10.38.138.150')

	# hyperparameters
	patch_size, \
	overcompleteness, \
	max_iter, \
	max_iter_ft, \
	train_prior, \
	sparse_coding = parameters[int(argv[1])]


	
	### DATA PREPROCESSING

	# load data, log-transform and center data
	data = load('data/vanhateren.{0}.1.npz'.format(patch_size))['data']
	data = preprocess(data)

	# discrete cosine transform and whitening transform
	dct = LinearTransform(dim=int(sqrt(data.shape[0])), basis='DCT')
	wt = WhiteningTransform(dct(data)[1:], symmetric=True)


	### MODEL DEFINITION

	isa = ISA(num_visibles=data.shape[0] - 1,
	          num_hiddens=data.shape[0] * overcompleteness - 1)

	# model DC component with a mixture of Gaussians
	model = StackedModel(dct,
		ConcatModel(MoGaussian(20), StackedModel(wt, isa)))



	### MODEL TRAINING

	# variables to store in results
	experiment['model'] = model
	experiment['parameters'] = parameters[int(argv[1])]


	def callback(phase, isa, iteration):
		"""
		Saves intermediate results every few iterations.
		"""

		if not iteration % 1:
			# whitened filters
			A = dot(dct.A[1:].T, isa.A)

			patch_size = int(sqrt(A.shape[0]) + 0.5)

			# save intermediate results
			experiment.save('results/vanhateren/results.{0}.{1}.{2}.xpck'.format(argv[1], phase, iteration))

			# visualize basis
			imsave('results/vanhateren/basis.{0}.{1}.{2}.png'.format(argv[1], phase, iteration),
				stitch(imformat(A.T.reshape(-1, patch_size, patch_size))))



	# enable regularization of marginals
	for gsm in isa.subspaces:
		gsm.gamma = 1e-2
		gsm.alpha = 2.
		gsm.beta = 1.

	# train mixture of Gaussians on DC component
	model.train(data, 0, max_iter=100)

	# initialize filters and marginals
	model.initialize(data, 1)
	model.initialize(model=1, method='laplace')

	experiment.progress(10)

	if sparse_coding:
		# initialize with sparse coding
		model.train(data[:, :20000], 1,
			method=('of', {
				'max_iter': 50,
				'noise_var': 0.1,
				'var_goal': 1.,
				'beta': 10.,
				'step_width': 0.01,
				'sigma': 1.0}),
			callback=lambda isa, iteration: callback(0, isa, iteration))
		isa.orthogonalize()

	else:
		# train model using a subset of the data
		model.train(data[:, :20000], 1,
			max_iter=max_iter,
			train_prior=train_prior,
			persistent=True,
			init_sampling_steps=10,
			method='lbfgs',
			callback=lambda isa, iteration: callback(0, isa, iteration),
			sampling_method=('gibbs', {'num_steps': 2}))

	experiment.progress(50)

	# disable regularization
	for gsm in isa.subspaces:
		gsm.gamma = 0.

	# fine-tune model using all the data
	model.train(data, 1,
		max_iter=max_iter_ft,
		train_prior=train_prior,
		persistent=True,
		init_sampling_steps=10 if sparse_coding or not train_prior else 50,
		method='lbfgs',
		callback=lambda isa, iteration: callback(1, isa, iteration),
		sampling_method=('gibbs', {'num_steps': 5}))

	experiment.save('results/vanhateren/vanhateren.{0}.{{0}}.{{1}}.xpck'.format(argv[1]))

	return 0



if __name__ == '__main__':
	sys.exit(main(sys.argv))
