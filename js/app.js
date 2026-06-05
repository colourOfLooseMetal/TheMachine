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

	// Hide the full-screen "loading page..." overlay; called once the wasm runtime is ready.
	function loadDone() {
		document.getElementById("loading").style.display = "none";
	}

	// jStringCheck holds the raw result string from C++ so egg() can find the END000 sentinel.
	jStringCheck = '';
	// egg(jsonString): the callback the C++ `search` export invokes (via EM_ASM) with results.
	// jsonString is flat pairs of caption + global corpus index, ending in a literal sentinel:
	//   ["caption text", globalIndex, "caption text", globalIndex, ...]END000
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
	// Fires when the .wasm has finished downloading + compiling - only then is searching safe,
	// so we drop the loading overlay here rather than on the window 'load' event.
	Module.onRuntimeInitialized = () => {
		console.log("ayy we in");


		// console.log("After wrapping with cwrap: ", wGreet('hello')); //hello Ajay Kumar because ajay were passed previously
		// const wamsSearch = Module.cwrap("search", 'string', ['string']);  //wrap original c++ function
		// wamsSearch("hello");
		loadDone();
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
	// Clears render state, then hands the lowercased query to the wasm engine; the engine
	// calls egg() back when done, which is what actually renders the results.
	function search() {
		console.time("searchTimer")
		
		$("#filter-records").html("searching");
		outputContentIndex = 0;
		count = 0;
		outputContent = [];
		// resultLimit = $("#maxResults option:selected").val();
		// contribMode = $("#contrib").is(":checked");
		var searchField = $("#txt-search").val();
		if (searchField === "") {
			$("#filter-records").html("");
			return;
		}
		// query is lowercased because the corpus (mapTextData in C++) is all lowercase.
		//wams search will then call egg when done to process results
		wamsSearch(searchField.toLowerCase());

		



	}
	// Map a global corpus index (0..365696) to [showFolder, perShowImageNumber].
	// mapTextData in C++ is every show concatenated, so these ranges MUST stay in sync with the
	// index map in wams.cpp (and CLAUDE.md). The image then loads from /assets/<dir>/<num>.jpg.
	function get_dir_and_index_from_biglistnum(blNum){
		//convert something like 34323 to sm 34323 and same for others
		dir = "";
		num = blNum;
		if(blNum >= 0 && blNum < 60941){
			dir = "sm";
		}
		else if(blNum >= 60941 && blNum < 61838){
			dir = "cw2003";
			num = num - 60941;
		}
		else if(blNum >= 61838 && blNum < 65820){
			dir = "swPrequel";
			num = num - 61838;
		}
		else if(blNum >= 65820 && blNum < 98080){
			dir = "recess";
			num = num - 65820;
		}
		else if(blNum >= 98080 && blNum < 142918){
			dir = "DisPix";
			num = num - 98080;
		}												
		else if(blNum >= 142918 && blNum < 167909){
			dir = "JohnnyBravo";
			num = num - 142918;
		}
		else if(blNum >= 167909 && blNum < 194672){
			dir = "ghibli";
			num = num - 167909;
		}
		else if(blNum >= 194672 && blNum < 214152){
			dir = "looneyTunes";
			num = num - 194672;
		}
		else if(blNum >= 214152 && blNum < 245632){
			dir = "db";
			num = num - 214152;
		}
		else if(blNum >= 245632 && blNum < 305584){
			dir = "dbz";
			num = num - 245632;
		}
		else if(blNum >= 305584 && blNum < 314267){
			dir = "dbzMov";
			num = num - 305584;
		}
		else if(blNum >= 314267 && blNum <= 365697){
			dir = "jojo";
			num = num - 314267;
		}
		return([dir,num]);

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
			"http://colourofloosemetal.com/assets/" + dirNnum[0] + "/" +
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


