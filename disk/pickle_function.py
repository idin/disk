import pickle as _pickle
import dill as _dill
from slytherin.immutability import Immutable, make_immutable


def pickle(obj, path, method='pickle', mode='wb', echo=0):
	echo = max(0, echo)
	if isinstance(obj, Immutable):
		obj = {'__immutable__':obj._original_object}
	with open(file=path, mode=mode) as output_file:
		try:
			if method == 'dill':
				_dill.dump(obj=obj, file=output_file, protocol=_dill.HIGHEST_PROTOCOL)
			else:
				_pickle.dump(obj=obj, file=output_file, protocol=_pickle.HIGHEST_PROTOCOL)
		except Exception as e:
			print(f'Error in pickling object: "{obj}" of type "{type(obj)}" to "{path}" using the {method} method!')
			raise e

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
			print(f'Error in unpickling "{path}" using the {method} method!')
			raise e

	if echo:
		print(f'Unpickled a {type(obj)} from "{path}"')
	if isinstance(obj, dict):
		if '__immutable__' in obj:
			return make_immutable(obj['__immutable__'])
	return obj
