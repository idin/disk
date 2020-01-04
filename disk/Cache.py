from .HardFolder import HardFolder

import atexit
import functools
import warnings
from zipfile import ZIP_DEFLATED
from chronometry import get_now, get_elapsed

class TimedObject:
	def __init__(self, obj):
		self._obj = obj
		self._time = get_now()

	@property
	def obj(self):
		return self._obj

	@property
	def time(self):
		return self._time

	def is_expired(self, expire_in):
		value, unit = expire_in.split()
		return get_elapsed(start=self.time, end=get_now(), unit=unit) >= float(value)

	def __getstate__(self):
		return self.obj, self.time

	def __setstate__(self, state):
		self._obj, self._time = state


class Cache:
	def __init__(self, path):

		if isinstance(path, self.__class__):
			children = path._children.copy()
			path = path.path
		else:
			children = {}

		self._stats = {
			'set_success': 0, 'get_success': 0, 'get_failure': 0, 'set_failure': 0, 'set_time': None, 'get_time': None
		}
		self._children = children

		self._hard_folder = HardFolder(path=path)
		atexit.register(self.hard_folder.save_keys)

	_STATE_ATTRIBUTES_ = ['_stats', '_children', '_hard_folder']

	def zip(self, zip_path=None, delete_directory=False, compression=ZIP_DEFLATED, echo=0):
		self['_cache_children_'] = self._children
		return self.hard_folder.zip(delete_directory=delete_directory, compression=compression, zip_path=zip_path, echo=echo)

	@classmethod
	def from_zip(cls, path, unzip_path=None, delete_original=False):
		"""
		:type path: str or Path or HardFolder or Cache
		:type unzip_path: str or Path
		:type delete_original: bool
		:rtype: Cache
		"""
		hard_folder = HardFolder.from_zip(path=path, delete_original=delete_original, unzip_path=unzip_path)
		result = cls(path=hard_folder)
		result._children = result['_cache_children_']
		try:
			del result['_cache_children_']
		except Exception as e:
			print(e)
		return result

	def __getstate__(self):
		return {key: getattr(self, key) for key in self._STATE_ATTRIBUTES_}

	def __setstate__(self, state):
		for key, value in state.items():
			setattr(self, key, value)

	def __hashkey__(self):
		return self.__class__.__name__, self._hard_folder.__hashkey__()

	@property
	def hard_folder(self):
		"""
		:rtype: HardFolder or Buffer
		"""
		return self._hard_folder

	def __del__(self):
		self.hard_folder.save_keys()

	def __getitem__(self, item):
		try:
			result = self._hard_folder[item]
		except Exception as e:
			self._stats['get_failure'] += 1
			raise e

		self._stats['get_success'] += 1
		return result

	def __setitem__(self, key, value):
		try:
			self._hard_folder[key] = value
		except Exception as e:
			self._stats['set_failure'] += 1
			raise e
		self._stats['set_success'] += 1

	def __contains__(self, item):
		return item in self._hard_folder

	def __delitem__(self, key):

		if key in self._hard_folder:
			del self._hard_folder[key]
		else:
			raise KeyError(f'{key} does not exist in cache!')

	@property
	def path(self):
		return self.hard_folder._path

	@property
	def statistics(self):
		result = {self.path: self._stats.copy()}
		for child in self._children:
			for key, value in child.statistics.items():
				result[key] = value
		return result

	def make_cached(
			self, function, id=None, condition_function=None, if_error='warning', sub_directory=None,
			key_args=True, key_kwargs=True, exclude_kwargs=None, expire_in=None
	):
		"""
		:param callable function: function to be cached
		:param int or str id: a unique identifier for function
		:param callable condition_function: a function that determines if the result is worthy of caching
		:param str if_error: what to do if error happens: warning, error, print, ignore
		:param str sub_directory: name of a sub directory inside the cache directory to be used, optional
		:param list[int] or bool key_args: either True/False for including/excluding all args in the hash key
		or a list of indices of args to be included
		:param list[str] or bool key_kwargs: either True/False for including/excluding all kwargs in the hash key
		or a list of the kwargs to be included
		:param str or list[str] or NoneType exclude_kwargs: exclude these arguments from hash key
		:param NoneType or str expire_in: if provided the cached value will expire, e.g., '2 days', '6 months'
		:rtype: callable
		"""
		if sub_directory is None:
			return make_cached(
				function=function, cache=self, id=id, condition_function=condition_function,
				if_error=if_error, key_args=key_args, key_kwargs=key_kwargs, exclude_kwargs=exclude_kwargs,
				expire_in=expire_in
			)
		else:
			sub_path = self.path + sub_directory
			if sub_path.path in self._children:
				sub_cache = self._children[sub_path.path]
			else:
				sub_cache = self.__class__(path=sub_path.path)
			self._children[sub_path.path] = sub_cache
			return make_cached(
				function=function, cache=sub_cache, id=id, condition_function=condition_function,
				if_error=if_error, key_args=key_args, key_kwargs=key_kwargs, exclude_kwargs=exclude_kwargs,
				expire_in=expire_in
			)


