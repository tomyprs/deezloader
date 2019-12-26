#!/usr/bin/python3

import os
from tqdm import tqdm
from spotipy import Spotify
from requests import Session
from deezloader import exceptions

from deezloader.utils import (
	decryptfile, genurl,
	calcbfkey, write_tags,
	var_excape, request,
	choose_img, create_zip,
	qualities, generate_token,
	artist_sort, check_dir
)

stock_output = "%s/Songs" % os.getcwd()
stock_quality = "MP3_320"
stock_recursive_quality = False
stock_recursive_download = False
stock_not_interface = False
stock_zip = False
answers = ["Y", "y", "Yes", "YES"]
method_get_track = "song.getData"
method_get_album = "song.getListByAlbum"
method_get_user = "deezer.getUserData"
api_link = "http://www.deezer.com/ajax/gw-light.php"

class Login:
	def __init__(self, token):
		self.spo = Spotify(
			generate_token()
		)

		self.req = Session()
		self.req.cookies['arl'] = token
		user_id = self.get_api(method_get_user)['USER']['USER_ID']

		if user_id == 0:
			raise exceptions.BadCredentials("Wrong token: %s :(" % token)

	def get_api(self, method, api_token = "null", json = None):
		params = {
			"api_version": "1.0",
			"api_token": api_token,
			"input": "3",
			"method": method
		}

		try:
			return self.req.post(
				api_link,
				params = params,
				json = json
			).json()['results']
		except:
			return self.req.post(
				api_link,
				params = params,
				json = json
			).json()['results']

	def download(
		self, link, name,
		quality, recursive_quality,
		recursive_download, datas,
		not_interface, directory,
		zips = False
	):
		if not quality in qualities:
			raise exceptions.QualityNotFound("The qualities have to be FLAC or MP3_320 or MP3_256 or MP3_128")

		self.token = self.get_api("deezer.getUserData")['checkForm']

		def get_infos(method, json):
			infos = None

			while not "MD5_ORIGIN" in str(infos):
				infos = self.get_api(method, self.token, json)

			return infos

		def ultimatum(infos, datas, name, quality):
			extension = ".mp3"
			ids = infos['SNG_ID']
			key = "FILESIZE_" + quality

			if int(infos[key]) > 0 and quality == "FLAC":
				quality = "9"
				extension = ".flac"
				qualit = "FLAC"

			elif int(infos[key]) > 0 and quality == "MP3_320":
				quality = "3"
				qualit = "320"

			elif int(infos[key]) > 0 and quality == "MP3_256":
				quality = "5"
				qualit = "256"

			elif int(infos[key]) > 0 and quality == "MP3_128":
				quality = "1"
				qualit = "128"

			else:
				if not recursive_quality:
					raise exceptions.QualityNotFound("The quality chosen can't be downloaded")

				for a in qualities:
					if int(infos['FILESIZE_' + a]) > 0:
						quality = qualities[a]['quality']
						extension = qualities[a]['extension']
						qualit = qualities[a]['qualit']
						break
					else:
						if a == "MP3_128":
							raise exceptions.TrackNotFound("There isn't any quality avalaible for download this song: %s" % name)

			name += " ({}){}".format(qualit, extension)

			if os.path.isfile(name):
				if recursive_download:
					return name

				ans = input("Track %s already exists, do you want to redownload it?(y or n):" % name)

				if not ans in answers:
					return name

			try:
				md5 = infos['FALLBACK']['MD5_ORIGIN']
			except KeyError:
				md5 = infos['MD5_ORIGIN']

			hashs = genurl(md5, quality, ids, infos['MEDIA_VERSION'])

			try:
				crypt = request(
					"https://e-cdns-proxy-{}.dzcdn.net/mobile/1/{}".format(md5[0], hashs)
				)
			except IndexError:
				raise exceptions.TrackNotFound("Track: %s not found:("  % name)

			if len(crypt.content) == 0:
				raise exceptions.TrackNotFound("Something is wrong with %s :(" % name)

			encry = open(name, "wb")
			encry.write(crypt.content)
			encry.close()
			decry = open(name, "wb")

			decryptfile(
				crypt.iter_content(2048),
				calcbfkey(ids),
				decry
			)

			write_tags(
				name,
				add_more_tags(datas, infos, ids)
			)

			return name

		def add_more_tags(datas, infos, ids):
			json = {
				"sng_id": ids
			}

			try:
				datas['author'] = " & ".join(
					infos['SNG_CONTRIBUTORS']['author']
				)
			except:
				datas['author'] = ""

			try:
				datas['composer'] = " & ".join(
					infos['SNG_CONTRIBUTORS']['composer']
				)
			except:
				datas['composer'] = ""

			try:
				datas['lyricist'] = " & ".join(
					infos['SNG_CONTRIBUTORS']['lyricist']
				)
			except:
				datas['lyricist'] = ""

			try:
				datas['version'] = infos['VERSION']
			except KeyError:
				datas['version'] = ""

			need = self.get_api("song.getLyrics", self.token, json)

			try:
				datas['lyric'] = need['LYRICS_TEXT']
				datas['copyright'] = need['LYRICS_COPYRIGHTS']
				datas['lyricist'] = need['LYRICS_WRITERS']
			except KeyError:
				datas['lyric'] = ""
				datas['copyright'] = ""
				datas['lyricist'] = ""

			return datas

		ids = link.split("/")[-1]

		if "track" in link:
			json = {
				"sng_id" : ids
			}

			infos = get_infos(method_get_track, json)
			image = choose_img(infos['ALB_PICTURE'])
			datas['image'] = image
			song = "{} - {}".format(datas['music'], datas['artist'])

			if not not_interface:
				print("Downloading: %s" % song)

			try:
				nams = ultimatum(infos, datas, name, quality)
			except exceptions.TrackNotFound:
				url = request(
					"https://api.deezer.com/search/track/?q=%s" % song.replace("#", ""), True
				).json()

				try:
					for b in range(url['total'] + 1):
						if url['data'][b]['title'] == datas['music'] or datas['music'] in url['data'][b]['title_short']:
							ids = url['data'][b]['link'].split("/")[-1]
							break
				except IndexError:
					raise exceptions.TrackNotFound("Track not found: %s" % song)

				json = {
					"sng_id": ids
				}

				infos = get_infos(method_get_track, json)
				nams = ultimatum(infos, datas, name, quality)

			return nams

		nams = []
		detas = {}
		zip_name = ""
		quali = ""

		json = {
			"alb_id": ids,
			"nb": -1
		}

		infos = get_infos(method_get_album, json)['data']

		image = choose_img(
			infos[0]['ALB_PICTURE']
		)

		detas['image'] = image
		detas['album'] = datas['album']
		detas['year'] = datas['year']
		detas['genre'] = datas['genre']
		detas['ar_album'] = datas['ar_album']
		detas['label'] = datas['label']

		for a in tqdm(
			range(
				len(name)
			), 
			disable = not_interface
		):
			detas['music'] = datas['music'][a]
			detas['artist'] = datas['artist'][a]
			detas['tracknum'] = datas['tracknum'][a]
			detas['discnum'] = datas['discnum'][a]
			detas['bpm'] = datas['bpm'][a]
			detas['gain'] = datas['gain'][a]
			detas['duration'] = datas['duration'][a]
			detas['isrc'] = datas['isrc'][a]
			song = "{} - {}".format(detas['music'], detas['artist'])

			try:
				nams.append(
					ultimatum(infos[a], detas, name[a], quality)
				)
			except exceptions.TrackNotFound:
				try:
					url = request(
						"https://api.deezer.com/search/track/?q=%s" % song.replace("#", ""), True
					).json()

					for b in range(url['total'] + 1):
						if url['data'][b]['title'] == detas['music'] or detas['music'] in url['data'][b]['title_short']:
							ids = url['data'][b]['link'].split("/")[-1]
							break

					json = {
						"sng_id": ids
					}

					nams.append(
						ultimatum
						(
							get_infos(method_get_track, json), 
							detas, name[a], quality
						)
					)
				except (exceptions.TrackNotFound, IndexError, exceptions.InvalidLink):
					nams.append(name[a])
					print("Track not found: %s :(" % song)
					continue

			quali = (
				nams[a]
				.split("(")[-1]
				.split(")")[0]
			)

		if zips:
			zip_name = (
				"%s%s (%s).zip"
				% (
					directory,
					directory.split("/")[-2],
					quali 
				)
			)

			create_zip(zip_name, nams)

		return nams, zip_name

	def download_trackdee(
		self, URL,
		output = stock_output + "/",
		quality = stock_quality,
		recursive_quality = stock_recursive_quality,
		recursive_download = stock_recursive_download,
		not_interface = stock_not_interface
	):
		datas = {}

		ids = (
			URL
			.split("?utm")[0]
			.split("/")[-1]
		)

		URL1 = "https://www.deezer.com/track/%s" % ids
		URL2 = "https://api.deezer.com/track/%s" % ids
		url = request(URL2, True).json()

		url1 = request(
			"http://api.deezer.com/album/%d" % url['album']['id'], True
		).json()

		datas['music'] = url['title']
		array = []

		for a in url['contributors']:
			if a['name'] != "":
				array.append(a['name'])

		array.append(
			url['artist']['name']
		)

		datas['artist'] = artist_sort(array)
		datas['album'] = url1['title']
		datas['tracknum'] = str(url['track_position'])
		datas['discnum'] = str(url['disk_number'])
		datas['year'] = url['release_date']
		datas['genre'] = []

		try:
			for a in url1['genres']['data']:
				datas['genre'].append(a['name'])
		except KeyError:
			pass

		datas['genre'] = " & ".join(datas['genre'])
		datas['ar_album'] = []

		for a in url1['contributors']:
			if a['role'] == "Main":
				datas['ar_album'].append(a['name'])

		datas['ar_album'] = " & ".join(datas['ar_album'])
		datas['label'] = url1['label']
		datas['bpm'] = str(url['bpm'])
		datas['gain'] = str(url['gain'])
		datas['duration'] = str(url['duration'])
		datas['isrc'] = url['isrc']
		album = var_excape(datas['album'])

		directory = (
			"%s%s %s/"
			% (
				output,
				album,
				url1['upc']
			)
		)

		check_dir(directory)

		name = (
			"%s%s CD %s TRACK %s"
			% (
				directory,
				album,
				datas['discnum'],
				datas['tracknum']
			)
		)

		name = self.download(
			URL, name,
			quality, recursive_quality,
			recursive_download, datas,
			not_interface, directory
		)

		return name

	def download_albumdee(
		self, URL,
		output = stock_output + "/",
		quality = stock_quality,
		recursive_quality = stock_recursive_quality,
		recursive_download = stock_recursive_download,
		not_interface = stock_not_interface,
		zips = stock_zip
	):
		datas = {}
		datas['music'] = []
		datas['artist'] = []
		datas['tracknum'] = []
		datas['discnum'] = []
		datas['bpm'] = []
		datas['gain'] = []
		datas['duration'] = []
		datas['isrc'] = []
		names = []
		array = []

		ids = (
			URL
			.split("?utm")[0]
			.split("/")[-1]
		)

		URL1 = "https://www.deezer.com/album/%s" % ids
		URL2 = "https://api.deezer.com/album/%s" % ids
		url = request(URL2, True).json()
		datas['album'] = url['title']
		datas['label'] = url['label']
		datas['year'] = url['release_date']
		datas['genre'] = []

		try:
			for a in url['genres']['data']:
				datas['genre'].append(a['name'])
		except KeyError:
			pass

		datas['genre'] = " & ".join(datas['genre'])
		datas['ar_album'] = []

		for a in url['contributors']:
			if a['role'] == "Main":
				datas['ar_album'].append(a['name'])

		datas['ar_album'] = " & ".join(datas['ar_album'])
		album = var_excape(datas['album'])
		
		directory = (
			"%s%s %s/"
			% (
				output,
				album,
				url['upc']
			)
		)

		for a in url['tracks']['data']:
			del array[:]
			datas['music'].append(a['title'])

			ur = request(
				"https://api.deezer.com/track/%d" % a['id'], True
			).json()

			discnum = str(ur['disk_number'])
			tracknum = str(ur['track_position'])

			names.append(
				"%s%s CD %s TRACK %s"
				% (
					directory,
					album,
					discnum,
					tracknum
				)
			)

			datas['tracknum'].append(tracknum)
			datas['discnum'].append(discnum)

			datas['bpm'].append(
				str(ur['bpm'])
			)

			datas['gain'].append(
				str(ur['gain'])
			)

			datas['duration'].append(
				str(ur['duration'])
			)

			datas['isrc'].append(ur['isrc'])

			for a in ur['contributors']:
				if a['name'] != "":
					array.append(a['name'])

			array.append(
				ur['artist']['name']
			)

			datas['artist'].append(
				artist_sort(array)
			)

		check_dir(directory)

		names, zip_name = self.download(
			URL, names,
			quality, recursive_quality,
			recursive_download, datas,
			not_interface, directory, zips
		)

		if zips:
			return names, zip_name

		return names

	def download_playlistdee(
		self, URL,
		output = stock_output + "/",
		quality = stock_quality,
		recursive_quality = stock_recursive_quality,
		recursive_download = stock_recursive_download,
		not_interface = stock_not_interface,
		zips = stock_zip
	):
		array = []

		ids = (
			URL
			.split("?utm")[0]
			.split("/")[-1]
		)

		url = request(
			"https://api.deezer.com/playlist/%s" % ids, True
		).json()
	
		for a in url['tracks']['data']:
			try:
				array.append(
					self.download_trackdee(
						a['link'], output,
						quality, recursive_quality,
						recursive_download, not_interface
					)
				)
			except (exceptions.TrackNotFound, exceptions.NoDataApi):
				song = "{} - {}".format(a['title'], a['artist']['name'])
				print("Track not found: %s" % song)
				array.append(song)

		if zips:
			zip_name = "{}playlist {}.zip".format(output, ids)
			create_zip(zip_name, array)
			return array, zip_name

		return array

	def download_trackspo(
		self, URL,
		output = stock_output + "/",
		quality = stock_quality,
		recursive_quality = stock_recursive_quality,
		recursive_download = stock_recursive_download,
		not_interface = stock_not_interface
	):
		URL = URL.split("?")[0]

		try:
			url = self.spo.track(URL)
		except Exception as a:
			if not "The access token expired" in str(a):
				raise exceptions.InvalidLink("Invalid link ;)")

			self.spo = Spotify(
				generate_token()
			)

			url = self.spo.track(URL)

		isrc = url['external_ids']['isrc']

		url = request(
				"https://api.deezer.com/track/isrc:%s" % isrc, True
		).json()

		name = self.download_trackdee(
			url['link'], output,
			quality, recursive_quality,
			recursive_download, not_interface
		)

		return name

	def download_albumspo(
		self, URL,
		output = stock_output + "/",
		quality = stock_quality,
		recursive_quality = stock_recursive_quality,
		recursive_download = stock_recursive_download,
		not_interface = stock_not_interface,
		zips = stock_zip
	):
		URL = URL.split("?")[0]

		try:
			tracks = self.spo.album(URL)
		except Exception as a:
			if not "The access token expired" in str(a):
				raise exceptions.InvalidLink("Invalid link ;)")

			self.spo = Spotify(
				generate_token()
			)

			tracks = self.spo.album(URL)

		try:
			upc = "0%s" % tracks['external_ids']['upc']

			while upc[0] == "0":
				upc = upc[1:]

				try:
					url = request("https://api.deezer.com/album/upc:%s" % upc, True).json()

					names = self.download_albumdee(
						url['link'], output,
						quality, recursive_quality,
						recursive_download, not_interface, zips
					)

					break
				except exceptions.NoDataApi:
					if upc[0] != "0":
						raise KeyError
		except KeyError:
			tot = tracks['total_tracks']

			for a in tracks['tracks']['items']:
				try:
					isrc = self.spo.track(
						a['external_urls']['spotify']
					)['external_ids']['isrc']
				except:
					self.spo = Spotify(
						generate_token()
					)

					isrc = self.spo.track(
						a['external_urls']['spotify']
					)['external_ids']['isrc']

				try:
					ids = request(
						"https://api.deezer.com/track/isrc:%s" % isrc, True
					).json()['album']['id']

					tracks = request(
						"https://api.deezer.com/album/%d" % ids, True
					).json()

					if tot == tracks['nb_tracks']:
						break
				except exceptions.NoDataApi:
					pass

			try:
				names = self.download_albumdee(
					tracks['link'], output,
					quality, recursive_quality,
					recursive_download, not_interface, zips
				)
			except KeyError:
				raise exceptions.AlbumNotFound("Album not found :(")

		return names

	def download_playlistspo(
		self, URL,
		output = stock_output + "/",
		quality = stock_quality,
		recursive_quality = stock_recursive_quality,
		recursive_download = stock_recursive_download,
		not_interface = stock_not_interface,
		zips = stock_zip
	):
		array = []

		URL = (
			URL
			.split("?")[0]
			.split("/")
		)

		try:
			tracks = self.spo.user_playlist_tracks(URL[-3], URL[-1])
		except Exception as a:
			if not "The access token expired" in str(a):
				raise exceptions.InvalidLink("Invalid link ;)")

			self.spo = Spotify(
				generate_token()
			)

			tracks = self.spo.user_playlist_tracks(URL[-3], URL[-1])

		def lazy(tracks):
			for a in tracks['items']:
				try:
					array.append(
						self.download_trackspo(
							a['track']['external_urls']['spotify'],
							output, quality,
							recursive_quality, recursive_download, not_interface
						)
					)
				except:
					print("Track not found :(")
					array.append("None")

		lazy(tracks)
		tot = tracks['total']

		for a in range(tot // 100 - 1):
			try:
				tracks = self.spo.next(tracks)
			except:
				self.spo = Spotify(
					generate_token()
				)

				tracks = self.spo.next(tracks)

			lazy(tracks)

		if zips:
			zip_name = "{}playlist {}.zip".format(output, URL[-1])			
			create_zip(zip_name, array)
			return array, zip_name

		return array

	def download_name(
		self, artist, song,
		output = stock_output + "/",
		quality = stock_quality,
		recursive_quality = stock_recursive_quality,
		recursive_download = stock_recursive_download,
		not_interface = stock_not_interface
	):
		query = "track:{} artist:{}".format(song, artist)

		try:
			search = self.spo.search(query)
		except:
			self.spo = Spotify(
				generate_token()
			)

			search = self.spo.search(query)

		try:
			return self.download_trackspo(
				search['tracks']['items'][0]['external_urls']['spotify'],
				output, quality,
				recursive_quality, recursive_download, not_interface
			)
		except IndexError:
			raise exceptions.TrackNotFound("Track not found: :(")