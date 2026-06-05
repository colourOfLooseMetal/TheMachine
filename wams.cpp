// ============================================================================
//  wams.cpp - "Web Assembly Machine Searcher", the search engine for The Machine.
//
//  Fuzzy-matches a query against caption lines loaded at runtime into g_corpus
//  (loaded from per-show .txt files by JS; see reserveCorpus/showWritePtr/commitShow)
//  and returns the best ~450 hits to the page.
//
//  Pipeline (all driven by cppSearch -> the extern "C" search() wasm export):
//    Stage 1  SearchStringFuzzy    fuzzy Bitap filter, edit distance <= queryLen/2
//    Stage 2  jaro_sliding_window  Jaro-style sliding-window scoring of survivors
//    Stage 3  hashSortIndices      O(n) counting sort of the scores
//    Return   Scores::to_json      pack top 450 as ["text",index,...]END000, then
//                                  hand to JS by calling egg(json) via EM_ASM
//
//  Two build targets (see the emcc command at the very bottom of this file):
//    - wasm:   the extern "C" search() export the web page calls through cwrap
//    - native: egg.exe, a g++ debug build that runs main() (comment out the
//              emscripten bits as noted near the Score/Scores classes)
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

#include <emscripten.h>
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

// ---- Work arrays (resized once when corpus size changes, before each search) -
std::vector<double>   scoresArr;
std::vector<int>      sortedIndices;
std::vector<uint8_t>  g_bitSet;     // replaces fixed bitSetOfMatches
std::vector<short>    g_matchIndex; // replaces local matchIndex in cppSearch

static int s_workArrayLen = 0;
static void ensureWorkArrays(int n) {
    if (s_workArrayLen == n) return;
    scoresArr.assign(n, 0.0);
    sortedIndices.assign(n, 999);
    g_bitSet.assign(n, 0);
    g_matchIndex.assign(n, 0);
    s_workArrayLen = n;
}

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
    g_totalLines = 0;
    s_workArrayLen = 0; // force work-array resize on next search
}

auto start = high_resolution_clock::now();



//escape special characters in json string so we dont reach unexpected end of file
std::string escape_json(const std::string &s) {
    std::ostringstream o;
    for (auto c = s.cbegin(); c != s.cend(); c++) {
        if (*c == '"' || *c == '\\' || ('\x00' <= *c && *c <= '\x1f')) {
            o << "\\u"
              << std::hex << std::setw(4) << std::setfill('0') << static_cast<int>(*c);
        } else {
            o << *c;
        }
    }
    return o.str();
}

// Stage 3: counting sort. Fills `sortedIndices` with the line indices 0..n-1 ordered by
// descending score (values[i] is the score for line i). O(n): count how many lines share
// each distinct score, work out where each score's block begins in the sorted output, then
// scatter each index into its slot. Also rewrites values[] into sorted order as a side
// effect. The numbered steps below are the classic counting-sort recipe.
void hashSortIndices(std::vector<double> &values, int n, std::vector<int> &sortedIndices)
{
	// 1. Create an empty hash table.
	std::map<double, int> numsAndCounts;

	// std::cout << "\n";
	// 2. Input array values are stores as key and their
	// counts are stored as value in hash table.

	// for the list 100, 12, 100, 1, 1, 12, 100, 1, 12, 100, 1, 1
	// this would make the map 100: 4  12: 3 1: 5
	for (int i = 0; i < n; i++)
	{
		numsAndCounts[values[i]]++;
		// if(values[i] > 1){
		// 	std::cout << i << " ," << values[i] << mapTextData[i] << "\n";
		// }
	}

	// std::cout << "bopoooo number of unique scores  " << numsAndCounts.size() << "\n";
	int numOfEachUniqueVal[numsAndCounts.size()];
	int uniqueValCounter[numsAndCounts.size()];
	// double uniqueVals[numsAndCounts.size()];
	int jIter = 0;
	// std::map<int, int>::iterator j;
	for (auto j = numsAndCounts.rbegin(); j != numsAndCounts.rend(); ++j)
	{
		numOfEachUniqueVal[jIter] = j->second;
		uniqueValCounter[jIter] = 0;
		// std::cout << j->first << " " << j->first << " " << j->second<< "\n";
		jIter += 1;
	}
	// ok hear me out here
	// if we know there are like 10 with a score of 1, then 8 with a score of 0.95 then 3 with a score of 0.9
	// we know the first 1 will be at index 0 obvs the first 0.95 will be at 11 and first 0.9 will be at index 21
	// so map the values to the index, and increment numofeachuniqueval down each time you add one

	std::map<double, int> uniqueValToFirstSortedIndex;
	int uniqueValCumulativeIndex = 0;
	for (auto j = numsAndCounts.rbegin(); j != numsAndCounts.rend(); ++j)
	{
		uniqueValToFirstSortedIndex[j->first] = uniqueValCumulativeIndex;
		uniqueValCumulativeIndex += j->second;
		// std::cout << j->first << " " << j->first << " " << j->second<< "\n";
	}
	for (int i = 0; i < n; i++)
	{
		// if(values[i] > 0){
		// std::cout << i << " " << uniqueValToFirstSortedIndex[values[i]] << "  " << values[i] << "\n";
		// }
		sortedIndices[uniqueValToFirstSortedIndex[values[i]]] = i;
		uniqueValToFirstSortedIndex[values[i]] += 1;
		if (values[i] > 0)
		{
		}
	}
	int index = 0;

	// 3. Consider all keys of hash table and sort them.
	// In std::map, keys are already sorted.

	// 4. Traverse all sorted keys and print every key its value times.
	for (auto it = numsAndCounts.rbegin(); it != numsAndCounts.rend(); ++it)
	{
		while (it->second--)
		{
			// if(it->first > .5){
			// // std::cout << it->first << " : " << it->second << "index" << index << "\n";
			// }
			values[index++] = it->first;
		}
	}
}

