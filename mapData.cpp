#include "data.h"
#include <iostream>
#include <string>


	std::bitset<searchTextLen> bset1(std::string("1000"));
	std::bitset<searchTextLen> bset2(std::string("0001"));

    std::map<std::string, std::bitset<searchTextLen>> sample_map { 
    { "ee", bset1}, 
    { "aa", bset2} 
    };