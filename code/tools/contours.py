"""
Tool for creating contour plots from samples.
"""

__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@tuebingen.mpg.de>'
__docformat__ = 'epytext'
__version__ = '1.1.0'

from numpy import histogram2d, cov, sqrt, sum, multiply, dot
from numpy.linalg import inv
from matplotlib.pyplot import clf, contour, axis, draw

def contours(data, bins=20, levels=10, threshold=3., **kwargs):
	"""
	Estimate and visualize 2D histogram.

	@type  data: array_like
	@param data: data stored in columns

	@type  bins: integer
	@param bins: number of bins per dimension

	@type  threshold: float
	@param threshold: the smaller, the more outliers will be ignored
	"""

	# detect outliers
	error = sqrt(sum(multiply(data, dot(inv(cov(data)), data)), 0))

	# make sure at least 90% of the data will be kept
	while sum(error < threshold) < 0.9 * data.shape[1]:
		threshold += 1.

	# exclude outliers
	data = data[:, error < threshold]

	# compute histogram
	Z, X, Y = histogram2d(data[0, :], data[1, :], bins, normed=True)

	X = (X[1:] + X[:-1]) / 2.
	Y = (Y[1:] + Y[:-1]) / 2.

	# contour plot of histogram
	contour(X, Y, Z.T, levels, **kwargs)
	draw()
