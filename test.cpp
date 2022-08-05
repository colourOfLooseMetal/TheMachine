#include <stdio.h>
#include <iostream>
// using namespace std;
#include <limits.h>
#include <string>
// #include <cmath>
#include <algorithm>
#include <vector>
#include <numeric>
#include <map>
// #include <random>
#include <chrono>
#include <cctype>
#include <bitset>
#include <cstring>
#include <emscripten.h>
using namespace std::chrono;

int main() {
    std::cout << "Hello World\n";
    // return 0;
}
class Friend {
  public:
    std::string to_json();
    std::string first_name;
    std::string last_name;
  private:
    std::string format(std::string name, std::string value);
};

class Friends {
  public:
    char* to_json();
    void add_friend(std::string first_name, std::string last_name);
    
  private:
    std::vector<Friend> _friends;
};


std::string Friend::to_json() {
  return "{" + format("firstName", first_name) + "," + format("lastName", last_name) + "}";
}

std::string Friend::format(std::string name, std::string val) {
  return "\"" + name + "\":" + "\"" + val + "\"";
}

void Friends::add_friend(std::string first_name, std::string last_name)
{
  Friend f;
  f.first_name = first_name;
  f.last_name = last_name;

  _friends.push_back(f);
}

char* Friends::to_json() {
  
  std::string json = "[";
  
  for(int i = 0; i < _friends.size(); i++)
  {
    json += _friends[i].to_json();

    if(i < _friends.size() -1)
    {
      json += ",";
    }
  }
  
  json += "]";

  char* char_array = new char[json.length()]();
  strcpy(char_array, json.c_str());

  return char_array;
}

extern "C" void show_friends() {
  Friends friends;
  friends.add_friend("Mr", "Egg");
  friends.add_friend("Eggy", "McEgg");

  char* json = friends.to_json();

    EM_ASM({
    console.log(UTF8ToString($0));
    egg(UTF8ToString($0));
    // e.data = UTF8ToString($0);
}, json);

  delete json;
}

// emcc ./test.cpp -o ./generatedWasm/test.js -s WASM=1 -s EXPORTED_FUNCTIONS="['_show_friends', '_malloc', '_free']" -s EXTRA_EXPORTED_RUNTIME_METHODS="["cwrap", "UTF8ToString"]"
