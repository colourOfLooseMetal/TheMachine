/*****Please include following header files*****/
// string
// limits.h
/***********************************************/

/*****Please use following namespaces*****/
// std
/*****************************************/
#include <iostream>
// using namespace std;
#include <limits.h>
// #include "data.h"
#include <string>
// #include <cmath>
#include <algorithm>
#include <vector>
#include <numeric>
#include <map>
#include <fstream>
// #include <random>
#include <chrono>
#include <cctype>
#include <bitset>
// #include <emscripten.h>
#include <cstring>
using namespace std::chrono;
const bool cLog = false; // console.log
// const int searchTextLen = 33;

// std::string mapTextData[searchTextLen]
const int searchTextLen = 365697;
double scores[searchTextLen];
// const char**  com = new const char*
// char *mapTextData[searchTextLen] = 
// std::string mapTextData[mapTextData];
std::vector<std::string> mapTextData(searchTextLen);
// vector<double> myVect(120000000, 0);
// std::string * mapTextData = new std::string[searchTextLen] {"xxxxhelloxx", "xxxhelloxx", "xxhelloxx", "xhelloxx", "xxxxhelloxx", "xxxxhellox", "xxxhellox", "xxhellox", "xhellox", "xxxxhellox", "xxxhello", "xxhello", "xhello", "hello", "hzello", "ayy hello there", "yeah hell of a", "helloasdaw", "hell. what a place", "hzello", "zhello", "helleo", "helol", "lehlo", "hello", "zhello", "helloz", "hellzowww", "hzellowww", "zzellowww", " hello "};
// static const char * const mapTextData[searchTextLen] = 
//char * mapTextData = new char[searchTextLen]

// void hashSortIndices(double values[], int n, int sortedIndices[])
void hashSortIndices(double values[], int n, std::vector<int> &sortedIndices)
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

	std::cout << "bopoooo number of unique scores  " << numsAndCounts.size() << "\n";
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
	// std::cout << "zoooop" << "\n";
	// for (auto j = uniqueValToFirstSortedIndex.rbegin(); j != uniqueValToFirstSortedIndex.rend(); ++j)
	// {
	// 	std::cout << j->first << " " << j->first << " " << j->second<< "\n";
	// }
	// std::cout << "zeeeep" << "\n";
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
	// std::cout << "pls" << "\n";
	// for(int i = 0; i < n; i++){
	// 	std::cout << sortedIndices[i] << "\n";
	// }
	// std::cout << "bopeeee" << "\n";
	// std::map<int, int>::iterator it;
	int index = 0;
	// for (it = myMap.begin(); it != myMap.end(); ++it)
	// {
	// 	std::cout << it->first << ' ' << it->second;
	// }

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

// Utility function to print an array
void printArray(double arr[], int n, std::vector<int> sortedIndices)
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
			std::cout << mapTextData[sortedIndices[i]] << " " << arr[i] << "\n"; // " idx " << i << " " << mapTextData[i] << "\n";
			std::cout << "\n";
		}
	}
	std::cout << "\n over Thresh count: " << overThreshCount; // 1555 450-380 ms print if i < 100 "hello"

	std::cout << "\n";
}

// normal one
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

