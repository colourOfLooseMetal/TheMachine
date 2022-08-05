
#include <iostream>

#include <string>

#include <vector>

#include <fstream>

// const int searchTextLen = 31;
const int searchTextLen = 365697;

std::vector<std::string> mapTextData(searchTextLen);

void stuff()
{
	std::cout << "in a function" << std::endl;
	for (int i = 0; i < searchTextLen; i++)
	{
		if(i%1000 == 0){
			std::cout << mapTextData[i] << std::endl;
		}
	}
}

int main()
{
	std::cout << "start of main" << std::endl;

	std::string line;
	std::ifstream myfile;


	myfile.open("machineTextTextCombined.json");//helloTest.txt   machineTextTextCombined.json
	int fileLineIter = 0;
	while (getline(myfile, line)){
		
		mapTextData[fileLineIter] = line;
		fileLineIter++;
	}
	
	myfile.close();
	std::cout << mapTextData[0] << "  -in main" << "\n";

	stuff();
	return 0;
}
