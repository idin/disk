from .Path import Path
import atexit
from chronometry import get_elapsed, get_now


# Box is an object that saves itself to the disk
class Box:
	def __init__(self, path, save_interval_seconds=60):
		self._path = Path(string=path)
		if not self._path.exists():
			self._path.make_parent_directory(ignore_if_exists=True)
		self._num_saved_items = None
		self._dict = {}
		self._save_interval_seconds = save_interval_seconds
		self._save_time = get_now()
		self.load(append=False)
		atexit.register(self.save)

	_STATE_ATTRIBUTES_ = ['_path', '_num_saved_items', '_dict', '_save_interval_seconds', '_save_time']

	def __getstate__(self):
		return {key: getattr(self, key) for key in self._STATE_ATTRIBUTES_}

	def __setstate__(self, state):
		for key, value in state.items():
			setattr(self, key, value)
		self._path.make_parent_directory(ignore_if_exists=True)
		self.load(append=True)
		atexit.register(self.save)

	def check(self, echo=0):
		echo = max(0, echo)
		# if the number of items increased by more than 10% o
		if get_elapsed(start=self._save_time, unit='sec') > self._save_interval_seconds:
			self.save(echo=echo)

	@property
	def path(self):
		"""
		:rtype: Path
		"""
		return self._path

	def load(self, append=True, echo=0):
		echo = max(0, echo)
		if self.path.exists():
			dictionary = self.path.unpickle(method='pickle', echo=echo)
			if append:
				dictionary.update(self._dict)
			self._dict = dictionary

	def save(self, echo=0):
		echo = max(0, echo)
		self.path.pickle(obj=self._dict, echo=echo)
		self._save_time = get_now()

	@property
	def size_bytes(self):
		self.check()
		return self.path.size_bytes

	@property
	def names(self):
		self.check()
		return self._dict.keys()

	@property
	def items(self):
		self.check()
		return self._dict.items()

	@property
	def objects(self):
		self.check()
		return self._dict.values()

	def get_all_names(self):
		self.check()
		return self._dict.keys()

	@property
	def size(self):
		self.check()
		return len(self._dict)

	def contains(self, name):
		self.check()
		return name in self._dict

	def get(self, name):
		self.check()
		if name not in self._dict:
			self.load(append=True)
		return self._dict[name]

	def set(self, name, obj):
		self._dict[name] = obj
		self.check()

	def __getitem__(self, item):
		return self.get(name=item)

	def __setitem__(self, key, value):
		self.set(name=key, obj=value)

	def __contains__(self, item):
		return self.contains(name=item)

	def remove(self, name):
		del self._dict[name]
		self.check()

	def flush(self):
		self._dict = {}
		self.check()