/// s2 is pattern
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
		std::cout << "extraspaceLoc " << extraSpaceLoc << "\n";
	}
	// extraSpaceLoc is 0 for before and after 1 for prefix 2 for suffix
	if (extraSpaceLoc == 2)
	{
		// std::cout << addedPatLen << l1-1 << s2[3] ;
		// std::cout << "hi jesse" << ":" << s2[l1-1] << ":" << s1[l1-1] << ":" << "\n";
		// std::cout << s1 << ":" << s2 << "\n";
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

double jaro_sliding_window(const std::string string, const std::string pattern, const int max_distance, int matchIndex)
{

	const int strLen = string.length(), patLen = pattern.length();
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

// casual mil nbd, we only need like 200k right now tho, but soon...
std::bitset<1000000> bitSetOfMatches;

void cppSearch()
{
		std::cout << "in a function" << std::endl;
	for (int i = 0; i < searchTextLen; i++)
	{
		if(i%1000 == 0){
			std::cout << mapTextData[i] << std::endl;
		}
	}
	std::cout << "eggstuff1"
			  << "\n";
	std::string query = "hello";
	// vector<std::string> mapTextData = {"ayy hello there", "yeah hell of a", "helloasdaw", "hell. what a place", "hzello", "zhello", "helleo", "helol", "lehlo", "hello", "zhello", "helloz", "hellzowww", "hzellowww", "zzellowww", " hello "};
	std::cout << "eggstuffqedqwdwqd"
			  << "\n";
	std::cout << mapTextData[0] << "\n";
	// cout<< sizeof(mapTextData) << " ";
	// cout<< sizeof(mapTextData[0]) << " ";
	// int loc = SearchString("The quick brown fox jumps over the lazy dog hello", "fox");
	// std::cout << "the index is  " << loc;

	// geeksforgeeks.org/c-bitset-and-its-application/

	std::cout << searchTextLen << "\n";

	const int len = searchTextLen;

	std::cout << len << "\n";
	// this is the index the pattern is found in the string
	std::vector<short int> matchIndex;
	matchIndex.resize(1000000);
	std::fill(matchIndex.begin(), matchIndex.end(), 0);
	// std::vector<double> scores;
	// scores.resize(1000000);
	// std::fill(scores.begin(), scores.end(), 0.0);

	
	for (int i = 0; i < len; i++)
	{
		scores[i] = 0.0;
	}
	std::cout << sizeof(matchIndex[0])*matchIndex.size() << "\n";
	std::cout << "shawtyInt " << matchIndex[0] << matchIndex[1000000-1] << "\n";

	int queryLen = query.length();
	// for leshacejkven search
	int maxEditDist = queryLen / 2;
	std::cout << "maxEditDist: " << maxEditDist << "\n";
	std::cout << "now running fuzzy bitap"
			  << "\n";
	int lesMatch = 0;
	for (int i = 0; i < len; i++)
	{
		short int singleMatchIdx = SearchStringFuzzy(mapTextData[i], query, maxEditDist);
		// std::cout << singleMatchIdx << "\n";
		if (singleMatchIdx != -1)
		{
			// std::cout << "\n" << "\n" << SearchStringFuzzy(mapTextData[i], query, maxEditDist) << "\n" << i << "\n";
			bitSetOfMatches[i] = 1;
			// lesMatch += 1;
			matchIndex[i] = singleMatchIdx;
		}
	}
	std::cout << "lesmatch, 0 cause disabled but that was to run the bitap fuzzy search: " << lesMatch << "\n";
	// int msl = queryLen;
	// msl = std::max(msl, 6);
	// const int match_distance = std::min(msl, 8) / 2 - 1; // min 2 max 3 //this can be calced once not each time
	// lets just do 2, this is distance which swapped chars can get points for
	const int match_distance = 2;
	for (int i = 0; i < len; i++)
	{
		if (bitSetOfMatches[i] == 1)
		{
			// std::cout << mapTextData[i] << "\n";
			double score = jaro_sliding_window(mapTextData[i], query, 2, matchIndex[i]); // 323ms"hello"
			// score cutoff thresh, otherwise will just be 0
			//  if (score > 0.5) the initial filtering kinda does this already in it's own way
			{
				// so the best non perfect match would be something like " hell o " since it has the chars and can do one swap to be there
				// with these numbers, that kind of match would overtake a perfect "hello" match if the hello occured at index 50
				// dosent really speed up but is cool//this int is like index/2 then index & 2, so instead of 0 1 2 3 4 5 6 we get
				//                                                       0 1 1 2 2 3 3
				// int mIndxModified = (matchIndex[i] >> 1) + (matchIndex[i] & 1);
				// std::cout << "\n mindxModified" << mIndxModified << "\n";
				double scoreWithIndex = score - matchIndex[i] * .002;
				int resSize = mapTextData[i].length();//strlen(mapTextData[i]);//strlen for char array mapTextData[i].length(); for string
				int lengthDiff = abs(resSize - queryLen);
				// int lenDiffModified = (lengthDiff >> 1) + (lengthDiff & 1);
				double scoreWithIndexAndLength = scoreWithIndex - (lengthDiff * 0.0005);
				// std::cout << "idx:" << i << " result:\"" << mapTextData[i] << "\" score:" << scoreWithIndexAndLength << "\n";
				// std::cout << "matchIndx:" << matchIndex[i] << " resultlength:" << strlen(mapTextData[i]) << " stringDiffLength:" << lengthDiff << "\n";
				// std::cout << "initial fuzzy Score:         " << score << "\n";
				// std::cout << "score w match index:         " << scoreWithIndex << "\n";
				// std::cout << "score w index & length diff: " << scoreWithIndexAndLength<< "\n" << "\n";
				scores[i] = scoreWithIndexAndLength;
			}
		}
	}
	std::cout << " \n";
	std::vector<int> sortedIndices(len);
	std::cout << "sorting"
			  << "\n";
	// std::cout << scores[60038] << " ," << scores[60039] << "\n" << "\n";
	std::cout << sizeof(scores) / sizeof(scores[0]) << "\n";
	std::cout << len << "\n";

	// // for (auto i: sort_indexes(scores)) {
	// // }
	hashSortIndices(scores, len, sortedIndices);

	std::cout << "Sorted array is\n";
	printArray(scores, len, sortedIndices);
}

// class Friend {
//   public:
//     std::string to_json();
//     std::string first_name;
//     std::string last_name;
//   private:
//     std::string format(std::string name, std::string value);
// };

// class Friends {
//   public:
//     char* to_json();
//     void add_friend(std::string first_name, std::string last_name);

//   private:
//     std::vector<Friend> _friends;
// };

// std::string Friend::to_json() {
//   return "{" + format("firstName", first_name) + "," + format("lastName", last_name) + "}";
// }

// std::string Friend::format(std::string name, std::string val) {
//   return "\"" + name + "\":" + "\"" + val + "\"";
// }

// void Friends::add_friend(std::string first_name, std::string last_name)
// {
//   Friend f;
//   f.first_name = first_name;
//   f.last_name = last_name;

//   _friends.push_back(f);
// }

// char* Friends::to_json() {

//   std::string json = "[";

//   for(int i = 0; i < _friends.size(); i++)
//   {
//     json += _friends[i].to_json();

//     if(i < _friends.size() -1)
//     {
//       json += ",";
//     }
//   }

//   json += "]";

//   char* char_array = new char[json.length()]();
//   strcpy(char_array, json.c_str());

//   return char_array;
// }

// extern "C" void search(char * query) {
//   Friends friends;
//   friends.add_friend(query, "Egg");
//   friends.add_friend("Eggy", "McEgg");
// 	cppSearch(query);
//   char* json = friends.to_json();

//     EM_ASM({
//     console.log(UTF8ToString($0));
//     egg(UTF8ToString($0));
//     // e.data = UTF8ToString($0);
// }, json);

//   delete json;
// }
void things(){
	cppSearch();
}

int main()
{

	std::ifstream myfile;
	std::string line;


	myfile.open("machineTextTextCombined.json");//helloTest.txt   machineTextTextCombined.json
	int fileLineIter = 0;
	while (getline(myfile, line)){
		// std::cout << line  << typeid(line.c_str()).name() << line.c_str() << typeid(line).name() << std::endl;
		// mapTextData[fileLineIter] = new char [line.size()+1];
		// strcpy(mapTextData[fileLineIter], line.c_str()); 
		// std::cout << "line is:" << line;
		mapTextData[fileLineIter] = line;
		// std::cout << "   in arr is;" << mapTextData[fileLineIter] << std::endl;;
		fileLineIter++;
	}
	myfile.close();
	int egg = 0;
	std::cout << mapTextData[0] << "\n";
	std::cout << "eggStart"
			  << "\n";
	auto start = high_resolution_clock::now();
	// cppSearch();
	things();
	// search();

	auto end = high_resolution_clock::now();
	duration<double, std::milli> diff = end - start; //
	std::cout << diff.count() << " ms"
			  << "\n";
	// std::cout << "egg" << "\n";

	// std::cout << diff.count() << " ms" << "\n";
	// // Driver program to test above function.
	// int arr[] = {100, 12, 100, 1, 1, 12, 100, 1, 12, 100, 1, 1};
	// int n = sizeof(arr) / sizeof(arr[0]);
	// int sortedIndices[n];
	// // std::cout << "Input array is\n";
	// // printArray(arr, n);

	// hashSortIndices(arr, n, sortedIndices);

	// std::cout << "Sorted array is\n";
	// printArray(arr, n, sortedIndices);

	return 0;
}
