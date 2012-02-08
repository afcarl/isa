"""
Show filters of a trained model.
"""

import sys

sys.path.append('./code')

from tools import Experiment, patchutil
from matplotlib.pyplot import figure, show
from numpy import sqrt, dot, square, sum, argsort

def main(argv):
	e = Experiment(argv[1])

	m = e['model']

	dct, wt = e['transforms']

	A = dot(dct.A[1:].T, wt.inverse(m[1].model.A))
	A_white = dot(dct.A[1:].T, m[1].model.A)

	if m[1].model.subspaces[0].dim == 1:
		n = sqrt(sum(square(m[1].model.A), 0))
		i = argsort(n)[::-1]

		A = A[:, i]
		A_white = A_white[:, i]

	patch_size = int(sqrt(A.shape[0]) + 0.5)

	figure()
	patchutil.show(A.T.reshape(-1, patch_size, patch_size))

	figure()
	patchutil.show(A_white.T.reshape(-1, patch_size, patch_size))

	show()

	return 0



if __name__ == '__main__':
	sys.exit(main(sys.argv))
