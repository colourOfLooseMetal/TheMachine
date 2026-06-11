// ============================================================================
//  wams.cpp - "Web Assembly Machine Searcher", the search engine for The Machine.
//
//  Fuzzy-matches a query against caption lines loaded at runtime into g_corpus
//  (loaded from per-show .txt files by JS; see reserveCorpus/showWritePtr/commitShow)
//  and returns the best ~450 hits to the page.
//
//  Pipeline (all driven by cppSearch -> the extern "C" search() wasm export):
//    Stage 1  SearchStringFuzzy    fuzzy Bitap filter, edit distance <= queryLen/2
//                                  (pattern mask + R rows are prepped ONCE per search
//                                  in cppSearch, not per line - that prep used to be
//                                  most of stage 1's cost). Hits go into g_survivors.
//    Stage 2  jaro_sliding_window  Jaro-style sliding-window scoring of survivors
//    Stage 3  partial_sort         sorts just the survivors for the top 450
//                                  (replaced hashSortIndices, the old counting sort
//                                  over ALL g_totalLines scores)
//    Return   Scores::to_json      pack top 450 as ["text",index,...]END000, then
//                                  hand to JS by calling egg(json) via EM_ASM
//
//  Two build targets (see the emcc command at the very bottom of this file):
//    - wasm:   the extern "C" search() export the web page calls through cwrap
//    - native: a g++ debug build that runs main() - the emscripten bits are behind
//              #ifdef __EMSCRIPTEN__ now, so plain `g++ -O3 wams.cpp` just works.
//              Usage: ./a.out "<query>" data/sm.txt [more .txt ...]
//
//  Flip the global `cLog` (just below the includes) to true for per-search
//  stdout/console tracing. Corpus size is g_totalLines (set as shows are loaded).
// ============================================================================
#include <iostream>
#include <limits.h>
#include <string>
#include <algorithm>
#include <vector>
#include <numeric>
#include <map>
#include <fstream>
#include <chrono>
#include <cctype>

#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#endif
#include <cstring>

#include <sstream>
#include <iomanip>

using namespace std::chrono;
const bool cLog = false; // console.log

// ---- Corpus store (runtime-loaded; replaces static data.cpp / mapTextData) --
// All loaded caption lines concatenated, each '\0'-terminated.
// g_lineOffsets[i] is the byte offset of line i within g_corpus.
// JS loads shows via reserveCorpus / showWritePtr / commitShow (see exports below).
std::string           g_corpus;
std::vector<uint32_t> g_lineOffsets;
int                   g_totalLines = 0;

inline const char* lineAt(int i) { return g_corpus.data() + g_lineOffsets[i]; }

// Line length without strlen: lines are packed back to back, so it's just the gap to the
// next offset minus the '\0' (the last line ends at the end of the corpus).
inline int lineLen(int i) {
    size_t end = (i + 1 < g_totalLines) ? (size_t)g_lineOffsets[i + 1] : g_corpus.size();
    return (int)(end - g_lineOffsets[i] - 1);
}

// ---- Per-search survivor list ------------------------------------------------
// Replaces the old full-corpus work arrays (scoresArr/sortedIndices/g_bitSet/
// g_matchIndex) - those needed ~5MB of fills per search and a counting sort over
// every line. Stage 1 pushes one entry per bitap hit, stage 2 fills in the score,
// stage 3 partial_sorts just these.
struct Survivor {
    int    line;     // index into g_lineOffsets
    short  matchIdx; // where in the line stage 1's bitap found the hit
    double score;    // filled in by stage 2
};
std::vector<Survivor> g_survivors;

// ---- Corpus management exports (called from JS) ------------------------------

// Call once per selection before the per-show showWritePtr/commitShow loop.
// Reserves exact capacity so subsequent resizes never reallocate (no wasm memory growth mid-loop).
extern "C" void reserveCorpus(int totalBytes, int totalLines) {
    g_corpus.reserve((size_t)totalBytes);
    g_lineOffsets.reserve((size_t)totalLines);
}

// Grow g_corpus by byteLen and return a pointer to the new region.
// JS then does Module.HEAPU8.set(showBytes, ptr) — the ONE copy into the store.
// Precondition: reserveCorpus was called first (no realloc, pointer stays valid).
extern "C" char* showWritePtr(int byteLen) {
    size_t off = g_corpus.size();
    g_corpus.resize(off + (size_t)byteLen);
    return &g_corpus[off];
}

