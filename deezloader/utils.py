#!/usr/bin/python3

import zipfile
from os import makedirs
from hashlib import md5
from requests import get
from mutagen import File
from spotipy import oauth2
from deezloader import exceptions
from collections import OrderedDict
from binascii import a2b_hex, b2a_hex
from Crypto.Cipher import AES, Blowfish

from mutagen.id3 import (
	ID3, APIC,
	USLT, _util
)

from mutagen.flac import (
	FLAC, Picture,
	FLACNoHeaderError, error
)

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

header = {
	"Accept-Language": "en-US,en;q=0.5"
}

def generate_token():
	return oauth2.SpotifyClientCredentials(
		client_id = "c6b23f1e91f84b6a9361de16aba0ae17",
		client_secret = "237e355acaa24636abc79f1a089e6204"
	).get_access_token()

def choose_img(image):
	image = request(
		"https://e-cdns-images.dzcdn.net/images/cover/%s/1200x1200-000000-80-0-0.jpg" % image
	).content

	if len(image) == 13:
		image = request("https://e-cdns-images.dzcdn.net/images/cover/1200x1200-000000-80-0-0.jpg").content

	return image

def request(url, control = False):
	try:
		thing = get(url, headers = header)
	except:
		thing = get(url, headers = header)

	if control:
		try:
			if thing.json()['error']['message'] == "no data":
				raise exceptions.NoDataApi("No data avalaible :(")
		except KeyError:
			pass

		try:
			if thing.json()['error']['message'] == "Quota limit exceeded":
				raise exceptions.QuotaExceeded("Too much requests limit yourself")
		except KeyError:
			pass

		try:
			if thing.json()['error']:
				raise exceptions.InvalidLink("Invalid link ;)")
		except KeyError:
			pass

	return thing

def create_zip(zip_name, nams):
	z = zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED)

	for a in nams:
		b = a.split("/")[-1]

		try:
			z.write(a, b)
		except FileNotFoundError:
			pass

	z.close()

def artist_sort(array):
	if len(array) > 1:
		for a in array:
			for b in array:
				if a in b and a != b:
					array.remove(b)

	artists = ", ".join(
		OrderedDict.fromkeys(array)
	)

	return artists

def check_dir(directory):
	try:
		makedirs(directory)
	except FileExistsError:
		pass

def md5hex(data):
	hashed = (
		md5(data)
		.hexdigest()
		.encode()
	)

	return hashed

def genurl(md5, quality, ids, media):
	data = b"\xa4".join(
		a.encode() 
		for a in [md5, quality, ids, str(media)]
	)

	data = b"\xa4".join(
		[md5hex(data), data]
	) + b"\xa4"

	if len(data) % 16:
		data += b"\x00" * (16 - len(data) % 16)

	c = AES.new("jo6aey6haid2Teih".encode(), AES.MODE_ECB)

	media_url = b2a_hex(
		c.encrypt(data)
	).decode()

	return media_url

def calcbfkey(songid):
	h = md5hex(
		b"%d" % int(songid)
	)

	key = b"g4el58wc0zvf9na1"

	return "".join(
		chr(
			h[i] ^ h[i + 16] ^ key[i]
		) for i in range(16)
	)

def blowfishDecrypt(data, key):
	c = Blowfish.new(
		key.encode(), Blowfish.MODE_CBC,
		a2b_hex("0001020304050607")
	)

	return c.decrypt(data)

def decryptfile(fh, key, fo):
	seg = 0

	for data in fh:
		if not data:
			break

		if (seg % 3) == 0 and len(data) == 2048:
			data = blowfishDecrypt(data, key)

		fo.write(data)
		seg += 1

	fo.close()

def var_excape(string):
	string = (
		string
		.replace("\\", "")
		.replace("/", "")
		.replace(":", "")
		.replace("*", "")
		.replace("?", "")
		.replace('"', "")
		.replace("<", "")
		.replace(">", "")
		.replace("|", "")
	)

	return string

def write_tags(song, data):
	try:
		tag = FLAC(song)
		tag.delete()
		images = Picture()
		images.type = 3
		images.data = data['image']
		tag.clear_pictures()
		tag.add_picture(images)
		tag['lyrics'] = data['lyric']
	except FLACNoHeaderError:
		try:
			tag = File(song, easy = True)
		except:
			raise exceptions.TrackNotFound("")
	except error:
		raise exceptions.TrackNotFound("")

	tag['artist'] = data['artist']
	tag['title'] = data['music']
	tag['date'] = data['year']
	tag['album'] = data['album']
	tag['tracknumber'] = data['tracknum']
	tag['discnumber'] = data['discnum']
	tag['genre'] = data['genre']
	tag['albumartist'] = data['ar_album']
	tag['author'] = data['author']
	tag['composer'] = data['composer']
	tag['copyright'] = data['copyright']
	tag['bpm'] = data['bpm']
	tag['length'] = data['duration']
	tag['organization'] = data['label']
	tag['isrc'] = data['isrc']
	tag['replaygain_*_gain'] = data['gain']
	tag['lyricist'] = data['lyricist']
	tag.save()

	try:
		audio = ID3(song)

		audio.add(
			APIC(
				encoding = 3,
				mime = "image/jpeg",
				type = 3,
				desc = u"Cover",
				data = data['image']
			)
		)

		audio.add(
			USLT(
				encoding = 3,
				lang = u"eng",
				desc = u"desc",
				text = data['lyric']
			)
		)

		audio.save()
	except _util.ID3NoHeaderError:
		pass