function get_traces(file, cb){
	var req = new XMLHttpRequest();
	req.onreadystatechange = function(){
		if (req.readyState === XMLHttpRequest.DONE) {
			if (req.status === 200) {
				var o = JSON.parse(req.responseText);
				cb(o);
			}
		}
	}
	req.open("GET", file);
	req.send();
}

function init_map() {
	var map = L.map('map');

	// create the tile layer with correct attribution
	var osmUrl='http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
	var osmAttrib='Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors';
	var osm = new L.TileLayer(osmUrl, {minZoom: 1, maxZoom: 12, attribution: osmAttrib});

	map.addLayer(osm);

	return map;
}

var m = init_map('map');

var plotlayers=[];

function removeMarkers() {
	for (i=0;i<plotlayers.length;i++) {
		map.removeLayer(plotlayers[i]);
	}
	plotlayers=[];
}

function draw_trace(trace, af){
	var afcolor = 'red';
	if (af == 6) afcolor = 'blue';

	var lasthoprtt = 0;
	var res = trace.trace.result;
	var lasthoppos, lastpos;
	function show_hop(i) {
		if (i>=res.length) return;
		var hop = res[i].result[0]; // XXX
		var geo = trace.geoips[hop.from];
		var pos = undefined;
		if (geo) {
			pos = new L.LatLng(geo.lat, geo.lon);
			if (lasthoppos) {
				var line = L.polyline([lasthoppos, pos], {color: afcolor});
				m.addLayer(line);
				plotlayers.push(line);
			} else if (lastpos) {
				var line = L.polyline([lastpos, pos], {color: afcolor, dashArray: [5, 10]});
				m.addLayer(line);
				plotlayers.push(line);
			}
			var marker = new L.circleMarker(pos, { color: afcolor, opacity: 0.5 });
			m.addLayer(marker);
			plotlayers.push(marker);
		}
		lasthoppos = pos;
		if (pos) lastpos = pos;
		var wait = 10*(hop.rtt-lasthoprtt);
		lasthoprtt = hop.rtt;

		setTimeout(function(){
			show_hop(i+1);
		}, wait);
	}
	show_hop(0);
}

var alltraces

function show_trace(traceid) {
	if (!alltraces) return;
	var trace = alltraces[traceid];
	document.getElementById('srcprobe').innerHTML = trace[4].src.id + ' (AS' + trace[4].src.asn + ')';
	document.getElementById('dstprobe').innerHTML = trace[4].dst.id + ' (AS' + trace[4].dst.asn + ')';
	console.log(trace);
	removeMarkers();
	var locs = [];
	var bounds = new L.LatLngBounds();
	var geoips = trace[4].geoips;
	for (k in geoips) {
		var gip = geoips[k];
		var pos = new L.LatLng(gip.lat, gip.lon);
		bounds.extend(pos);
		//m.addLayer(new L.Marker(pos));
		//plotlayers.push(marker);
	}
	var geoips = trace[6].geoips;
	for (k in geoips) {
		var gip = geoips[k];
		var pos = new L.LatLng(gip.lat, gip.lon);
		bounds.extend(pos);
		//m.addLayer(new L.circleMarker(pos));
	}
	m.fitBounds(bounds);
	draw_trace(trace[4], 4);
	draw_trace(trace[6], 6);
}

var curtrace = 7;

function next_trace() {
	curtrace++;
	if (curtrace >= traces.length) curtrace = 0;
	show_trace(curtrace);
}

get_traces('geocodedtraces.json', function(traces){
	alltraces = traces;
	show_trace(curtrace);
});