// Index the bytes JS just wrote: replace each '\n' with '\0', record line offsets.
// The .txt file must end with '\n' (getKeyFromJson.py guarantees this) so the
// trailing '\n' becomes the null terminator for the last line. Returns #lines added.
extern "C" int commitShow(int byteLen) {
    if (byteLen <= 0) return 0;
    size_t regionStart = g_corpus.size() - (size_t)byteLen;
    int linesAdded = 0;
    size_t lineStart = regionStart;
    for (size_t i = regionStart; i < g_corpus.size(); i++) {
        if (g_corpus[i] == '\n') {
            g_lineOffsets.push_back((uint32_t)lineStart);
            g_corpus[i] = '\0';
            lineStart = i + 1;
            linesAdded++;
        }
    }
    // Safeguard: if the region didn't end with '\n', null-terminate the last line.
    if (lineStart < g_corpus.size()) {
        g_lineOffsets.push_back((uint32_t)lineStart);
        g_corpus.push_back('\0');
        linesAdded++;
    }
    g_totalLines += linesAdded;
    return linesAdded;
}

// Free all corpus memory (swap idiom actually releases capacity) and reset state.
extern "C" void clearCorpus() {
    std::string().swap(g_corpus);
    std::vector<uint32_t>().swap(g_lineOffsets);
    std::vector<Survivor>().swap(g_survivors);
    g_totalLines = 0;
}

auto start = high_resolution_clock::now();



//escape special characters in json string so we dont reach unexpected end of file
//(builds straight into a plain string now - the old per-result ostringstream was slow)
std::string escape_json(const std::string &s) {
    static const char* hexDigits = "0123456789abcdef";
    std::string o;
    o.reserve(s.size());
    for (auto c = s.cbegin(); c != s.cend(); c++) {
        unsigned char u = (unsigned char)*c;
        if (u == '"' || u == '\\' || u <= 0x1f) {
            o += "\\u00";
            o += hexDigits[u >> 4];
            o += hexDigits[u & 0xf];
        } else {
            o += (char)u;
        }
    }
    return o;
}

// (hashSortIndices, the O(n) counting sort over every line's score, used to live here.
// It's gone - stage 3 is now a partial_sort over just the survivors at the end of
// cppSearch, so there's nothing to sort for the ~99% of lines the bitap filtered out.)

// Debug-only: dump the top 100 results (caption + score) in sorted order to stdout.
// Only reached when cLog is true (see the gated call at the end of cppSearch).
void printArray(int topN)
{
	for (int i = 0; i < topN && i < 100; i++)
	{
		std::cout << lineAt(g_survivors[i].line) << " " << g_survivors[i].score << "\n";
		std::cout << "\n";
	}
}

// The query padded with spaces, built ONCE per search in cppSearch. The sliding window
// used to rebuild " "+query+" " (and substr the line) on every single slide step.
struct PaddedQuery {
	std::string q;    // the raw query
	std::string pre;  // " " + q
	std::string suf;  // q + " "
	std::string both; // " " + q + " "
};

// so this isnt the jaro algoritim, and this isnt the sliding window search, this gets called when the query is longer than the text we are searching, it wouldnt be a bad idea to slide the searched text over the query
//i guess the same way we slide the query over the searched text in the next function, ill explain the scoring in the next function, i dont actually know how all of this function works lol, i mean i kinda do, but the guts are jaro
//and then i change the scoring
//(s1/s2 are raw pointers now - only the first l1/l2 chars are read, no copies)
double jaro_actual_search(const char* s1, const char* s2, int l1, int l2, const int match_distance)
{
	if (l1 == 0)
	{
		return l2 == 0 ? 1.0 : 0.0;
	}

	// const int match_distance = l2 / 2 - 1;
	bool s1_matches[l1];
	bool s2_matches[l2];
	std::fill(s1_matches, s1_matches + l1, false);
	std::fill(s2_matches, s2_matches + l2, false);
	// int matches = 0;
	int actualMatches = 0;
	for (int i = 0; i < l1; i++)
	{
		const int end = std::min(i + match_distance + 1, l2);
		for (int k = std::max(0, i - match_distance); k < end; k++)
			if (!s2_matches[k] && s1[i] == s2[k])
			{
				s1_matches[i] = true;
				s2_matches[k] = true;
				// matches++;
				break;
			}
	}

	// if (matches == 0)
	// 	return 0.0;
	double t = 0.0;
	for (int i = 0; i < l1; i++)
		if (s1_matches[i])
		{
			if (s2[i] != s1[i])
			{
				t += 0.1;
			}
			else
			{
				actualMatches += 1;
			}
		}

	// const double m = matches;
	if (cLog)
	{
		std::cout << " actM:" << actualMatches << " t:" << t << "\n";
	}
	double score = ((actualMatches + t) / l2);
	if (cLog)
	{
		std::cout << ":scoreNonWindow:" << score;
	}

	return (score);
}

