
$(function () {
	$("#play").click(function () {
		$("#play_progress").toggleClass("hidden");
		var quality = $("#quality").val();
		var link = $("#link").val();
		var url = server + "/want?link=" + link + "&quality=" + quality;
		var n_url;

		if (link.includes("artist")) {
			n_url = server + "/artist?link=" + link;
		} else if (link.includes("album") || link.includes("playlist")) {
			n_url = server + "/playlist?link=" + link + "&quality=" + quality;
		} else {
			var info = back_json(url);
			n_url = info.stream;
		}

		window.location.replace(n_url);
	})
})
