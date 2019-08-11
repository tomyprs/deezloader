#!/usr/bin/python3

import os
import requests
from tqdm import tqdm
from deezloader import exceptions
from spotipy import Spotify, oauth2
from collections import OrderedDict
from deezloader.utils import (
	decryptfile, genurl,
	calcbfkey, write_tags,
	var_excape, request,
	choose_img, create_zip
)

stock_output = os.getcwd() + "/Songs/"
stock_quality = "MP3_320"
stock_recursive_quality = False
stock_recursive_download = False
stock_interface = True
stock_zip = False

qualities = {

	"FLAC": {
		"quality": "9",
		"extension": ".flac",
		"qualit": "FLAC"
	},

	"MP3_320": {
		"quality": "3",
		"extension": ".mp3",
		"qualit": "320"
	},

	"MP3_256": {
		"quality": "5",
		"extension": ".mp3",
		"qualit": "256"
	},

	"MP3_128": {
		"quality": "1",
		"extension": ".mp3",
		"qualit": "128"
	}
}

def generate_token():
	return oauth2.SpotifyClientCredentials(
		client_id="c6b23f1e91f84b6a9361de16aba0ae17",
		client_secret="237e355acaa24636abc79f1a089e6204"
	).get_access_token()

class Login:
	def __init__(self, mail, password, token=None):
		self.spo = Spotify(
			auth=generate_token()
		)

		self.req = requests.Session()
		
		check = self.get_api("deezer.getUserData")['checkFormLogin']

		post_data = {
				"type": "login",
				"mail": mail,
				"password": password,
				"checkFormLogin": check
		}

		end = self.req.post(
			"https://www.deezer.com/ajax/action.php", post_data
		).text

		if "success" == end:
			print("Success, you are in :)")

		else:
			if not token:
				raise exceptions.BadCredentials(end + ", and no token provided")

			self.req.cookies['arl'] = token

			user_id = (
				self.req.get("https://www.deezer.com/")
				.text
				.split("'deezer_user_id': ")[1]
				.split(",")[0]
			)

			if user_id == "0":
				raise exceptions.BadCredentials("Wrong token :(")

	def get_api(self, method, api_token="null", json=None):
		params = {
			"api_version": "1.0",
			"api_token": api_token,
			"input": "3",
			"method": method
		}

		try:
			return self.req.post(
				"http://www.deezer.com/ajax/gw-light.php",
				params=params,
				json=json
			).json()['results']
		except:
			return self.req.post(
				"http://www.deezer.com/ajax/gw-light.php",
				params=params,
				json=json
			).json()['results']

	def download(
		self, link, name,
		quality, recursive_quality, recursive_download,
		datas, interface, zips=False
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
							raise exceptions.TrackNotFound("There isn't any quality avalaible for download this song")

			name += " (" + qualit + ")" + extension

			if os.path.isfile(name):
				if recursive_download:
					return name

				ans = input("Track " + name + " already exists, do you want to redownload it?(y or n):")

				if not ans in ["Y", "y", "Yes", "YES"]:
					return name

			try:
				md5 = infos['FALLBACK']['MD5_ORIGIN']
			except KeyError:
				md5 = infos['MD5_ORIGIN']

			hashs = genurl(md5, quality, ids, infos['MEDIA_VERSION'])

			try:
				crypt = request(
					"https://e-cdns-proxy-%s.dzcdn.net/mobile/1/%s" 
					% (
						md5[0],
						hashs
					)
				)
			except IndexError:
				raise exceptions.TrackNotFound("Track not found :(")

			if len(crypt.content) == 0:
				raise exceptions.TrackNotFound("Error with this track :(")

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
				add_more_tags(
					datas, infos, ids
				)
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

		json = {
			"sng_id" : ids
		}

		if "track" in link:
			method = "song.getData"
			infos = get_infos(method, json)
			image = choose_img(infos['ALB_PICTURE'])
			datas['image'] = image
			song = datas['music'] + " - " + datas['artist']
			
			if interface:
				print("Downloading:" + song)

			try:
				nams = ultimatum(infos, datas, name, quality)
			except exceptions.TrackNotFound:
				url = request(
					"https://api.deezer.com/search/track/?q=%s + %s"
					% (
						datas['music'].replace("#", ""),
						datas['artist'].replace("#", "")
					),
					True
				).json()

				try:
					for b in range(url['total'] + 1):
						if url['data'][b]['title'] == datas['music'] or datas['music'] in url['data'][b]['title_short']:
							URL = url['data'][b]['link']
							break
				except IndexError:
					raise exceptions.TrackNotFound("Track not found: " + song)
					
				json = {
					"sng_id": URL.split("/")[-1]
				}
				
				infos = get_infos(method, json)
				nams = ultimatum(infos, detas, name, quality)

			return nams
		
		nams = []
		detas = {}
		method = "song.getListByAlbum"
		zip_name = ""
		quali = ""

		json = {
			"alb_id": ids,
			"nb": -1
		}

		infos = get_infos(method, json)['data']

		image = choose_img(
			infos[0]['ALB_PICTURE']
		)

		detas['image'] = image
		detas['album'] = datas['album']
		detas['year'] = datas['year']
		detas['genre'] = datas['genre']
		detas['ar_album'] = datas['ar_album']
		detas['label'] = datas['label']

		for a in tqdm(range(len(name)), disable=interface):
			detas['music'] = datas['music'][a]
			detas['artist'] = datas['artist'][a]
			detas['tracknum'] = datas['tracknum'][a]
			detas['discnum'] = datas['discnum'][a]
			detas['bpm'] = datas['bpm'][a]
			detas['gain'] = datas['gain'][a]
			detas['duration'] = datas['duration'][a]
			detas['isrc'] = datas['isrc'][a]

			try:
				nams.append(
					ultimatum(infos[a], detas, name[a], quality)
				)
			except exceptions.TrackNotFound:
				url = request(
					"https://api.deezer.com/search/track/?q=%s + %s"
					% (
						detas['music'].replace("#", ""),
						detas['artist'].replace("#", "")
					),
					True
				).json()

				try:
					for b in range(url['total'] + 1):
						if url['data'][b]['title'] == detas['music'] or detas['music'] in url['data'][b]['title_short']:
							URL = url['data'][b]['link']
							break
				except IndexError:
					nams.append(name[a])
					print("Track not found: " + detas['music'] + " - " + detas['artist'])
					continue

				try:
					method = "song.getData"

					json = {
						"sng_id": URL.split("/")[-1]
					}

					nams.append(
						ultimatum
						(
							get_infos(
								method, json
							), 
							detas, name[a], quality
						)
					)		
				except exceptions.TrackNotFound:
					nams.append(name[a])
					print("Track not found: " + detas['music'] + " - " + detas['artist'])
					continue

			quali = (
				nams[a]
				.split("(")[-1]
				.split(")")[0]
			)
				
		if zips:
			directory = "/".join(
				name[a]
				.split("/")[:-1]
			) + "/"
				
			if len(nams) > 0:
				zip_name = directory + directory.split("/")[-2] + " (" + quali + ").zip"
				create_zip(zip_name, nams)

		return nams, zip_name

	def download_trackdee(
		self, URL,
		output = stock_output,
		quality = stock_quality,
		recursive_quality = stock_recursive_quality,
		recursive_download = stock_recursive_download,
		interface = stock_interface
	):
		datas = {}

		if "?utm" in URL:
			URL, a = URL.split("?utm")

		URL1 = "https://www.deezer.com/track/" + URL.split("/")[-1]
		URL2 = "https://api.deezer.com/track/" + URL.split("/")[-1]

		url = request(
			URL2, True
		).json()

		url1 = request(
			"http://api.deezer.com/album/" + str(url['album']['id']), True
		).json()

		datas['music'] = url['title']
		array = []

		for a in url['contributors']:
			array.append(a['name'])

		array.append(url['artist']['name'])
			
		if len(array) > 1:
			for a in array:
				for b in array:
					if a in b and a != b:
						array.remove(b)
			
		datas['artist'] = ", ".join(
				OrderedDict.fromkeys(array)
		)

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
		directory = output + album + " " + url1['upc'] + "/"

		try:
			os.makedirs(directory)
		except FileExistsError:
			pass

		name = directory + album + " CD " + datas['discnum'] + " TRACK " + datas['tracknum']

		name = self.download(
			URL, name,
			quality, recursive_quality,
			recursive_download, datas, interface
		)

		return name

	def download_albumdee(
		self, URL,
		output = stock_output,
		quality = stock_quality,
		recursive_quality = stock_recursive_quality,
		recursive_download = stock_recursive_download,
		interface = stock_interface,
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

		if "?utm" in URL:
			URL, a = URL.split("?utm")
		URL1 = "https://www.deezer.com/album/" + URL.split("/")[-1]
		URL2 = "https://api.deezer.com/album/" + URL.split("/")[-1]

		url = request(
			URL2, True
		).json()

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
		directory = output + "/" + album + " " + url['upc'] + "/"

		for a in url['tracks']['data']:
			del array[:]
			datas['music'].append(a['title'])

			ur = request(
				"https://api.deezer.com/track/" + str(a['id']), True
			).json()

			discnum = str(ur['disk_number'])
			tracknum = str(ur['track_position'])
			
			names.append(
				directory + album + " CD " + discnum + " TRACK " + tracknum
			)
			
			datas['tracknum'].append(tracknum)
			datas['discnum'].append(discnum)
			datas['bpm'].append(str(ur['bpm']))
			datas['gain'].append(str(ur['gain']))
			datas['duration'].append(str(ur['duration']))
			datas['isrc'].append(ur['isrc'])

			for a in ur['contributors']:
				array.append(a['name'])

			array.append(
				ur['artist']['name']
			)

			if len(array) > 1:
				for a in array:
					for b in array:
						if a in b and a != b:
							array.remove(b)
				
			datas['artist'].append(
				", ".join(
					OrderedDict.fromkeys(array)
				)
			)

		try:
			os.makedirs(directory)
		except FileExistsError:
			pass

		names, zip_name = self.download(
			URL, names,
			quality, recursive_quality,
			recursive_download, datas,
			interface, zips
		)

		if zips:
			return names, zip_name

		return names

	def download_playlistdee(
		self, URL,
		output = stock_output,
		quality = stock_quality,
		recursive_quality = True,
		recursive_download = True,
		interface = stock_interface,
		zips = stock_zip
	):
		array = []

		if "?utm" in URL:
			URL, a = URL.split("?utm")

		ids = URL.split("/")[-1]

		url = request(
			"https://api.deezer.com/playlist/" + ids, True
		).json()
			
		for a in url['tracks']['data']:
			try:
				array.append(
					self.download_trackdee(
						a['link'], output,
						quality, recursive_quality,
						recursive_download, interface
					)
				)
			except exceptions.TrackNotFound:
				print("Track not found " + a['title'])
				array.append("None")

		if zips:
			zip_name = output + "playlist_" + ids + ".zip"
			create_zip(zip_name, array)
			return array, zip_name

		return array

	def download_trackspo(
		self, URL,
		output = stock_output,
		quality = stock_quality,
		recursive_quality = stock_recursive_quality,
		recursive_download = stock_recursive_download,
		interface = stock_interface
	):
		if "?" in URL:
			URL, a = URL.split("?")

		try:
			url = self.spo.track(URL)
		except Exception as a:
			if not "The access token expired" in str(a):
				raise exceptions.InvalidLink("Invalid link ;)")

			self.spo = Spotify(
				auth=generate_token()
			)
		
			url = self.spo.track(URL)
		
		isrc = url['external_ids']['isrc']

		url = request(
				"https://api.deezer.com/track/isrc:" + isrc, True
		).json()

		name = self.download_trackdee(
			url['link'], output,
			quality, recursive_quality,
			recursive_download, interface
		)

		return name

	def download_albumspo(
		self, URL,
		output = stock_output,
		quality = stock_quality,
		recursive_quality = stock_recursive_quality,
		recursive_download = stock_recursive_download,
		interface = stock_interface,
		zips = stock_zip
	):
		if "?" in URL:
			URL,a = URL.split("?")

		try:
			tracks = self.spo.album(URL)
		except Exception as a:
			if not "The access token expired" in str(a):
				raise exceptions.InvalidLink("Invalid link ;)")

			self.spo = Spotify(
				auth=generate_token()
			)

			tracks = self.spo.album(URL)

		try:
			upc = tracks['external_ids']['upc']

			while upc[0] == "0":
				upc = upc[1:]

			url = request("https://api.deezer.com/album/upc:" + upc).json()

			names = self.download_albumdee(
				url['link'], output,
				quality, recursive_quality,
				recursive_download, interface, zips
			)
		except KeyError:
			search = len(
					tracks['tracks']['items']
			) // 8

			try:
				url = self.spo.track(
					tracks['tracks']['items'][search]['external_urls']['spotify']
				)
			except:
				self.spo = Spotify(
					auth=generate_token()
				)

				url = self.spo.track(
					tracks['tracks']['items'][search]['external_urls']['spotify']
				)

			isrc = url['external_ids']['isrc']

			try:
				url = request(
					"https://api.deezer.com/track/isrc:" + isrc, True
				).json()
					
				names = self.download_albumdee(
					url['album']['link'], output,
					quality, recursive_quality,
					recursive_download, interface, zips
				)
			except exceptions.TrackNotFound:
				raise exceptions.AlbumNotFound("Album not found :(")

		return names

	def download_playlistspo(
		self, URL,
		output = stock_output,
		quality = stock_quality,
		recursive_quality = stock_recursive_quality,
		recursive_download = stock_recursive_download,
		interface = stock_interface,
		zips = stock_zip
	):
		array = []

		if "?" in URL:
			URL, a = URL.split("?")

		URL = URL.split("/")

		try:
			tracks = self.spo.user_playlist_tracks(
				URL[-3],
				playlist_id=URL[-1]
			)
		except Exception as a:
			if not "The access token expired" in str(a):
				raise exceptions.InvalidLink("Invalid link ;)")

			self.spo = Spotify(
				auth=generate_token()
			)

			tracks = self.spo.user_playlist_tracks(
					URL[-3],
					playlist_id=URL[-1]
			)

		for a in tracks['items']:
			try:
				array.append(
					self.download_trackspo(
						a['track']['external_urls']['spotify'],
						output, quality,
						recursive_quality, recursive_download, interface
					)
				)
			except:
				print("Track not found :(")
				array.append("None")

		if tracks['total'] != 100:
			for a in range(tracks['total'] // 100):
				try:
					tracks = self.spo.next(tracks)
				except:
					self.spo = Spotify(
						auth=generate_token()
					)

					tracks = self.spo.next(tracks)

				for a in tracks['items']:
					try:
						array.append(
							self.download_trackspo(
								a['track']['external_urls']['spotify'],
								output, quality,
								recursive_quality, recursive_download, interface
							)
						)
					except:
						print("Track not found :(")
						array.append("None")

		if zips:
			zip_name = output + "playlist_" + URL[-1] + ".zip"
			create_zip(zip_name, array)
			return array, zip_name

		return array

	def download_name(
		self, artist, song,
		output = stock_output,
		quality = stock_quality,
		recursive_quality = stock_recursive_quality,
		recursive_download = stock_recursive_download,
		interface = stock_interface
	):

		query = (
			"track:%s artist:%s"
			% (
				song,
				artist
			)
		)

		try:
			search = self.spo.search(q=query)
		except:
			self.spo = Spotify(
				auth=generate_token()
			)

			search = self.spo.search(q=query)

		try:
			return self.download_trackspo(
				search['tracks']['items'][0]['external_urls']['spotify'],
				output, quality,
				recursive_quality, recursive_download, interface
			)
		except IndexError:
			raise exceptions.TrackNotFound("Track not found: " + artist + " - " + song)