/// s2 is pattern/query
// The windowed scorer that jaro_sliding_window calls for each window position.
// s1 = a slice of the caption line (raw pointer into g_corpus, NOT null-terminated at l1,
// only the first l1 chars are valid); s2 = the query padded with a leading/trailing space.
// addedPatLen = how many padding spaces were added; extraSpaceLoc says where they are
// (0 both / 1 prefix / 2 suffix) so matched padding can be discounted from the denominator.
// Returns a score in [0,1]; see the worked 'hello' / 'hellzo' example inside the body.
//so like i said earlier, guts are jaro (not jaro winkler)
double jaro_actual_search_but_with_window_bs(const char* s1, const char* s2, int l1, int l2, int addedPatLen, int extraSpaceLoc, const int match_distance)
{
	if (cLog)
	{
		std::cout << ":" << std::string(s2, l2) << ":"
				  << ":" << std::string(s1, l1) << ":" << l1 << "," << l2 << "\n";
	}

	if (l1 == 0)
	{
		return l2 == 0 ? 1.0 : 0.0;
	}
	// int msl = std::max(l1, l2);
	// msl = std::max(msl, 6);
	// const int match_distance = std::min(msl,8) / 2 - 1; //min 2 max 3 //this can be calced once not each time
	// const int match_distance = l2 / 2 - 1;
	bool s1_matches[l1];
	bool s2_matches[l2];
	std::fill(s1_matches, s1_matches + l1, false);
	std::fill(s2_matches, s2_matches + l2, false);
	// int matches = 0;
	double actualMatches = 0;
	for (int i = 0; i < l1; i++)
	{
		const int end = std::min(i + match_distance + 1, l2);
		for (int k = std::max(0, i - match_distance); k < end; k++)
			if (!s2_matches[k] && s1[i] == s2[k])
			{
				s1_matches[i] = true;
				s2_matches[k] = true;
				// matches++;
				break;
			}
	}

	// if (matches == 0)
	// 	return 0.0;
	double t = 0.0;
	// int k = 0;
	//for every character that matches but..
	for (int i = 0; i < l1; i++)
		if (s1_matches[i])
		{//if the character is not in the correct spot but is one space off (since our match distance is alwways 2)
			if (s2[i] != s1[i])
			{
				//add a small amout to t
				t += 0.1;
			}
			else
			{
				//otherwise add 1 to actual matches
				actualMatches += 1;
			}
		}

	// const double m = matches;
	if (cLog)
	{
		std::cout << " actM:" << actualMatches << " t:" << t << "\n";
		std::cout << "extraspaceLoc " << extraSpaceLoc << "\n";
	}
	//if we have extra space added before or after the query string to check for characters out of place beyond the length of the query string
	// extraSpaceLoc is 0 for before and after 1 for prefix 2 for suffix
	if (extraSpaceLoc == 2)
	{
		//if the extra spaces do match, we dont consider the extra string length when scoring, what this does is
		//subtract 1 from added pat len, the full pattern length with the padded spaces is l2,
		//so if we had 'hello' as a query and ' hello ' as search text, we would pad with spaces when  we reach 2nd index while sliding in the outer function,
		//then in this function we see both outer spaces match, so added pat len goes from 2 to 0, so then when we score we just have 7/7-0
		//
		//for something like 'hellzo' we would have 4 that match, then t is 0.1 for the out of place o, added pat len is 1, and l2 is 6,
		//added pat len is not reduced because it doesnt match at that index, (the last char in s2 is ' ' and in s1 is 'o')
		//so we get 4+0.1/6-1, which is 0.82, hope that makes sense future me or whichever poor soul chooses to read this :)
		if (s2[l1 - 1] == s1[l1 - 1])
		{
			// actualMatches -= 0.84;
			addedPatLen -= 1;
		}
	}
	else if (extraSpaceLoc == 0)
	{
		if (s2[l1 - 1] == s1[l1 - 1])
		{
			// actualMatches -= 0.84;
			addedPatLen -= 1;
		}
		if (s2[0] == s1[0])
		{
			// actualMatches -= 0.84;
			addedPatLen -= 1;
		}
	}
	else if (extraSpaceLoc == 1)
	{
		if (s2[0] == s1[0])
		{
			// actualMatches -= 0.84;
			addedPatLen -= 1;
		}
	}

	if (cLog)
	{
		std::cout << "actMatches" << actualMatches << "\n";
		std::cout << "addedPatLen " << addedPatLen << "\n";
		std::cout << l2 - addedPatLen << "\n";
	}
	double score = ((actualMatches + t) / (l2 - addedPatLen));
	if (cLog)
	{
		std::cout << ":score:" << score << "\n";
		int w;
		w = getc(stdin);
	}
	return (score);
}

