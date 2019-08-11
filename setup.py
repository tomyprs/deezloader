from setuptools import setup
setup(
	name = "deezloader",
	version = "5.5.1",
	description = "Downloads songs, albums or playlists from deezer",
	license = "CC BY-NC-SA 4.0",
	author = "An0nimia",
	author_email = "An0nimia@protonmail.com",
	url = "https://github.com/An0nimia/deezloader",
	packages = ["deezloader"],
	install_requires = ['mutagen', 'requests', 'spotipy', 'tqdm'],
	scripts = ['deezloader/bin/deezloader-dw']
)