// Debug-only: dump the top 100 results (caption + score) in sorted order to stdout.
// Only reached when cLog is true (see the gated call at the end of cppSearch).
// overThreshCount is a leftover profiling tally of how many scores exceed 0.7.
void printArray(std::vector<double>& arr, int n, std::vector<int> sortedIndices)
{
	int overThreshCount = 0;
	for (int i = 0; i < n; i++)
	{
		if (arr[i] > 0.7)
		{
			overThreshCount++;
		}
		if (i < 100)
		{
			std::cout << lineAt(sortedIndices[i]) << " " << arr[i] << "\n"; // " idx " << i << " " << lineAt(i) << "\n";
			std::cout << "\n";
		}
	}
	// std::cout << "\n over Thresh count: " << overThreshCount; // 1555 450-380 ms print if i < 100 "hello"

	// std::cout << "\n";
}

// so this isnt the jaro algoritim, and this isnt the sliding window search, this gets called when the query is longer than the text we are searching, it wouldnt be a bad idea to slide the searched text over the query
//i guess the same way we slide the query over the searched text in the next function, ill explain the scoring in the next function, i dont actually know how all of this function works lol, i mean i kinda do, but the guts are jaro
//and then i change the scoring
double jaro_actual_search(const std::string s1, const std::string s2, int l1, int l2, const int match_distance)
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
	double tAct = 0.0;
	int k = 0;
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
// s1 = a slice of the caption line; s2 = the query padded with a leading/trailing space.
// addedPatLen = how many padding spaces were added; extraSpaceLoc says where they are
// (0 both / 1 prefix / 2 suffix) so matched padding can be discounted from the denominator.
// Returns a score in [0,1]; see the worked 'hello' / 'hellzo' example inside the body.
//so like i said earlier, guts are jaro (not jaro winkler)
double jaro_actual_search_but_with_window_bs(const std::string s1, const std::string s2, int l1, int l2, int addedPatLen, int extraSpaceLoc, const int match_distance)
{
	if (cLog)
	{
		std::cout << ":" << s2 << ":"
				  << ":" << s1 << ":" << l1 << "," << l2 << "\n";
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
		// std::cout << addedPatLen << l1-1 << s2[3] ;
		// std::cout << "hi jesse" << ":" << s2[l1-1] << ":" << s1[l1-1] << ":" << "\n";
		// std::cout << s1 << ":" << s2 << "\n";
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

// Stage 2 entry point: score one caption line against the query (`pattern`).
// If the line is longer than the query it slides a space-padded window across the line -
// only near `matchIndex` (where Stage 1's bitap found a hit), not the whole line - scoring
// each offset with jaro_actual_search_but_with_window_bs and keeping the best. If the line
// is shorter than the query it just falls back to a single jaro_actual_search. Returns [0,1].
double jaro_sliding_window(const std::string string, const int strLen, const std::string pattern, const int patLen, const int max_distance, int matchIndex)
{

	// const int strLen = string.length();
	// std::cout << "\n" << "\n" << ":" << pattern << ":" <<  "  main " << ":" << string << ":" << "\n";
	// int w;
	// w = getc(stdin);
	const int l2 = patLen;
	const std::string s2 = pattern;
	double maxScore = 0;
	double score = 0;
	int maxScoreIndex = 0;
	// if the string is longer than the query(pattern) do a sliding window search
	// ok so right now if we search hello and have the strings zzello and hzello they will score the same since the query can
	// only match the length of hello, im thinking that we add spaces before and after as we slide it, but remove the leading space when e is 0
	// and the trailing space when we are at the last window position
	std::string s1 = "";
	if (strLen > patLen)
	{
		int strIndexStart = std::max(0, matchIndex - 1);
		int strIndexEnd = std::min(strLen - patLen, matchIndex + patLen + 2);
		for (int e = strIndexStart; e <= strIndexEnd; e++)
		{
			// extraSpaceLoc is 0 for before and after 1 for prefix 2 for suffix
			if (e == 0)
			{
				s1 = string.substr(e, l2 + 1);
				// std::cout << "e0" << ":" << s1 << ":" << "\n";
				score = jaro_actual_search_but_with_window_bs(s1, s2 + " ", s1.length(), l2 + 1, 1, 2, max_distance);
			}
			else if (e == strLen - patLen)
			{
				s1 = string.substr(e - 1, l2 + 1);
				// std::cout << "esl-pl" << ":" << s1 << ":" << "\n";
				score = jaro_actual_search_but_with_window_bs(s1, " " + s2, s1.length(), l2 + 1, 1, 1, max_distance);
			}
			else
			{
				s1 = string.substr(e - 1, l2 + 2);
				// std::cout << "e-else-mid " << e << " l2patlen :" << l2 << ":" << s1 << ":" << string.substr(e - 1, e + l2 + 1) << ":" << "\n";
				score = jaro_actual_search_but_with_window_bs(s1, " " + s2 + " ", s1.length(), l2 + 2, 2, 0, max_distance);
			}

			// std::cout << score;
			if (score > maxScore)
			{
				maxScore = score;
				maxScoreIndex = e;
			}
		}
	}
	// otherwise just straight up compare
	else
	{
		score = jaro_actual_search(string, pattern, strLen, patLen, max_distance);
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
static short int SearchStringFuzzy(std::string text, std::string pattern, int k)
{
	int result = -1;
	int m = pattern.size();
	unsigned long *R;
	unsigned long patternMask[CHAR_MAX + 1];
	int i, d;

	if (pattern[0] == '\0')
		return 0;
	if (m > 31)
		return -1; // Error: The pattern is too long!

	R = new unsigned long[(k + 1) * sizeof *R];
	for (i = 0; i <= k; ++i)
		R[i] = ~1;

	for (i = 0; i <= CHAR_MAX; ++i)
		patternMask[i] = ~0;

	for (i = 0; i < m; ++i)
		patternMask[pattern[i]] &= ~(1UL << i);

	for (i = 0; text[i] != '\0'; ++i)
	{
		unsigned long oldRd1 = R[0];

		R[0] |= patternMask[text[i]];
		R[0] <<= 1;

		for (d = 1; d <= k; ++d)
		{
			unsigned long tmp = R[d];

			R[d] = (oldRd1 & (R[d] | patternMask[text[i]])) << 1;
			oldRd1 = tmp;
		}

		if (0 == (R[k] & (1UL << m)))
		{
			result = (i - m) + 1;
			break;
		}
	}
	// std::cout << text << ":" << pattern << ":" << result << "\n";
	free(R);
	return result;
}

//the main search function
void cppSearch(std::string query)
{
	if (cLog)
		std::cout << query << "\n";

	const int len = g_totalLines;

	// Resize work arrays if corpus changed since last search; reset per-search state.
	ensureWorkArrays(len);
	// g_bitSet and g_matchIndex must be cleared each search so previous results don't leak.
	std::fill(g_bitSet.begin(), g_bitSet.end(), 0);
	std::fill(g_matchIndex.begin(), g_matchIndex.end(), 0);

	int queryLen = query.length();
	// for leshacejkven search
	int maxEditDist = queryLen / 2;
	if (cLog)
	{
		std::cout << "maxEditDist: " << maxEditDist << "\n";
		std::cout << "now running fuzzy bitap" << "\n";
	}

	// Stage 1 - fuzzy bitap filter: flag every line within edit distance maxEditDist
	for (int i = 0; i < len; i++)
	{
		short int singleMatchIdx = SearchStringFuzzy(lineAt(i), query, maxEditDist);
		if (singleMatchIdx != -1)
		{
			g_bitSet[i] = 1;
			g_matchIndex[i] = singleMatchIdx;
		}
	}

	// lets just do 2, this is distance which swapped chars can get points for
	const int match_distance = 2;
	// Stage 2 - jaro sliding-window scoring of the filtered lines
	for (int i = 0; i < len; i++)
	{
		if (g_bitSet[i])
		{
			int textLen = strlen(lineAt(i)); // length of string we are checking/number of characters
			double score = jaro_sliding_window(lineAt(i), textLen, query, queryLen, 2, g_matchIndex[i]); // 323ms"hello"
			// score cutoff thresh, otherwise will just be 0
			//  if (score > 0.5) the initial filtering kinda does this already in it's own way
			{
				// so the best non perfect match would be something like " hell o " since it has the chars and can do one swap to be there
				// with these numbers, that kind of match would overtake a perfect "hello" match if the hello occured at index 50
				double scoreWithIndex = score - g_matchIndex[i] * .002;
				int resSize = textLen;
				int lengthDiff = abs(resSize - queryLen);
				double scoreWithIndexAndLength = scoreWithIndex - (lengthDiff * 0.0005);
				scoresArr[i] = scoreWithIndexAndLength;
			}
		}
	}

	// Stage 3 - counting sort of all scores into sortedIndices
	hashSortIndices(scoresArr, len, sortedIndices);

	if (cLog)
	{
		std::cout << "Sorted array is\n";
		printArray(scoresArr, len, sortedIndices);
	}
}

//classes to hold score info to make passing back to js easier, score is as you see the score index, and the text of the string, we dont actually pass a score back... awkward lol
//might eventually but eh
//the index is from our combined list obvs and is used js side to find the index of the image in the set

// comment out here to before main for normal compile
class Score {
  public:
    std::string to_json();
    std::string text;
    int index;
//   private:
//     std::string format(std::string name, std::string value);
};

class Scores {
  public:
    char* to_json();
    void add_Score(std::string text, int index);

  private:
    std::vector<Score> _Scores;
};

std::string Score::to_json() {
  return "\"" + text + "\"" + "," + std::to_string(index);
}

// std::string Score::format(std::string name, std::string val) {
//   return "\"" + name + "\":" + "\"" + val + "\"";
// }

void Scores::add_Score(std::string text, int index)
{
  Score f;
  f.text = escape_json(text);
  f.index = index;

  _Scores.push_back(f);
}

char* Scores::to_json() {

  std::string json = "[";

  for(int i = 0; i < _Scores.size(); i++)
  {
    json += _Scores[i].to_json();

    if(i < _Scores.size() -1)
    {
      json += ",";
    }
  }

  json += "]END000";

  char* char_array = new char[json.length()]();
  strcpy(char_array, json.c_str());

  return char_array;
}

extern "C" void search(char * query) {
  cppSearch(query);
  Scores Scores;
  int topN = std::min(450, g_totalLines);
  for (int i = 0; i < topN; i++)
	{
		Scores.add_Score(lineAt(sortedIndices[i]), sortedIndices[i]);
	}
  char* json = Scores.to_json();

    EM_ASM({
    // console.log(UTF8ToString($0));
    egg(UTF8ToString($0));
    // e.data = UTF8ToString($0);
}, json);
  delete json;
	// Reset work arrays for the next search.
	std::fill(scoresArr.begin(), scoresArr.end(), 0.0);
	std::fill(sortedIndices.begin(), sortedIndices.end(), 999);
}


int main()
{
	// Native egg.exe debug path: load a .txt corpus file, then search.
	// For wasm the loading is done from JS; here we drive it directly.
	// Uncomment the block below and supply a small <show>.txt next to egg.exe.
	//
	// std::ifstream f("sm_test.txt", std::ios::binary | std::ios::ate);
	// auto sz = (int)f.tellg(); f.seekg(0);
	// reserveCorpus(sz, 100000);
	// char* ptr = showWritePtr(sz);
	// f.read(ptr, sz);
	// int added = commitShow(sz);
	// std::cout << "loaded " << added << " lines, total=" << g_totalLines << "\n";
	// start = high_resolution_clock::now();
	// cppSearch("hello");
	// auto end = high_resolution_clock::now();
	// duration<double, std::milli> diff = end - start;
	// std::cout << diff.count() << " ms\n";
	return 0;
}


// Build via build.ps1 (see CLAUDE.md). Raw command (-O3 release, -O1 for testing):
// emcc -O3 .\wams.cpp -o .\wams.js -s WASM=1
//   -s EXPORTED_FUNCTIONS="['_search','_reserveCorpus','_showWritePtr','_commitShow','_clearCorpus','_malloc','_free']"
//   -s EXPORTED_RUNTIME_METHODS="['cwrap','UTF8ToString','HEAPU8']"
//   -s ALLOW_MEMORY_GROWTH=1
// Note: data.cpp is no longer compiled in - corpus is loaded at runtime from per-show .txt files.