// Stage 2 entry point: score one caption line against the query (`pq`, padded once per
// search). If the line is longer than the query it slides a window across the line -
// only near `matchIndex` (where Stage 1's bitap found a hit), not the whole line - scoring
// each offset with jaro_actual_search_but_with_window_bs and keeping the best. The window
// is just a pointer offset into the line now (the old substr/`" "+s2+" "` per step was a
// pile of allocations); the maths inside the scorer is unchanged. If the line is shorter
// than the query it just falls back to a single jaro_actual_search. Returns [0,1].
double jaro_sliding_window(const char* string, const int strLen, const PaddedQuery &pq, const int patLen, const int max_distance, int matchIndex)
{
	const int l2 = patLen;
	double maxScore = 0;
	double score = 0;
	// if the string is longer than the query(pattern) do a sliding window search
	// ok so right now if we search hello and have the strings zzello and hzello they will score the same since the query can
	// only match the length of hello, im thinking that we add spaces before and after as we slide it, but remove the leading space when e is 0
	// and the trailing space when we are at the last window position
	if (strLen > patLen)
	{
		int strIndexStart = std::max(0, matchIndex - 1);
		int strIndexEnd = std::min(strLen - patLen, matchIndex + patLen + 2);
		for (int e = strIndexStart; e <= strIndexEnd; e++)
		{
			// extraSpaceLoc is 0 for before and after 1 for prefix 2 for suffix
			// (window slices below never run off the line: strLen > patLen bounds them)
			if (e == 0)
			{
				score = jaro_actual_search_but_with_window_bs(string, pq.suf.c_str(), l2 + 1, l2 + 1, 1, 2, max_distance);
			}
			else if (e == strLen - patLen)
			{
				score = jaro_actual_search_but_with_window_bs(string + e - 1, pq.pre.c_str(), l2 + 1, l2 + 1, 1, 1, max_distance);
			}
			else
			{
				score = jaro_actual_search_but_with_window_bs(string + e - 1, pq.both.c_str(), l2 + 2, l2 + 2, 2, 0, max_distance);
			}

			// std::cout << score;
			if (score > maxScore)
			{
				maxScore = score;
			}
		}
	}
	// otherwise just straight up compare
	else
	{
		score = jaro_actual_search(string, pq.q.c_str(), strLen, patLen, max_distance);
		return score;
	}
	return maxScore;
}
//this is a hard match, not used in fuzzy, it uses bitap, idk how it all works i copied it in lol
static int SearchString(std::string stringIn, std::string pattern)
{
	std::string text = stringIn; // to_lowercase(stringIn);
	// text = tolower(text);
	// std::cout << text << pattern;
	int m = pattern.size();
	unsigned long R;
	unsigned long patternMask[CHAR_MAX + 1];
	int i;

	if (pattern[0] == '\0')
		return 0;
	if (m > 31)
		return -1; // Error: The pattern is too long!

	R = ~1;

	for (i = 0; i <= CHAR_MAX; ++i)
		patternMask[i] = ~0;

	for (i = 0; i < m; ++i)
		patternMask[pattern[i]] &= ~(1UL << i);

	for (i = 0; text[i] != '\0'; ++i)
	{
		R |= patternMask[text[i]];
		R <<= 1;

		if (0 == (R & (1UL << m)))
			return (i - m) + 1;
	}

	return -1;
}

