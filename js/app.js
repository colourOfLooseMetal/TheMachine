// The Machine - all front-end page logic (was two inline <script> blocks in MachineFtWams.html).
//
// Loaded once at the end of <body>, so by the time this runs the DOM, jQuery, and the
// emscripten glue (wams.js, which defines the global Module + cwrap) are all already present.
//
// Search round-trip:
//   search()             builds/clears state, then calls wamsSearch(query)
//   wamsSearch           = cwrap wrapper around the C++ `search` export in wams.cpp (see below)
//   wams.cpp             does the fuzzy match, then calls egg(jsonResults) back here via EM_ASM
//   egg(jsonResults)     parses the hits, builds one card per result, renders into #filter-records
//
// Result cards are assembled as HTML strings into outputContent[] and revealed in batches
// (infinite scroll) by loadMore(). Key globals are documented at their declarations below.

		// --- Disabled helpers for a planned "filter by show / search mode" UI ---
		// These pair with the commented-out checkboxes + advanced-search table in
		// MachineFtWams.html. Wire them back up if/when that filter UI is re-enabled.
		//when a search option is checked all other search options are unchecked
		// function advancedSearchCheck() {
		// 	if (document.getElementById("advancedSearch").checked) {
		// 		//console.log("checked")
		// 		document.getElementById("tag").checked = false;
		// 		document.getElementById("episode").checked = false;
		// 	}
		// }
		// function episodeCheck() {
		// 	if (document.getElementById("episode").checked) {
		// 		//console.log("checked")
		// 		document.getElementById("tag").checked = false;
		// 		document.getElementById("advancedSearch").checked = false;
		// 	}
		// }
		// function tagCheck() {
		// 	if (document.getElementById("tag").checked) {
		// 		//console.log("checked")
		// 		document.getElementById("advancedSearch").checked = false;
		// 		document.getElementById("episode").checked = false;
		// 	}
		// }
		//select or deselect all show options when buttton pressed, excludes search option checkboxes
		// function selectAll() {
		// 	x = document.getElementsByClassName("custom-control-input"); // Check
		// 	for (i = 0; i < x.length; i++) {
		// 		if (x[i].id != 'tag' && x[i].id != 'episode' && x[i].id != 'advancedSearch') {
		// 			x[i].checked = true;
		// 		}
		// 	}
		// }
		// function deselectAll() {
		// 	x = document.getElementsByClassName("custom-control-input"); // Check
		// 	for (i = 0; i < x.length; i++) {
		// 		if (x[i].id != 'tag' && x[i].id != 'episode' && x[i].id != 'advancedSearch') {
		// 			x[i].checked = false;
		// 		}
		// 	}
		// }
		// Toggle the .dark-mode class on <body> and every descendant (the CSS keys off it).
		// Wired to the "Toggle dark mode" button in MachineFtWams.html.
		function darkMode() {
			$("body").toggleClass("dark-mode");
			$("body *").toggleClass("dark-mode");
		}
		//download the changes as a txt file
		// Currently unused - was for exporting the contrib-mode caption changeList.
		function download(filename, text) {
			var element = document.createElement('a');
			element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
			element.setAttribute('download', filename);

			element.style.display = 'none';
			document.body.appendChild(element);

			element.click();

			document.body.removeChild(element);
		}

