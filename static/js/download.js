function back_json(url){
	var req = new XMLHttpRequest();
	req.open("GET", url, false);
	req.send();
	var resp = req.responseText;
	var info = JSON.parse(resp);
	return info;
}

function get(ip, port){
	var e = document.getElementById("inputGroupSelect01");
	var quality = e.options[e.selectedIndex].value;
	var link = document.getElementById("link").value
	var server = "http://" + ip + ":" + port
	var url = server + "/want?link=" + link + "&quality=" + quality;
	var info = back_json(url);
	var n_url;

	if (info.path === undefined){
		n_url = server + "/list?link=" + link + "&quality=" + quality;
	}
	else{
		n_url = info.stream;
	}

	window.location.replace(n_url);
}

function show_playlist(url){
	var info = back_json(url).streams;
	var list = document.getElementById("playlist");
	
	for (a = 0; a < info.length; a++){
		var thing = document.createElement("li");
		var href = document.createElement("a");
		href.setAttribute("href", info[a])
		href.setAttribute("target", "_blank")
		href.innerHTML = "TRACK " + (a + 1);
		thing.classList.add("list-group-item");
		thing.setAttribute("style", "background-color: black; border-color: white; border-style: dashed;");
		thing.appendChild(href);
		list.appendChild(thing);
	}
}