//this is levenshtein distance usiong bitap, it is much faster than the jaro sliding alternative above
//so we use it to filter, since if there isnt a decent levenshtein distance match there wont be a match at all, but the scoring is too limited so im not using this for that just
//a step along the way
//
//the pattern-only setup (patternMask, the R rows, the m>31 / empty checks) lives in
//cppSearch now and is done ONCE per search - this used to copy both strings, heap-allocate
//R, and rebuild the whole mask table for every single line, which was most of stage 1's
//runtime. text is indexed as unsigned char so a non-ascii byte can't index off the table.
static short int SearchStringFuzzy(const char *text, const unsigned long *patternMask, unsigned long *R, int m, int k)
{
	int i, d;
	for (i = 0; i <= k; ++i)
		R[i] = ~1;

	for (i = 0; text[i] != '\0'; ++i)
	{
		unsigned long oldRd1 = R[0];
		unsigned long mask = patternMask[(unsigned char)text[i]];

		R[0] |= mask;
		R[0] <<= 1;

		for (d = 1; d <= k; ++d)
		{
			unsigned long tmp = R[d];

			R[d] = (oldRd1 & (R[d] | mask)) << 1;
			oldRd1 = tmp;
		}

		if (0 == (R[k] & (1UL << m)))
			return (short)((i - m) + 1);
	}
	return -1;
}

//the main search function
void cppSearch(std::string query)
{
	if (cLog)
		std::cout << query << "\n";

	const int len = g_totalLines;
	g_survivors.clear();

	int queryLen = query.length();
	// for leshacejkven search
	int maxEditDist = queryLen / 2;
	if (cLog)
	{
		std::cout << "maxEditDist: " << maxEditDist << "\n";
		std::cout << "now running fuzzy bitap" << "\n";
	}

	// Stage 1 - fuzzy bitap filter: flag every line within edit distance maxEditDist.
	// All the query-only prep (mask table, R rows) happens here, once, instead of per line.
	if (queryLen == 0)
	{
		// empty pattern matches everything at offset 0 (same early-out the old per-line code had)
		for (int i = 0; i < len; i++)
			g_survivors.push_back({i, 0, 0.0});
	}
	else if (queryLen <= 31) // bitap patterns are capped at 31 chars (known rough edge)
	{
		unsigned long patternMask[256]; // indexed by unsigned char
		for (int i = 0; i < 256; ++i)
			patternMask[i] = ~0;
		for (int i = 0; i < queryLen; ++i)
			patternMask[(unsigned char)query[i]] &= ~(1UL << i);

		std::vector<unsigned long> R(maxEditDist + 1);
		// a line shorter than this can't possibly contain a match, skip it without scanning
		const int minLen = queryLen - maxEditDist;

		for (int i = 0; i < len; i++)
		{
			if (lineLen(i) < minLen)
				continue;
			short int singleMatchIdx = SearchStringFuzzy(lineAt(i), patternMask, R.data(), queryLen, maxEditDist);
			if (singleMatchIdx != -1)
			{
				g_survivors.push_back({i, singleMatchIdx, 0.0});
			}
		}
	}
	// queryLen > 31: bitap can't handle it (old code returned -1 per line) -> no survivors

	// lets just do 2, this is distance which swapped chars can get points for
	const int match_distance = 2;
	// pad the query once for the sliding window (was re-padded on every slide step)
	PaddedQuery pq;
	pq.q = query;
	pq.pre = " " + query;
	pq.suf = query + " ";
	pq.both = " " + query + " ";

	// Stage 2 - jaro sliding-window scoring of the filtered lines
	for (Survivor &s : g_survivors)
	{
		int textLen = lineLen(s.line); // length of string we are checking/number of characters
		double score = jaro_sliding_window(lineAt(s.line), textLen, pq, queryLen, 2, s.matchIdx);
		// so the best non perfect match would be something like " hell o " since it has the chars and can do one swap to be there
		// with these numbers, that kind of match would overtake a perfect "hello" match if the hello occured at index 50
		double scoreWithIndex = score - s.matchIdx * .002;
		int resSize = textLen;
		int lengthDiff = abs(resSize - queryLen);
		double scoreWithIndexAndLength = scoreWithIndex - (lengthDiff * 0.0005);
		s.score = scoreWithIndexAndLength;
	}

	// Stage 3 - partial_sort just the survivors for the top 450 (desc score; ties keep
	// ascending line order, which is what the old counting sort produced too)
	int topN = std::min((int)g_survivors.size(), 450);
	std::partial_sort(g_survivors.begin(), g_survivors.begin() + topN, g_survivors.end(),
		[](const Survivor &a, const Survivor &b) {
			if (a.score != b.score)
				return a.score > b.score;
			return a.line < b.line;
		});

	if (cLog)
	{
		std::cout << "Sorted array is\n";
		printArray(topN);
	}
}

