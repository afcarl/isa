from distribution import Distribution
from numpy import zeros

class StackedModel(Distribution):
	def __init__(self, *args):
		self.transforms = list(args[:-1])
		self.model = args[-1]
		self.dim = self.model.dim



	def __getitem__(self, key):
		return (list(self.transforms) + [self.model])[key]



	def initialize(self, data=None, *args, **kwargs):
		if data is not None:
			for transform in self.transforms:
				data = transform(data)
		self.model.initialize(data, *args, **kwargs)



	def train(self, data, *args, **kwargs):
		for transform in self.transforms:
			data = transform(data)
		self.model.train(data, *args, **kwargs)

	

	def sample(self, num_samples):
		samples = self.model.sample(num_samples)

		for transform in reversed(self.transforms):
			samples = transform.inverse(samples)

		return samples



	def loglikelihood(self, data, **kwargs):
		loglik = zeros([1, data.shape[1]])

		for transform in self.transforms:
			loglik += transform.logjacobian(data)
			data = transform(data)

		loglik = loglik + self.model.loglikelihood(data, **kwargs)

		return loglik
