from .Box import Box
from .HardFolder import HardFolder
from .individual_functions import get_path


class NestedBoxes:
	def __init__(self, path, num_items_per_box=10):
		self._path = path
		self._keys = Box(path=get_path(directory=self._path, file='keys.pickle'))
		self._data_boxes = {}
		self._items_in_data_boxes = {}

	def __contains__(self, item):
		return item in self._keys

	def data_group_names(self):
		return set(self._keys.names)

	def get_file_name(self, item):
		return self._keys[item]

	def __getitem__(self, item):
		group_key = self._keys[item]
		if group_key in self._data_boxes:
			return self._data_boxes[group_key][item]
		else:
			self._data_boxes[group_key] = Box(path=get_path(directory=self._path, file=f'{group_key}.box'))
			return self._data_boxes[group_key][item]

	def __setitem__(self, key, value):
		pass



