# featuring wams
  web assembly machine searcher, a fuzzy string search method created specifically for searching the machine\
  uses a combination of fuzzy bitap to filter and kinda uses a sliding window jaro/ngram method to score, and scores based on match index,\
  but like c++ is hard and im tired so instead of explaining the scoring method take a look at the scores for the search term "hello"\
\for searching the list ["hello", "helloz","helloasdaw","zhello"," hello ", "ayy hello there", "yeah hell of a", "helleo", "hellzowww", "hzello", "hzellowww"]
\
\the scoring has changed a little but these results would appear in the same order as they do here
\
\
result:"hello"\
matchIndx:0 resultlength:5 stringDiffLength:0\
initial fuzzy Score:         1\
score w match index:         1\
score w index & length diff: 1\
\
result:"helloz"\
matchIndx:0 resultlength:6 stringDiffLength:1\
initial fuzzy Score:         1\
score w match index:         1\
score w index & length diff: 0.9995\
\
result:"helloasdaw"\
matchIndx:0 resultlength:10 stringDiffLength:5\
initial fuzzy Score:         1\
score w match index:         1\
score w index & length diff: 0.9975\
\
result:"zhello"\
matchIndx:1 resultlength:6 stringDiffLength:1\
initial fuzzy Score:         1\
score w match index:         0.998\
score w index & length diff: 0.9975\
\
result:" hello "\
matchIndx:1 resultlength:7 stringDiffLength:2\
initial fuzzy Score:         1\
score w match index:         0.998\
score w index & length diff: 0.997\
\
result:"ayy hello there"\
matchIndx:4 resultlength:15 stringDiffLength:10\
initial fuzzy Score:         1\
score w match index:         0.992\
score w index & length diff: 0.987\
\
result:"yeah hell of a"\
matchIndx:5 resultlength:14 stringDiffLength:9\
initial fuzzy Score:         0.866667\
score w match index:         0.856667\
score w index & length diff: 0.852167\
\
result:"helleo"\
matchIndx:0 resultlength:6 stringDiffLength:1\
initial fuzzy Score:         0.82\
score w match index:         0.82\
score w index & length diff: 0.8195\
\
result:"hellzowww"\
matchIndx:0 resultlength:9 stringDiffLength:4\
initial fuzzy Score:         0.82\
score w match index:         0.82\
score w index & length diff: 0.818\
\
result:"hzello"\
matchIndx:1 resultlength:6 stringDiffLength:1\
initial fuzzy Score:         0.82\
score w match index:         0.818\
score w index & length diff: 0.8175\
\
result:"hzellowww"\
matchIndx:1 resultlength:9 stringDiffLength:4\
initial fuzzy Score:         0.82\
score w match index:         0.818\
score w index & length diff: 0.816\
\
