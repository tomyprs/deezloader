
function show_album_spotify(access_token, link) {
	var headers = get_headers(access_token);
	var ids = get_ids(link);
	var api_artist = api_spotify + "artists/" + ids + "/albums";

	$.ajax({
		type: "GET",
		url: api_artist,
		headers: headers,
		success: function (json) {
			var l = json['items'].length
			var where = $("#albums");
			where.empty();
			var html = "";
			var times = 0;

			for (a = 0; a < l; a++) {
				var c = json['items'][a];
				var link = c['external_urls']['spotify'] + "?";
				link = server + "/playlist?link=" + link + "&quality=MP3_320";
				var image = c['images'][0]['url'];
				var album_name = c['name'];

				if (a % 4 === 0) {
					html += "<div class="card-group">";
				}

				html += "<div class="card">";
				html += "<img src="" + image + "" class="card-img-top" alt="album picture">";
				html += "<div class="card-body">";
				html += "<h5 class="card-title">" + album_name + "</h5>";
				html += "<a href="" + link + "" class="btn btn-primary song">LISTEN</a></div>";
				html += "<br><select class="custom-select" id="quality">";
				html += "<option value="FLAC">FLAC</option>";
				html += "<option value="MP3_320" selected>320</option>";
				html += "<option value="MP3_256">256</option>";
				html += "<option value="MP3_128">128</option>";
				html += "</select></div><br/>";
				times++;

				if (times === 4) {
					html += "</div>";
					times = 0;
				}
			}

			html += "</div>"
			where.append(html);
		}
	})
}

function show_album_deezer(url) {
	var ids = get_ids(url);
	var api_artist = api_deezer + "artist/" + ids + "/albums";
	var json = back_json(api_artist);
	var l = json['data'].length
	var where = $("#albums");
	where.empty();
	var html = "";
	var times = 0;

	for (a = 0; a < l; a++) {
		var c = json['data'][a];
		var link = c['link'] + "?";
		link = server + "/playlist?link=" + link + "&quality=MP3_320";
		var image = c['cover_xl'];
		var album_name = c['title'];

		if (a % 4 === 0) {
			html += "<div class="card-group">";
		}

		html += "<div class="card">";
		html += "<img src="" + image + "" class="card-img-top" alt="album picture">";
		html += "<div class="card-body">";
		html += "<h5 class="card-title">" + album_name + "</h5>";
		html += "<a href="" + link + "" class="btn btn-primary song">LISTEN</a></div>";
		html += "<br><select class="custom-select" id="quality">";
		html += "<option value="FLAC">FLAC</option>";
		html += "<option value="MP3_320" selected>320</option>";
		html += "<option value="MP3_256">256</option>";
		html += "<option value="MP3_128">128</option>";
		html += "</select></div><br/>";
		times++;

		if (times === 4) {
			html += "</div>";
			times = 0;
		}
	}

	html += "</div>"
	where.append(html);
}

function get_api(link) {
	if (link.includes("artist")) {
		if (link.includes("spotify")) {
			$.ajax({
				type: "POST",
				url: OAUTH_TOKEN_URL,
				data: data,
				headers: headers_token,
				success: function (json) {
					var accesstoken = json['access_token'];
					show_album_spotify(accesstoken, link);
				}
			})
		} else if (link.includes("deezer")) {
			show_album_deezer(link)
		}
	}
}

$(function () {
	var link = $("#artist_link").html()
	get_api(link);

	$(document).on("change", "#quality", function () {
		var href = $(this).closest(".card").find("a");
		var c_quality = $(this).val();
		var s_href = href.attr("href").split("=");
		s_href[2] = c_quality;
		var link = s_href.join("=");
		href.attr("href", link);
	})
})
