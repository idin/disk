import os
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
from chronometry.progress import ProgressBar


def zip_directory(path, zip_path, compression=ZIP_DEFLATED, echo=0):
	echo = max(0, echo)
	progress_bar = ProgressBar(echo=echo, total=None)

	compression = compression or ZIP_STORED
	amount = 0
	with ZipFile(file=zip_path, mode='w', compression=compression) as zip_file:
		for root, dirs, files in os.walk(path):
			for file in files:
				zip_file.write(os.path.join(root, file))
				progress_bar.show(amount=amount, text=f'"{file}" zipped into {zip_path}')
				amount += 1
	progress_bar.show(amount=amount, text=f'{zip_path} complete!')
	return zip_path


def zip_file(path, zip_path, compression=ZIP_DEFLATED, echo=0):
	compression = compression or ZIP_STORED
	with ZipFile(file=zip_path, mode='w', compression=compression) as zip_file:
		zip_file.write(path)
	if echo:
		print(f'"{path}" zipped as "{zip_path}"')
	return zip_path


def unzip(path, unzip_path):
	with ZipFile(file=path, mode='r') as zip_file:
		zip_file.extractall(path=unzip_path)
	return unzip_path
