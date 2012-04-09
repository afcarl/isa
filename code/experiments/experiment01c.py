"""
Evaluate overcomplete ISA models.
"""

import sys

sys.path.append('./code')

from tools import Experiment, preprocess, mapp
from numpy import load, mean, log, min, max, std, sqrt
from models import Distribution 

Distribution.VERBOSITY = 0
mapp.max_processes = 10

def main(argv):
	if len(argv) < 2:
		print 'Usage:', argv[0], '<experiment>', '[data_points]'
		return 0

	experiment = Experiment()

	# range of data points evaluated
	if len(argv) < 3:
		fr, to = 0, 1000
	else:
		if '-' in argv[2]:
			fr, to = argv[2].split('-')
			fr, to = int(fr), int(to)
		else:
			fr, to = 0, int(argv[2])

	indices = range(fr, to)

	# load experiment with trained model
	results = Experiment(argv[1])

	# ISA
	model = results['model'][1].model

	patch_size = results['parameters'][0]
	noise_level = results['parameters'][5]

	# generate test data
	data = load('data/vanhateren.{0}.0.npz'.format(patch_size))['data']
	data = preprocess(data, noise_level=noise_level, shuffle=False)

	# apply DCT and whiten data
	dct, wt = results['transforms']
	data = wt(dct(data)[1:])

	# compute logloss on whitened data
	ll = model.loglikelihood(data[:, indices],
		num_samples=200, sampling_method=('ais', {'num_steps': 200}))
	ll = ll / log(2.) / data.shape[0]

	# average log-loss and standard error of the mean
	logloss = -mean(ll)
	sem = std(ll, ddof=1) / sqrt(ll.size)

	print min(indices), max(indices)
	print '{0:.5f} +- {1:.5f} [bit/pixel]'.format(logloss, sem)

	experiment['indices'] = indices
	experiment['model'] = model
	experiment['loglik'] = ll
	experiment['logloss'] = logloss
	experiment['sem'] = sem
	experiment.save('results/experiment01c/experiment01c.{0}.{1}.xpck')

	return 0



if __name__ == '__main__':
	sys.exit(main(sys.argv))
