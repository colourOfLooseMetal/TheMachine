#include <string>
#include <vector>
#include <map>
#include <bitset>
const int bsLen = 4;
const int searchTextLen = 365697;
// const int searchTextLen = 31;
// std::vector<std::string> mapTextData =  {"xxxxhelloxx","xxxhelloxx","xxhelloxx","xhelloxx","xxxxhelloxx","xxxxhellox","xxxhellox","xxhellox","xhellox","xxxxhellox","xxxhello","xxhello","xhello","hello", "hzello","ayy hello there", "yeah hell of a", "helloasdaw", "hell. what a place", "hzello", "zhello", "helleo", "helol", "lehlo", "hello", "zhello", "helloz", "hellzowww", "hzellowww", "zzellowww", " hello "};

extern const char* const mapTextData[searchTextLen];
// extern const short int eachTextLen[searchTextLen];
extern std::map<std::string, std::bitset<searchTextLen>> sample_map;