def make_cached(
		function, cache, id=0, condition_function=None, if_error='warning', key_args=True, key_kwargs=True,
		exclude_kwargs=None, expire_in=None
):
	"""
	:param callable function: function to be cached
	:param Cache cache:
	:param int or str id: a unique identifier for function
	:param callable condition_function: a function that determines if the result is worthy of caching
	:param str if_error: what to do if error happens: warning, error, print, ignore
	:param list[int] or bool key_args: either True/False for including/excluding all args in the hash key or
	a list of indices of args to be included
	:param list[str] or bool key_kwargs: either True/False for including/excluding all kwargs in the hash key or
	a list of the kwargs to be included
	:param NoneType or str expire_in: if provided the cached value will expire, e.g., '2 days', '6 months'
	:rtype: callable
	"""
	if not isinstance(key_args, (bool, list)):
		raise TypeError('key_args should be either boolean or list.')
	if not isinstance(key_kwargs, (bool, list)):
		raise TypeError('key_kwargs should be either boolean or list.')

	exclude_kwargs = exclude_kwargs or []
	if isinstance(exclude_kwargs, str):
		exclude_kwargs = [exclude_kwargs]

	if_error = if_error.lower()[0]

	@functools.wraps(function)
	def wrapper(*args, update_cache=False, **kwargs):
		if isinstance(key_args, list):
			args_in_key = tuple(map(args.__getitem__, key_args))
		elif key_args:
			args_in_key = args
		else:
			args_in_key = None

		if isinstance(key_kwargs, list):
			kwargs_in_key = {key: kwargs[key] for key in key_kwargs if key not in exclude_kwargs}
		elif key_kwargs:
			kwargs_in_key = {key: value for key, value in kwargs.items() if key not in exclude_kwargs}
		else:
			kwargs_in_key = None

		key = (id, function.__name__, function.__doc__, args_in_key, kwargs_in_key)

		if key in cache and not update_cache:
			try:
				result = cache[key]

				if isinstance(result, TimedObject):
					if not result.is_expired(expire_in=expire_in):
						return result.obj
				else:
					return result

			except EOFError as e:
				if if_error == 'w':  # warning
					warnings.warn(str(e))
				elif if_error == 'e':  # error
					raise e
				elif if_error == 'p':  # print
					print(e)
				# else: ignore

		result = function(*args, **kwargs)

		if condition_function is None:
			# save the result regardless
			should_save_in_cache = True

		else:
			# run condition function
			condition_args = list(condition_function.__code__.co_varnames)[:condition_function.__code__.co_argcount]
			condition_kwargs = {key: value for key, value in kwargs.items() if key in condition_args}

			# include the result in the arguments for condition function if necessary
			if 'result' in condition_args:
				condition_kwargs['result'] = result

			if condition_function(**condition_kwargs):
				should_save_in_cache = True
			else:
				should_save_in_cache = False

		if should_save_in_cache:
			if expire_in is not None:
				cache[key] = TimedObject(obj=result)
			else:
				cache[key] = result

		return result
	wrapper.cache = cache

	return wrapper
