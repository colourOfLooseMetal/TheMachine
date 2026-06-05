// data.h — previously declared the static mapTextData corpus and searchTextLen.
// The corpus is now loaded at runtime via reserveCorpus/showWritePtr/commitShow
// (see wams.cpp). data.cpp is no longer compiled; this header is kept only as a
// reference and for any legacy standalone .cpp files (bitapTest.cpp etc.).
#include <string>
#include <vector>
#include <map>
#include <bitset>

// Legacy: static corpus (not used by the wasm/live build)
// const int searchTextLen = 365697;
// extern const char* const mapTextData[searchTextLen];
// extern const short int eachTextLen[searchTextLen];
// extern std::map<std::string, std::bitset<searchTextLen>> sample_map;
