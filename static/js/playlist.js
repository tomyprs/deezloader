
function show_album_spotify(access_token, url) {
	var headers = get_headers(access_token);
	var ids = get_ids(url);
	var api_album_spotify = api_spotify + "albums/" + ids;

	$.ajax({
		type: "GET",
		url: api_album_spotify,
		headers: headers,
		success: function (json) {
			var image = json['images'][0]['url'];
			var label = json['label'];
			var genres = json['genres'].join(",");
			var album = json['name'];
			var artist = json['artists'][0];
			var artist_name = artist['name'];
			var artist_link = artist['external_urls']['spotify'];
			var api_artist = artist['href'];

			$.ajax({
				type: "GET",
				url: api_artist,
				headers: headers,
				success: function (json) {
					var artist_image = json['images'][0]['url'];
					$("#artist-art").attr("src", artist_image);
				}
			})

			var redirect_artist = server + "/artist?link=" + artist_link;
			var artist_link_html = "<a id="redirect-artist" href="" + redirect_artist + "" target="_blank">" + artist_name + "</a>";
			$("#artist-name").html(artist_link_html);
			$("#bg-artwork").css("background-image", "url(" + image + ")");
			$("#album-art").attr("src", image);
			$("#album-title").html(album);
			$("#genre").html(genres);
			$("#label").html(label);
			var url = $(".url").val();
			var slave = new Worker(slaver);

			slave.addEventListener("message", function (e) {
				var info = e.data;
				console.log(info);
				var list = $("#songs");
				var tracks = json['tracks']['items'];
				var downloads = info.downloads;
				var plays = info.streams;

				for (a = 0; a < tracks.length; a++) {
					var c = tracks[a];
					var song = c['name'];
					var duration = c['duration_ms'];
					var html = "<li><div class="hidden">" + downloads[a] + "</div>";
					html += "<div class="control"><div class="button play" id="play"></div></div>";
					var play_href = "<a id="redirect-player" href="" + plays[a] + "">"
					html += "<span>" + play_href + song + "</a></span><span>" + duration + "</span></li>";
					list.append(html);
				}

				$("#load").remove();

			})

			slave.postMessage(url);

		}
	})
}

function show_album_deezer(url) {
	var ids = get_ids(url);
	var api_album_deezer = api_deezer + "album/" + ids;
	var json = back_json(api_album_deezer);
	var image = json['cover_xl'];
	var label = json['label'];
	var genress = json['genres']['data'];
	var genres = [];

	for (var a = 0; a < genress.length; a++) {
		var genre = genress[a]['name'];
		genres.push(genre);
	}

	genres = genres.join("&");
	var artist_image = json['artist']['picture_xl'];
	var artist_name = json['artist']['name'];
	var album = json['title'];
	var id_artist = json['artist']['id'];
	var api_artist = api_deezer + "artist/" + id_artist;
	var redirect_artist = server + "/artist?link=" + api_artist;
	var artist_link_html = "<a id="redirect-artist" href="" + redirect_artist + "" target="_blank">" + artist_name + "</a>";
	$("#artist-art").attr("src", artist_image);
	$("#artist-name").html(artist_link_html);
	$("#bg-artwork").css("background-image", "url(" + image + ")");
	$("#album-art").attr("src", image);
	$("#album-title").html(album);
	$("#genre").html(genres);
	$("#label").html(label);
	var url = $(".url").val();
	var slave = new Worker(slaver);

	slave.addEventListener("message", function (e) {
		var info = e.data;
		var list = $("#songs");
		var tracks = json['tracks']['data'];
		var downloads = info.downloads;
		var plays = info.streams;

		for (a = 0; a < tracks.length; a++) {
			var c = tracks[a];
			var song = c['title'];
			var duration = c['duration'];
			var html = "<li><div class="hidden">" + downloads[a] + "</div>";
			html += "<div class="control"><div class="button play" id="play"></div></div>";
			var play_href = "<a id="redirect-player" href="" + plays[a] + "">"
			html += "<span>" + play_href + song + "</a></span><span>" + duration + "</span></li>";
			list.append(html);
		}

		$("#load").remove();

	})

	slave.postMessage(url);

}

