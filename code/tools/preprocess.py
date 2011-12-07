"""
Tool for preprocessing data in a standard way.
"""

__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@tuebingen.mpg.de>'
__docformat__ = 'epytext'
__version__ = '1.1.0'

from numpy import log, transpose, mean, dot, diag, sqrt, cov, asarray
from numpy.random import permutation
from numpy.linalg import eig

def preprocess(data):
	"""
	Log-transforms, centers and symmetrically whitens data.

	@type  data: array_like
	@param data: data points stored in columns
	"""

	data[data == 0] = 1
	data = asarray(data, dtype='float64')

	# log-transform
	data = log(data)

	# center
	data = data - mean(data, 1).reshape(-1, 1)

	# shuffle
	data = data[:, permutation(data.shape[1])]

	# find eigenvectors
	eigvals, eigvecs = eig(cov(data))

	# eliminate eigenvectors whose eigenvalues are zero
	eigvecs = eigvecs[:, eigvals > 0]
	eigvals = eigvals[eigvals > 0]

	# symmetric whitening matrix
	whitening_matrix = dot(eigvecs, dot(diag(1. / sqrt(eigvals)), eigvecs.T))

	# whiten data
	return asarray(dot(whitening_matrix, data), order='F')
