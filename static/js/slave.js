
function back_json(url) {
	var req = new XMLHttpRequest();
	req.open("GET", url, false);
	req.send();
	var resp = req.responseText;
	var info = JSON.parse(resp);
	return info;
}

self.addEventListener("message", function (e) {
	var url = e.data;
	var info = back_json(url);
	self.postMessage(info);
})
