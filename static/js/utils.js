
var ip = "127.0.0.1";
var port = "8000";
var server = "http://" + ip + ":" + port;
var slaver = "js/slave.js";
var client_id = "c6b23f1e91f84b6a9361de16aba0ae17";
var client_secret = "237e355acaa24636abc79f1a089e6204";
var OAUTH_TOKEN_URL = "https://accounts.spotify.com/api/token";
var api_spotify = "https://api.spotify.com/v1/";
var api_deezer = "https://cors-anywhere.herokuapp.com/https://api.deezer.com/";
var auth_header = btoa(client_id + ":" + client_secret);
var song_default_image = "https://e-cdns-images.dzcdn.net/images/cover/640x640-000000-80-0-0.jpg";

var data = {
	"grant_type": "client_credentials"
}

var headers_token = {
	"Authorization": "Basic " + auth_header
}

function back_json(url) {
	var req = new XMLHttpRequest();
	req.open("GET", url, false);
	req.send();
	var resp = req.responseText;
	var info = JSON.parse(resp);
	return info;
}

function get_ids(url) {
	var ids = (
		url
		.split("?")[0]
		.split("/")
		.slice(-1)[0]
	)

	return ids;
}

function get_headers(access_token) {
	headers = {
		"Authorization": "Bearer " + access_token
	}

	return headers;
}
