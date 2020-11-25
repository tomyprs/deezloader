
function show_artist(access_token, name) {
	headers = {
		"Authorization": "Bearer " + access_token
	}

	var api_search_spotify = api_spotify + "search?q=artist:" + name + "&type=artist"

	$.ajax({
		type: "GET",
		url: api_search_spotify,
		headers: headers,
		success: function (json) {
			var l = json['artists']['items'].length
			var where = $("#artists");
			where.empty();
			var html = "";
			var times = 0;

			for (a = 0; a < l; a++) {
				var c = json['artists']['items'][a];
				var link = c['external_urls']['spotify'] + "?";
				link = server + "/artist?link=" + link + "&quality=MP3_320";

				if (c['images'].length !== 0) {
					var image = c['images'][0]['url'];
				} else {
					var image = song_default_image;
				}

				var name = c['name'];

				if (a % 4 === 0) {
					html += "<div class="card-group">";
				}

				html += "<div class="card">";
				html += "<img src="" + image + "" class="card-img-top" alt="artist picture">";
				html += "<div class="card-body">";
				html += "<h5 class="card-title">" + name + "</h5>";
				html += "<a href="" + link + "" class="btn btn-primary artist">SHOW ALBUM</a></div>";
				html += "<br></div><br/>";
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

$(function () {
	$("#look").click(function () {
		$("#play_progress").toggleClass("hidden");
		var name = $("#search").val();
		$("#artists").empty();

		$.ajax({
			type: "POST",
			url: OAUTH_TOKEN_URL,
			data: data,
			headers: headers_token,
			success: function (json) {
				var accesstoken = json['access_token'];
				show_artist(accesstoken, name);
			}
		})

		$("#play_progress").toggleClass("hidden");

	})
})