// ---- below was the main <script> block after </body>: search()/egg() and rendering glue ----

	// Infinite scroll: when the viewport hits the bottom of the page, reveal more cards.
	window.onscroll = function (ev) {
		if (window.innerHeight + window.scrollY >= document.body.offsetHeight) {
			loadMore();
		}
	};
	// Reveal the next 10 already-built cards from outputContent[] into #filter-records.
	// outputContentIndex = how many are currently shown; egg() is what fills outputContent[].
	function loadMore() {
		if (outputContentIndex != outputContent.length) {
			if (outputContent.length - 1 > outputContentIndex + 10) {
				$("#filter-records").html(
					outputContent.slice(0, outputContentIndex + 10)
				);
				outputContentIndex += 10;
			} else {
				$("#filter-records").html(
					outputContent.slice(0, outputContent.length)
				);
				outputContentIndex = outputContent.length;
			}
		}
	}

	// Show/hide the full-screen "loading page..." overlay.
	function loadDone()  { document.getElementById("loading").style.display = "none"; }
	function loadStart() { document.getElementById("loading").style.display = ""; }

	// jStringCheck holds the raw result string from C++ so egg() can find the END000 sentinel.
	jStringCheck = '';
	// egg(jsonString): the callback the C++ `search` export invokes (via EM_ASM) with results.
	// jsonString is flat pairs of caption + active-corpus index, ending in a literal sentinel:
	//   ["caption text", corpusIndex, "caption text", corpusIndex, ...]END000
	// We strip END000, JSON.parse, then build one card per [text, index] pair.
	function egg(jsonString) {
		jStringCheck = jsonString;
		//having weird characters leak through so adding end000 at end in c++ then using that, hacky but eh
		// jStringCheck.indexOf("END000")
		jsonString = jsonString.slice(0,jStringCheck.indexOf("END000"));
		// console.log(jsonString.slice(599, 620));
		advResult = JSON.parse(jsonString);
		// console.log(egggggg);
		// $("#filter-records").html(egggggg);
			for (index = 0; index < advResult.length; index+= 2) {
				// console.log(advResult[index])
				advSearchProcessResult(advResult.slice(index, index+2))
				// if (index + 1 >= resultLimit){
				// 	break;
				// }
			}
			$("#filter-records").html("");
		$("#resultsNum").text(count + " results");
		if (outputContent.length < 20) {
			outputContentIndex = outputContent.length - 1;
		} else {
			outputContentIndex = 20;
		}

		$("#filter-records").html(outputContent.slice(0, outputContentIndex));
		// console.log("done");
		console.log("search took:");
		console.timeEnd("searchTimer");
		console.log("ms");
	}
	// Wrap the C++ `search(char*)` export so JS can call it with a normal string.
	// (cwrap + Module come from the emscripten glue in wams.js, loaded in <head>.)
	var wamsSearch = cwrap('search', 'string', ['string']);
	console.log("ayy we out and not in yet");

	// loadedShows: [{key, dir, start, lines}, ...] built as shows are committed.
	// Used by get_dir_and_index_from_biglistnum to map active-corpus index -> show dir + image num.
	var loadedShows = [];
	// Manifest entry list fetched once; cached so checkbox toggles re-use it without re-fetching JSON.
	var g_manifest = null;
	// True when the checkbox selection has changed since the last corpus load.
	// search() rebuilds the corpus before searching if this is set, then clears it.
	var corpusDirty = true;

	// Mobile detection (same regex as the soft-keyboard workaround in the Enter handler),
	// hoisted up here because the prefetch decision below needs it at parse time.
	var g_isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

	// Fetch every show's .txt in parallel (they used to download one at a time).
	// Resolves to an array of ArrayBuffers in the same order as `shows`.
	function fetchShows(shows) {
		return Promise.all(shows.map(function(s) {
			return fetch(s.file).then(function(r) { return r.arrayBuffer(); });
		}));
	}

	// Kick the downloads off at parse time, NOT inside onRuntimeInitialized — the manifest
	// (and on desktop the whole corpus) downloads in parallel with the wasm compile instead
	// of after it. Committing into wasm memory still waits for the runtime, of course.
	var g_manifestPromise = fetch('manifest.json').then(function(r) { return r.json(); });
	// Desktop default is "all shows checked", so prefetch everything; mobile starts with
	// nothing checked, so there's nothing worth prefetching.
	var g_eagerBuffersPromise = g_isMobile ? null : g_manifestPromise.then(function(m) { return fetchShows(m); });

	// Load the selected shows into the wasm corpus (one copy into C++ memory; no JS-side cache).
	// selectedShows: array of manifest entries in the order they should be loaded.
	// prefetched: optional promise of their ArrayBuffers (the eager startup path passes
	// g_eagerBuffersPromise); when absent the fetches start here, all in parallel.
	async function loadSelection(selectedShows, prefetched) {
		loadStart();
		document.getElementById("txt-search").disabled = true;

		Module._clearCorpus();

		var totalBytes = selectedShows.reduce(function(a, s) { return a + s.bytes; }, 0);
		var totalLines = selectedShows.reduce(function(a, s) { return a + s.lines; }, 0);
		Module._reserveCorpus(totalBytes, totalLines); // exact alloc; no realloc during the loop below

		var buffers = await (prefetched || fetchShows(selectedShows));

		loadedShows = [];
		var start = 0;
		for (var si = 0; si < selectedShows.length; si++) {
			var s = selectedShows[si];
			var u8 = new Uint8Array(buffers[si]); // transient — released after HEAPU8.set
			buffers[si] = null;                   // drop our ref so each buffer can GC as we go
			var ptr = Module._showWritePtr(u8.length);        // pointer into g_corpus
			Module.HEAPU8.set(u8, ptr);                       // the ONE copy into wasm memory
			var added = Module._commitShow(u8.length);         // index in place; u8 is now GC-able
			loadedShows.push({ key: s.key, dir: s.dir, start: start, lines: added });
			start += added;
			console.log("loaded " + s.name + ": " + added + " lines");
		}

		document.getElementById("txt-search").disabled = false;
		loadDone();
	}

	// Fires when the .wasm has finished downloading + compiling - only then is searching safe.
	Module.onRuntimeInitialized = async function() {
		console.log("ayy we in");

		// Manifest fetch started at parse time (g_manifestPromise above); usually done by now.
		g_manifest = await g_manifestPromise;

		// Build show-selection checkboxes from manifest (so adding a show needs no HTML edit).
		// Desktop: all checked. Mobile: all unchecked — corpus loads on first search.
		// The template CSS expects <input> + <label> as siblings (not input inside label):
		// input[type="checkbox"] is hidden (opacity:0), label:before draws the box via Font Awesome.
		var container = document.getElementById("checkboxes");
		g_manifest.forEach(function(show) {
			var input = document.createElement('input');
			input.type = 'checkbox';
			input.className = 'show-checkbox';
			input.id = 'show-' + show.key;
			input.checked = !g_isMobile;
			var label = document.createElement('label');
			label.htmlFor = 'show-' + show.key;
			label.textContent = show.name;
			container.appendChild(input);
			container.appendChild(label);
		});

		// Mark dirty when a checkbox changes; corpus rebuilds on next search, not immediately.
		container.addEventListener('change', function() {
			corpusDirty = true;
		});

		// Desktop: load corpus eagerly so the first search is instant.
		// Mobile: nothing is checked, so skip the load — corpus builds on first search.
		var initialSelected = g_manifest.filter(function(s) {
			var cb = document.getElementById('show-' + s.key);
			return cb && cb.checked;
		});
		if (initialSelected.length > 0) {
			// The eager prefetch covers ALL shows in manifest order; only hand it over if the
			// initial selection still matches (a checkbox can't realistically change before
			// the runtime is up, but a stale prefetch here would misalign buffers vs shows).
			var prefetched = (g_eagerBuffersPromise && initialSelected.length === g_manifest.length)
				? g_eagerBuffersPromise : null;
			await loadSelection(initialSelected, prefetched);
			corpusDirty = false;
		} else {
			loadDone(); // nothing to load; hide the loading overlay
		}
		g_eagerBuffersPromise = null; // one-shot; later rebuilds fetch per selection
	};


	// Wire up the search box: pressing Enter runs a search (there's no <form> submit).
	window.addEventListener("load", function () {
		var input = document.getElementById("txt-search");
		input.addEventListener("keyup", function (event) {
			//if the enter key is pressed, dont submit the form
			if (event.keyCode === 13) {
				event.preventDefault();
				search();
				//so the issue is the soft keyboard doesnt go down on mobile when you search, so to make it do that, we check if on mobile, then add a text field, focus on it to drop the keyboard and focus off the
				//search bar, then hide it and remove it, kinda weird lol

				if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
					var field = document.createElement('input');
					field.setAttribute('type', 'text');
					document.body.prepend(field);
					setTimeout(function () {
						field.focus();
						setTimeout(function () {
							field.setAttribute('style', 'display:none;');
							field.remove();
						}, 50);
					}, 50);
				}
			}
		});
		//display "loading page" text until the enormous ammount of json data is loaded along with everything else
		//we will do this in module on load
		//   document.getElementById("loading").style.display = "none";
		console.log("loaded")
	});

	//initialize contribMode variable and changeList which stores text corrections for the images that can be made in contrib mode
	var contribMode = $("#contrib").is(":checked");
	var changeList = [];
	//run the search whenever anything is typed in the search box
	//$("#txt-search").keyup(function () {
	//  search();
	//});

	//function to escape characters in string that would act as regex special characters
	// Currently unused - kept for a future regex / exact-match search mode.
	function escapeRegExp(string) {
		return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	}


	// --- Result render state (shared by search / egg / loadMore) ---
	var count = 0;               // number of result cards built this search (shown as "N results")
	var outputContent = [];      // one HTML string per result card, already in score order
	var outputContentIndex = 0;  // how many of those cards are currently rendered (infinite scroll)


	// the glorious search function - entry point fired by the Search button / Enter key.
	// If corpusDirty (checkbox selection changed since last load), rebuilds the corpus first.
	// Then hands the lowercased query to the wasm engine; the engine calls egg() back when done.
	async function search() {
		var searchField = $("#txt-search").val();
		if (searchField === "") {
			$("#filter-records").html("");
			return;
		}

		if (corpusDirty) {
			var selected = g_manifest ? g_manifest.filter(function(s) {
				var cb = document.getElementById('show-' + s.key);
				return cb && cb.checked;
			}) : [];
			await loadSelection(selected);
			corpusDirty = false;
		}

		console.time("searchTimer");
		$("#filter-records").html("searching");
		outputContentIndex = 0;
		count = 0;
		outputContent = [];
		// query is lowercased because the corpus is all lowercase.
		wamsSearch(searchField.toLowerCase());
	}
	// Map an active-corpus index to [showFolder, perShowImageNumber].
	// loadedShows is built by loadSelection() to mirror the order shows were committed
	// into g_corpus, so this is always in sync with what C++ returns. Binary search
	// since shows are ordered by ascending start offset.
	function get_dir_and_index_from_biglistnum(blNum) {
		var lo = 0, hi = loadedShows.length - 1;
		while (lo < hi) {
			var mid = (lo + hi + 1) >> 1;
			if (loadedShows[mid].start <= blNum) lo = mid;
			else hi = mid - 1;
		}
		var show = loadedShows[lo];
		return [show.dir, blNum - show.start];
	}
	// Build one result card (screenshot + caption + prev/next buttons) and push its HTML onto
	// outputContent[]. resultObj is a single [text, globalIndex] pair handed over by egg().
	// (The "fuse" mention is historical - matching is the wasm engine now, not Fuse.js.)
	function advSearchProcessResult(resultObj) {
		//result object is [text, biglistnum]
		dirNnum = get_dir_and_index_from_biglistnum(resultObj[1])
		var output = "";
		output += '<div class="col-md-6 well">';
		output +=
			'<div class="col-md-3"><img class="img-responsive" id="' + dirNnum[0] + dirNnum[1] + '" object-fit: contain" src="' +
			"https://colourofloosemetal.com/assets/" + dirNnum[0] + "/" +
			dirNnum[1] +
			".jpg" +
			'" alt="' +
			resultObj[0] +
			'" /></div>' +
			'<button  id="' +
			dirNnum[0] + dirNnum[1] +
			'" class="leftBtn">←</button>' +
			'<button  id="' +
			dirNnum[0] + dirNnum[1] +
			'" class="rightBtn">→</button></div>';

		output += '<div class="col-md-7">';

		output += "<h4>" + resultObj[0] + "</h4>";
		output += "<p><small>" + dirNnum[0] + "</small></p>";


		//output += "<h2>" + resultObj["num"] + "</h2>";
		// output += "<h5>" + resultObj["timeStamp"] + "</h5>";
		// score = (1 - resultObj.score) * 100
		// output += "<h5>Score:" + score.toFixed(2) + "</h5>";
		//if the result is a sailor moon one then we will add tags

		//same thing for recess

		//same thing for smCT

		output += "<p><br></p>";
		output += "</div>";
		output += "</div>";
		//console.log(val);
		//this could be modified to have multiple results per row
		//   if (count % 1 == 0) {
		output += '</div><div class="row">';
		//   }
		count++;
		outputContent.push(output);
	}



	//function to display a brief message that disappears after a durration
	// Currently unused - handy for transient "copied!"-style toasts.
	function tempAlert(msg, duration) {
		var el = document.createElement("div");
		el.setAttribute(
			"style",
			"font-size:2em;position:fixed;top:50%;left:70%;"
		);
		el.innerHTML = msg;
		setTimeout(function () {
			el.parentNode.removeChild(el);
		}, duration);
		document.body.appendChild(el);
	}


	// Prev/next image scrubbing: a card's < / > buttons step its screenshot to the neighbouring
	// frame by parsing the number out of the <img> src, +/- 1, and swapping the src back in.
	// Delegated off document.body because the cards are added to the DOM dynamically.
	$(document.body).on("click", ".rightBtn", function (event) {
		//get the id of the button which is the dir and the image number and also the id of the image
		var imgId = $(this).attr("id");
		//console.log(imgId);
		//console.log(document.getElementById(imgId).getAttribute('src'));
		imgScr = document.getElementById(imgId).getAttribute('src');
		imgScr = imgScr.split("/");
		imgPrePath = imgScr.slice(0, -1)
		imgPrePath = imgPrePath.join('/');
		//console.log(imgPrePath);
		imgIndx = imgScr[imgScr.length - 1];
		//console.log(imgIndx);
		imgIndx = imgIndx.substr(0, imgIndx.length - 4);
		//console.log(imgIndx);
		imgIndx = parseInt(imgIndx) + 1;
		//console.log(imgIndx);
		//console.log(imgIndx.toString());
		$('img#' + imgId).attr('src', imgPrePath + '/' + imgIndx + '.jpg');
		//console.log();
	});

	// same as the .rightBtn handler above, but steps the frame backwards (-1).
	$(document.body).on("click", ".leftBtn", function (event) {
		//get the id of the button which is the dir and the image number and also the id of the image
		var imgId = $(this).attr("id");
		//console.log(imgId);
		//console.log(document.getElementById(imgId).getAttribute('src'));
		imgScr = document.getElementById(imgId).getAttribute('src');
		imgScr = imgScr.split("/");
		imgPrePath = imgScr.slice(0, -1)
		imgPrePath = imgPrePath.join('/');
		//console.log(imgPrePath);
		imgIndx = imgScr[imgScr.length - 1];
		//console.log(imgIndx);
		imgIndx = imgIndx.substr(0, imgIndx.length - 4);
		//console.log(imgIndx);
		imgIndx = parseInt(imgIndx) - 1;
		//console.log(imgIndx);
		//console.log(imgIndx.toString());
		$('img#' + imgId).attr('src', imgPrePath + '/' + imgIndx + '.jpg');
		//console.log();
	});


