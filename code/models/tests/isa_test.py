import sys
import unittest 

sys.path.append('./code')

from models import ISA, Distribution
from numpy import zeros, all, abs, eye, sqrt
from tools import mapp

mapp.max_processes = 1
Distribution.VERBOSITY = 0

class Tests(unittest.TestCase):
	def test_prior_energy(self):
		step_size = 1E-5

		model = ISA(3, 7, 1)

		for gsm in model.subspaces:
			gsm.initialize('student')

		# samples and true gradient
		X = model.sample_prior(100)
		G = model.prior_energy_gradient(X)

		# numerical gradient
		N = zeros(G.shape)
		for i in range(N.shape[0]):
			d = zeros(X.shape)
			d[i] = step_size
			N[i] = (model.prior_energy(X + d) - model.prior_energy(X - d)) / (2. * step_size)

		# test consistency of energy and gradient
		self.assertTrue(all(abs(G - N) < 1E-5))



	def test_train(self):
		isa = ISA(2, 2)
		data = isa.sample_prior(1000)

		# make sure training doesn't throw any exceptions
		isa.train_sgd(data, max_iter=1)
		isa.train_lbfgs(data, max_fun=1)

		isa = ISA(2, 2, noise=True)
		data = isa.sample_prior(1000)

		# make sure training doesn't throw any exeptions
		isa.train_sgd(data, max_iter=1, weight_decay=0.01)
		isa.train_analytic(data, max_iter=1, weight_decay=0.01)
		isa.train_lbfgs(data, max_fun=1, weight_decay=0.01)
	


	def test_train_subspaces(self):
		isa = ISA(4, 4, 2)
		isa.initialize(method='laplace')

		samples = isa.sample_prior(10000)

		isa = ISA(4, 4, 1)
		isa.initialize(method='laplace')

		isa.train_subspaces(samples, max_merge=5)
		isa.train_subspaces(samples, max_merge=5)

		self.assertTrue(len(isa.subspaces) == 2)



	def test_compute_map(self):
		isa = ISA(2, 4)

		X = isa.sample(100)

		M = isa.compute_map(X, tol=1E-4, maxiter=1000)
		Y = isa.sample_posterior(X)

		self.assertTrue(all(isa.prior_energy(M) <= isa.prior_energy(Y)))



	def test_evaluate(self):
		isa1 = ISA(2)
		isa1.A = eye(2)

		for gsm in isa1.subspaces:
			gsm.scales[:] = 1.

		# equivalent overcomplete model
		isa2 = ISA(2, 4)
		isa2.A[:, :2] = isa1.A / sqrt(2.)
		isa2.A[:, 2:] = isa1.A / sqrt(2.)

		for gsm in isa2.subspaces:
			gsm.scales[:] = 1.

		data = isa1.sample(100)

		# the results should not depend on the parameters
		ll1 = isa1.evaluate(data)
		ll2 = isa2.evaluate(data, num_samples=2, sampling_method=('ais', {'num_steps': 2}))

		self.assertTrue(abs(ll1 - ll2) < 1e-5)



if __name__ == '__main__':
	unittest.main()