function show_playlist_spotify(access_token, url) {
	var headers = get_headers(access_token);
	var ids = get_ids(url);
	var api_playlist_spotify = api_spotify + "playlists/" + ids;

	$.ajax({
		type: "GET",
		url: api_playlist_spotify,
		headers: headers,
		success: function (json) {
			var image = json['images'][0]['url'];
			var label = "";
			var genres = "";
			var album = json['name'];
			var artist_name = json['owner']['display_name'];
			var api_artist_spotify = json['owner']['href'];

			$.ajax({
				type: "GET",
				url: api_artist_spotify,
				headers: headers,
				success: function (json) {
					if (json['images'].length !== 0) {
						var artist_image = json['images'][0]['url'];
					} else {
						var artist_image = song_default_image;
					}

					$("#artist-art").attr("src", artist_image);
				}
			})

			$("#artist-name").html(artist_name);
			$("#bg-artwork").css("background-image", "url(" + image + ")");
			$("#album-art").attr("src", image);
			$("#album-title").html(album);
			$("#genre").html(genres);
			$("#label").html(label);
			var url = $(".url").val();
			var slave = new Worker(slaver);

			slave.addEventListener("message", function (e) {
				var info = e.data;
				var list = $("#songs");
				var tracks = json['tracks']['items'];

				for (a = 0; a < info.length; a++) {
					var c = tracks[a]['track'];
					var song = c['name'];
					var duration = c['duration_ms'];
					var html = "<li>";
					html += "<div class="hidden">" + info[a] + "</div>";
					html += "<div class="control"><div class="button play" id="play"></div></div>";
					html += "<span>" + song + "</span><span>" + duration + "</span></li>";
					list.append(html);
				}

				$("#load").remove();

			})

			slave.postMessage(url);

		}
	})
}

function show_playlist_deezer(url) {
	var ids = get_ids(url);
	var api_playlist_deezer = api_deezer + "playlist/" + ids;
	var json = back_json(api_playlist_deezer);
	var image = json['picture_xl'];
	var duration = json['duration'];
	var nb_tracks = json['nb_tracks'];
	var api_artist_deezer = api_deezer + "user/" + json['creator']['id'];
	var artist_image = back_json(api_artist_deezer)['picture_xl'];
	var artist_name = json['creator']['name'];
	var album = json['title'];
	$("#artist-art").attr("src", artist_image);
	$("#artist-name").html(artist_name);
	$("#bg-artwork").css("background-image", "url(" + image + ")");
	$("#album-art").attr("src", image);
	$("#album-title").html(album);
	$("#genre").html(duration);
	$("#label").html(nb_tracks);
	var url = $(".url").val();
	var slave = new Worker(slaver);

	slave.addEventListener("message", function (e) {
		var info = e.data;
		var list = $("#songs");
		var tracks = json['tracks']['data'];

		for (a = 0; a < info.length; a++) {
			var c = tracks[a];
			var song = c['title'];
			var duration = c['duration'];
			var html = "<li>";
			html += "<div class="hidden">" + info[a] + "</div>";
			html += "<div class="control"><div class="button play" id="play"></div></div>";
			html += "<span>" + song + "</span><span>" + duration + "</span></li>";
			list.append(html);
		}

		$("#load").remove();

	})

	slave.postMessage(url);

}

function get_api(url) {
	if (url.includes("album")) {
		if (url.includes("spotify")) {
			$.ajax({
				type: "POST",
				url: OAUTH_TOKEN_URL,
				data: data,
				headers: headers_token,
				success: function (json) {
					var accesstoken = json['access_token'];
					show_album_spotify(accesstoken, url);
				}
			})
		} else if (url.includes("deezer")) {
			url = url.replace("&quality", "")
			show_album_deezer(url)
		}
	} else if (url.includes("playlist")) {
		if (url.includes("spotify")) {
			$.ajax({
				type: "POST",
				url: OAUTH_TOKEN_URL,
				data: data,
				headers: headers_token,
				success: function (json) {
					var accesstoken = json['access_token'];
					show_playlist_spotify(accesstoken, url);
				}
			})
		} else if (url.includes("deezer")) {
			url = url.replace("&quality", "")
			show_playlist_deezer(url)
		}
	}
}

$(function () {
	var url = $(".url").val();
	var s_href = url.split("=");
	get_api(s_href[1]);
	var audio = new Audio();

	$(document).on("click", "#play", function () {
		var which = $(this).closest("li");

		var audio_link = (
			which
			.find("div")
			.html()
			.replace(/ /g, "%20")
		);

		console.log(audio_link);

		if (audio.src !== audio_link) {
			audio.pause();
			audio.src = audio_link;
			var all = $(".pause");
			all.removeClass("pause");
			all.addClass("play");
		}

		var who = which.find("#play");

		if (audio.paused) {
			audio.src = audio_link;
			audio.play();
			who.removeClass("play");
			who.addClass("pause");
		} else {
			audio.pause();
			who.removeClass("pause");
			who.addClass("play");
		}
	})

	$(".plays").click(function () {
		var audio_link = (
			$("ol")
			.first()
			.find("div")
			.html()
		);

		audio.src = audio_link;

		if (audio.paused) {
			audio.play();
		} else {
			audio.pause();
		}
	})
})
