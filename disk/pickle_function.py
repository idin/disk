import pickle as _pickle
import dill as _dill
import warnings

def pickle(obj, path, method='pickle', mode='wb', echo=0):
	echo = max(0, echo)
	with open(file=path, mode=mode) as output_file:
		try:
			if method == 'dill':
				_dill.dump(obj=obj, file=output_file, protocol=_dill.HIGHEST_PROTOCOL)
			else:
				_pickle.dump(obj=obj, file=output_file, protocol=_pickle.HIGHEST_PROTOCOL)
		except Exception as e:
			warnings.warn(f'Error in pickling object: {obj} to "{path}" using the {method} method!')
			raise e from e

	if echo:
		print(f'Pickled a {type(obj)} at "{path}"')


def unpickle(path, method='pickle', mode='rb', echo=0):
	echo = max(0, echo)
	with open(file=path, mode=mode) as input_file:
		try:
			if method == 'dill':
				obj = _dill.load(file=input_file)
			else:
				obj = _pickle.load(file=input_file)
		except Exception as e:
			warnings.warn(f'Error in unpickling "{path}" using the {method} method!')
			raise e from e

	if echo:
		print(f'Unpickled a {type(obj)} from "{path}"')
	return obj