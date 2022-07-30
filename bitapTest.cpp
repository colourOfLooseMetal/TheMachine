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
using namespace std::chrono;


double jaro(const std::string string, const std::string pattern) {

	const int strLen = string.length(), patLen = pattern.length();
	// cout << string << strLen << " " << patLen << endl;
	// int w;
	// w = getc(stdin);
	const int l1 = patLen, l2 = patLen;
	const std::string s2 = pattern;
	double maxScore = 0;
	if(strLen >= patLen){
	for(int e = 0; e < strLen-patLen; e++){
		// cout << e << "eeeeeeeee";
		std::string s1 = string.substr (e,e+l1);
		// cout << s1 << endl;
		if (l1 == 0)
			return l2 == 0 ? 1.0 : 0.0;
		// const int match_distance = std::max(l1, l2) / 2 - 1;
		const int match_distance = l2 / 2 - 1;
		bool s1_matches[l1];
		bool s2_matches[l2];
		std::fill(s1_matches, s1_matches + l1, false);
		std::fill(s2_matches, s2_matches + l2, false);
		int matches = 0;
		for (int i = 0; i < l1; i++)
		{
			const int end = std::min(i + match_distance + 1, l2);
			for (int k = std::max(0, i - match_distance); k < end; k++)
				if (!s2_matches[k] && s1[i] == s2[k])
				{
					s1_matches[i] = true;
					s2_matches[k] = true;
					matches++;
					break;
				}
		}
		if (matches == 0)
			return 0.0;
		double t = 0.0;
		int k = 0;
		for (int i = 0; i < l1; i++)
			if (s1_matches[i])
			{
				while (!s2_matches[k]) k++;
				if (s1[i] != s2[k]) t += 0.5;
				k++;
			}
	
		const double m = matches;
		double score = (m / l1 + m / l2 + (m - t) / m) / 3.0;
		// cout << score;
		if(score > maxScore){
			maxScore = score;
		}
	}
	}
	// cout << endl;
	return maxScore;
}
 
// int main() {
//     using namespace std;
//     cout << jaro("MARTHA", "MARHTA") << endl;
//     cout << jaro("DIXON", "DICKSONX") << endl;
//     cout << jaro("JELLYFISH", "SMELLYFISH") << endl;
//     return 0;
// }



/* C++ Program for Bad Character Heuristic of Boyer
Moore String Matching Algorithm */
#include <bits/stdc++.h>
using namespace std;
# define NO_OF_CHARS 256
 
// The preprocessing function for Boyer Moore's
// bad character heuristic
void badCharHeuristic( string str, int size,
                        int badchar[NO_OF_CHARS])
{
    int i;
 
    // Initialize all occurrences as -1
    for (i = 0; i < NO_OF_CHARS; i++)
        badchar[i] = -1;
 
    // Fill the actual value of last occurrence
    // of a character
    for (i = 0; i < size; i++)
        badchar[(int) str[i]] = i;
}
 
/* A pattern searching function that uses Bad
Character Heuristic of Boyer Moore Algorithm */
static int boyer_moore( string txt, string pat)
{
    int m = pat.size();
    int n = txt.size();
 
    int badchar[NO_OF_CHARS];
 
    /* Fill the bad character array by calling
    the preprocessing function badCharHeuristic()
    for given pattern */
    badCharHeuristic(pat, m, badchar);
 
    int s = 0; // s is shift of the pattern with
                // respect to text
    while(s <= (n - m))
    {
        int j = m - 1;
 
        /* Keep reducing index j of pattern while
        characters of pattern and text are
        matching at this shift s */
        while(j >= 0 && pat[j] == txt[s + j])
            j--;
 
        /* If the pattern is present at current
        shift, then index j will become -1 after
        the above loop */
        if (j < 0)
        {
            // cout << "pattern occurs at shift = " <<  s << endl;
 
            /* Shift the pattern so that the next
            character in text aligns with the last
            occurrence of it in pattern.
            The condition s+m < n is necessary for
            the case when pattern occurs at the end
            of text */
            s += (s + m < n)? m-badchar[txt[s + m]] : 1;
			return(s);
 
        }
 
        else
            /* Shift the pattern so that the bad character
            in text aligns with the last occurrence of
            it in pattern. The max function is used to
            make sure that we get a positive shift.
            We may get a negative shift if the last
            occurrence of bad character in pattern
            is on the right side of the current
            character. */
            s += max(1, j - badchar[txt[s + j]]);
    }
	return(-1);
}
 
/* Driver code */
// int main()
// {
//     string txt= "ABAAABCD";
//     string pat = "ABC";
//     search(txt, pat);
//     return 0;
// }
  
 // This code is contributed by rathbhupendra

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


	cout << vtr[0] << endl;
	// cout<< sizeof(vtr) << " ";
	// cout<< sizeof(vtr[0]) << " ";
	// int loc = SearchString("The quick brown fox jumps over the lazy dog hello", "fox");
	// cout << "the index is  " << loc;
	

	cout << vtr.size() << endl;
	
	int len = vtr.size();
	cout << len << endl;
	for(int i = 0; i < len; i++){
		// if(i%100 == 0){
		// 	cout << i << endl;
		// }
		// if(SearchString(vtr[i], "sushi") != -1){
		if(SearchStringFuzzy(vtr[i], "hello", 2) != -1){
		// double score = jaro(vtr[i], "hello");
		// if(score > 0.6){
		// // if(boyer_moore(vtr[i], "happy") != -1){
			// cout << vtr[i] << " " << " " << endl << endl;

		// }
		if(i == 36433){
			cout << "+++++++++" << endl;
			cout << vtr[i] << endl << endl;
		}
		// cout << "egg" << vtr[i] << i << endl;
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




 