/*****Please include following header files*****/
// string
// limits.h
/***********************************************/

/*****Please use following namespaces*****/
// std
/*****************************************/
#include <iostream>
using namespace std;
#include <limits.h>
#include <string>
// #include <cmath>
#include <algorithm>
#include <vector>
// #include <random>
#include <iostream>
#include <chrono>
#include <cctype>
#include <bitset>
using namespace std::chrono;

//normal one
double jaro_actual_search(const std::string s1, const std::string s2,int l1, int l2, const int match_distance) {
 	if (l1 == 0){
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
			if(s2[i] != s1[i]){
				t += 0.5;
			}
			else{
				actualMatches += 1;
			}
		}
	
	// const double m = matches;
	// cout << " actM:" << actualMatches << " t:" << t << endl;

	double score = ((actualMatches + t) / l2);
	// cout << ":scoreNonWindow:" << score;
	return(score);
}

///s2 is pattern
double jaro_actual_search_but_with_window_bs(const std::string s1, const std::string s2,int l1, int l2,int addedPatLen, int extraSpaceLoc,const int match_distance) {

	cout << ":" << s2 << ":" << ":" << s1 << ":" << l1 << l2 << endl;


 	if (l1 == 0){
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
	int k = 0;
	for (int i = 0; i < l1; i++)
		if (s1_matches[i])
		{
			if(s2[i] != s1[i]){
				t += 0.3;
			}
			else{
				actualMatches += 1;
			}
		}
	
	// const double m = matches;
	cout << " actM:" << actualMatches << " t:" << t << endl;
    
	if(extraSpaceLoc == 0){
		if(s2[l1-1] == s1[l1-1]){
			actualMatches -= 0.85;
		}
		if(s2[0] == s1[0]){
			actualMatches -= 0.85;
		}
	}
	else if(extraSpaceLoc == 1){
		if(s2[0] == s1[0]){
			actualMatches -= 0.85;
		}
	}
	else if(extraSpaceLoc == 2){
		// cout << addedPatLen;
		// cout << "hi jesse" << ":" << s1[l1-1] << ":" << s2[l1-1] << ":" << endl;
		// cout << s1 << ":" << s2 << endl;
		if(s2[l1-1] == s1[l1-1]){
			actualMatches -= 0.8;
		}
	}
	cout << "actMatches" << actualMatches << endl;
	cout << "addedPatLen " << addedPatLen << endl;
	cout << l2-addedPatLen <<endl;
	double score = ((actualMatches + t) / (l2-addedPatLen));
	cout << ":score:" << score << endl;
	int w;
	w = getc(stdin);
	return(score);
}


double jaro_sliding_window(const std::string string, const std::string pattern, const int max_distance) {

	const int strLen = string.length(), patLen = pattern.length();
	cout << endl << endl << ":" << pattern << ":" <<  "  main " << ":" << string << ":" << endl;
	// int w;
	// w = getc(stdin);
	const int l1 = patLen, l2 = patLen;
	const std::string s2 = pattern;
	double maxScore = 0;
	double score = 0;
	int maxScoreIndex = 0;
	//if the string is longer than the query(pattern) do a sliding window search
	//ok so right now if we search hello and have the strings zzello and hzello they will score the same since the query can
	//only match the length of hello, im thinking that we add spaces before and after as we slide it, but remove the leading space when e is 0
	//and the trailing space when we are at the last window position
	
	if(strLen > patLen){
		for(int e = 0; e <= strLen-patLen; e++){
			//extraSpaceLoc is 0 for before and after 1 for prefix 2 for suffix
			if(e == 0){
				std::string s1 = string.substr (e,e+l1+1);
				score = jaro_actual_search_but_with_window_bs(s1,s2 + " ",l1 + 1,l2+1,1,2,max_distance);
			}
			else if(e == strLen-patLen){
				std::string s1 = string.substr (e-1,e+l1);
				score = jaro_actual_search_but_with_window_bs(s1," "+s2,l1 + 1,l2+1,1,1,max_distance);
			}
			else{
				std::string s1 = string.substr (e-1,e+l1+1);
				score = jaro_actual_search_but_with_window_bs(s1," "+s2+" ",l1 + 2,l2+2,2,0,max_distance);
			}
			
			// cout << score;
			if(score > maxScore){
				maxScore = score;
				maxScoreIndex = e;
			}
		}
	}
	//otherwise just straight up compare
	else{
		score = jaro_actual_search(string,pattern,strLen,patLen,max_distance);
		return score;
	}
	// cout << endl;
	// if(maxScore > 0.6){
	// cout << " msindex: " << maxScoreIndex << " "; 
	// }
	return maxScore;
}
 


static int SearchString(string stringIn, string pattern)
{	
	string text = stringIn;//to_lowercase(stringIn);
	// text = tolower(text);
	// cout << text << pattern;
	int m = pattern.size();
	unsigned long R;
	unsigned long patternMask[CHAR_MAX + 1];
	int i;

	if (pattern[0] == '\0') return 0;
	if (m > 31) return -1; //Error: The pattern is too long!

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

static int SearchStringFuzzy(string text, string pattern, int k)
{
	int result = -1;
	int m = pattern.size();
	unsigned long *R;
	unsigned long patternMask[CHAR_MAX + 1];
	int i, d;

	if (pattern[0] == '\0') return 0;
	if (m > 31) return -1; //Error: The pattern is too long!

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

	free(R);
	return result;
}

int stuff(){
	
	vector vtr = {"yeah hell of a", "helloasdaw","hell. what a place", "hzello","zhello", "helleo", "helol", "lehlo","hello", "zhello", "helloz", "hellzowww", "hzellowww", "zzellowww", " hello "};


	cout << vtr[0] << endl;
	// cout<< sizeof(vtr) << " ";
	// cout<< sizeof(vtr[0]) << " ";
	// int loc = SearchString("The quick brown fox jumps over the lazy dog hello", "fox");
	// cout << "the index is  " << loc;

	// geeksforgeeks.org/c-bitset-and-its-application/

	

	cout << vtr.size() << endl;
	
	const int len = vtr.size();
	// int len = static_cast<int>(vtr.size());
	cout << len << endl;
	bitset<1000000> bitSetOfMatches;
	// std::vector<std::bitset<len>> wrapper(1);
    // auto & cover = wrapper[0];
    // cover[0] = 1;
    // std::cout << cover[0] << " " << cover[len - 1];
	std::string query = "hello";
	
	int maxEditDist = query.length()/2;
	cout << maxEditDist << endl;
	for(int i = 0; i < len; i++){
		if(SearchStringFuzzy(vtr[i], query, maxEditDist) != -1){
			bitSetOfMatches[i] = 1;
			// cout << vtr[i] << endl;
		}
		bitSetOfMatches[i] = 1;
	}
	int msl = query.length();
	msl = std::max(msl, 6);
	const int match_distance = std::min(msl,8) / 2 - 1; //min 2 max 3 //this can be calced once not each time
	for(int i = 0; i < len; i++){
		if(bitSetOfMatches[i] == 1){
		double score = jaro_sliding_window(vtr[i], query, match_distance); //323ms"hello"
		if(score > 0.8){
			cout << vtr[i] << " " << score << endl << endl;
		}
	// if(SearchString(vtr[i], "hello")!= -1){//35ms"hello"
	// 	// cout << vtr[i] << endl << endl;
	// 	}
	}
	}

	return 0;

}

int main(){
	
	auto start = high_resolution_clock::now();

	stuff();

	auto end = high_resolution_clock::now();
	duration<double, std::milli> diff = end - start ; // still zero
	cout << diff.count() << " ms" << endl;
	cout << "egg" << endl;
 
	// To get the value of duration use the count()
	// member function on the duration object

	// std::cout << t.time_since_epoch() << ' ';

	// cout << "Time taken by function: " << duration.count() << " microseconds" << endl;
	
	return 0;
}




 