//classes to hold score info to make passing back to js easier, score is as you see the score index, and the text of the string, we dont actually pass a score back... awkward lol
//might eventually but eh
//the index is from our combined list obvs and is used js side to find the index of the image in the set
class Score {
  public:
    std::string to_json();
    std::string text;
    int index;
};

class Scores {
  public:
    std::string to_json();
    void add_Score(const std::string &text, int index);

  private:
    std::vector<Score> _Scores;
};

std::string Score::to_json() {
  return "\"" + text + "\"" + "," + std::to_string(index);
}

void Scores::add_Score(const std::string &text, int index)
{
  Score f;
  f.text = escape_json(text);
  f.index = index;

  _Scores.push_back(f);
}

// builds the whole payload in one std::string now - the old version strcpy'd into a
// new char[json.length()] (one byte short for the '\0', oops) and leaked the mismatch
// to delete. the caller just hands json.c_str() to EM_ASM, no copy needed.
std::string Scores::to_json() {

  std::string json;
  json.reserve(_Scores.size() * 48 + 16); // rough per-result guess, just avoids regrows
  json += "[";

  for(size_t i = 0; i < _Scores.size(); i++)
  {
    json += _Scores[i].to_json();

    if(i < _Scores.size() -1)
    {
      json += ",";
    }
  }

  json += "]END000";

  return json;
}

extern "C" void search(char * query) {
  cppSearch(query);
  Scores Scores;
  // only real bitap survivors come back now - when fewer than 450 lines match, the old
  // code padded the payload out to 450 with zero-score junk lines
  int topN = std::min((int)g_survivors.size(), 450);
  for (int i = 0; i < topN; i++)
	{
		Scores.add_Score(lineAt(g_survivors[i].line), g_survivors[i].line);
	}
  std::string json = Scores.to_json();

#ifdef __EMSCRIPTEN__
    EM_ASM({
    // console.log(UTF8ToString($0));
    egg(UTF8ToString($0));
    // e.data = UTF8ToString($0);
}, json.c_str());
#else
  (void)json; // native build: main() below prints results itself
#endif
}


int main(int argc, char** argv)
{
#ifndef __EMSCRIPTEN__
	// Native debug/test path: load .txt corpora through the same exports JS uses,
	// run one search, print "index<TAB>score<TAB>caption" for the top 450.
	//   g++ -O3 wams.cpp -o wams && ./wams "hello" data/sm.txt data/recess.txt
	if (argc < 3)
	{
		std::cerr << "usage: " << argv[0] << " \"<query>\" <show.txt> [more .txt ...]\n";
		return 1;
	}
	long totalBytes = 0;
	std::vector<std::string> bufs;
	for (int a = 2; a < argc; a++)
	{
		std::ifstream f(argv[a], std::ios::binary);
		if (!f) { std::cerr << "can't open " << argv[a] << "\n"; return 1; }
		std::string b((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
		totalBytes += (long)b.size();
		bufs.push_back(std::move(b));
	}
	reserveCorpus((int)totalBytes, 400000);
	for (std::string &b : bufs)
	{
		char* ptr = showWritePtr((int)b.size());
		memcpy(ptr, b.data(), b.size());
		commitShow((int)b.size());
	}
	std::cerr << "loaded " << g_totalLines << " lines\n";
	start = high_resolution_clock::now();
	cppSearch(argv[1]);
	auto end = high_resolution_clock::now();
	duration<double, std::milli> diff = end - start;
	std::cerr << diff.count() << " ms\n";
	int topN = std::min((int)g_survivors.size(), 450);
	for (int i = 0; i < topN; i++)
	{
		printf("%d\t%.17g\t%s\n", g_survivors[i].line, g_survivors[i].score, lineAt(g_survivors[i].line));
	}
#endif
	return 0;
}


// Build via build.ps1 (see CLAUDE.md). Raw command (-O3 release, -O1 for testing):
// emcc -O3 .\wams.cpp -o .\wams.js -s WASM=1
//   -s EXPORTED_FUNCTIONS="['_search','_reserveCorpus','_showWritePtr','_commitShow','_clearCorpus','_malloc','_free']"
//   -s EXPORTED_RUNTIME_METHODS="['cwrap','UTF8ToString','HEAPU8']"
//   -s ALLOW_MEMORY_GROWTH=1
// Note: data.cpp is no longer compiled in - corpus is loaded at runtime from per-show .txt files.
