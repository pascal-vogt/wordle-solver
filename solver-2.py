import re
import datetime
import glob
import sys

matchingFiles = glob.glob('main.*.js')
if len(matchingFiles) == 0:
  print('Put the main.*.js file of wordle in this directory first')
  sys.exit(-1)
minifiedCode = open(matchingFiles[0], mode="r", encoding="utf-8").read()
lines = [x.upper() for x in re.findall(r'"([a-z]{5})"', minifiedCode)]

def updateStats(c, d):
  if c not in d:
    d[c] = 1
  else:
    d[c] = d[c] + 1

def parsePreviousAttempt(previousAttemptAsText):
  result = {
    "correctIn": [None] * 5,
    "wrongIn": [None] * 5,
    "letterCount": {},
    "minLetterCount": {}
  }
  
  # Build some stats about the response for the individual letters. Sometime it's easier to look at them
  # per letter instead of per position
  letterStats = {}
  for i in range(5):
    letter = previousAttemptAsText[2 * i]
    letterResult = previousAttemptAsText[2 * i + 1]
    if not letter in letterStats:
      letterStats[letter] = {
        "correctCount": 0,
        "misplacedCount": 0,
        "wrongCount": 0
      }
    if letterResult == ':':
      letterStats[letter]["correctCount"] += 1
    elif letterResult == '.':
      letterStats[letter]["misplacedCount"] += 1
    elif letterResult == ' ':
      letterStats[letter]["wrongCount"] += 1

  # Fill minLetterCount/letterCount info (one is the exact letter count, the other just a lower bound)
  for letter, stats in letterStats.items():
    if stats["wrongCount"] > 0:
      result["letterCount"][letter] = stats["correctCount"] + stats["misplacedCount"]
    elif stats["correctCount"] + stats["misplacedCount"] > 0:
      result["minLetterCount"][letter] = stats["correctCount"] + stats["misplacedCount"]

  # Fill correctIn/wrongIn
  for i in range(5):
    letter = previousAttemptAsText[2 * i]
    letterResult = previousAttemptAsText[2 * i + 1]
    if letterResult == ':':
      result["correctIn"][i] = letter
    else:
      result["wrongIn"][i] = letter
  return result

def parsePreviousAttempts(previousAttemptsAsText):
  return [parsePreviousAttempt(x) for x in previousAttemptsAsText]

def testWord(w, previousAttempts):
  blacklist = set()
  locked = set()
  requiredAt = {}
  for previousAttempt in previousAttempts:
    letterCounts = {}
    for i in range(5):
      letter = w[i]
      if not letter in letterCounts:
        letterCounts[letter] = 1
      else:
        letterCounts[letter] += 1
      if previousAttempt["correctIn"][i] is not None and letter != previousAttempt["correctIn"][i]:
        return False
      if previousAttempt["wrongIn"][i] is not None and letter == previousAttempt["wrongIn"][i]:
        return False
    for letter, letterCount in previousAttempt["letterCount"].items():
      count = letterCounts[letter] if letter in letterCounts else 0
      if count != letterCount:
        return False
    for letter, minLetterCount in previousAttempt["minLetterCount"].items():
      count = letterCounts[letter] if letter in letterCounts else 0
      if count < minLetterCount:
        return False
  return True

def getNextWord(previousAttempts):
  stats = [ {} ] * 5
  
  candidates = []
  for word in lines:
    if testWord(word, previousAttempts):
      updateStats(word[0], stats[0])
      updateStats(word[1], stats[1])
      updateStats(word[2], stats[2])
      updateStats(word[3], stats[3])
      updateStats(word[4], stats[4])
      candidates.append(word)
  
  lastBestWord = [None] * 5
  for i in range(5):
    bestFrequency = -1
    bestWord = None
    for word in candidates:
      for i in range(5):
        if lastBestWord[i] is None:
          letter = word[i]
          frequency = stats[i][letter]
          if frequency > bestFrequency:
            bestWord = [x for x in lastBestWord]
            bestWord[i] = letter
    lastBestWord = bestWord
    newCandidates = []
    for word in candidates:
      for i in range(5):
        if lastBestWord[i] is None or lastBestWord[i] == word[i]:
          newCandidates.append(word)
    candidates = newCandidates
  return ''.join(lastBestWord)

def getWordResult(attempt, truth):
  result = {
    "correctIn": [None] * 5,
    "wrongIn": [None] * 5,
    "letterCount": {},
    "minLetterCount": {}
  }
  letterCountsTruth = {}
  letterCountsAttempt = {}
  for i in range(5):
    # Truth stats
    if truth[i] not in letterCountsTruth:
      letterCountsTruth[truth[i]] = 1
    else:
      letterCountsTruth[truth[i]] += 1
  for i in range(5):
    # Attempt stats (again)
    if attempt[i] not in letterCountsAttempt:
      letterCountsAttempt[attempt[i]] = 1
    else:
      letterCountsAttempt[attempt[i]] += 1

    if attempt[i] == truth[i]:
      result["correctIn"][i] = attempt[i]
    else:
      result["wrongIn"][i] = attempt[i]
      letterCountTruth = letterCountsTruth[attempt[i]] if attempt[i] in letterCountsTruth else 0
      if letterCountsAttempt[attempt[i]] > letterCountTruth:
        result["letterCount"][attempt[i]] = letterCountTruth
      else:
        result["minLetterCount"][attempt[i]] = letterCountsAttempt[attempt[i]]
    
  return result

def testAlgorithm(truth, n):
  print('Testing algorithm with: %s' % truth)
  previousAttempts = []
  guessedIn = None
  for i in range(n):
    if guessedIn is None:
      attempt = getNextWord(previousAttempts)
      if attempt == truth:
        guessedIn = i + 1
      if attempt is not None:
        result = getWordResult(attempt, truth)
        print('Testing: %s -> %s' % (attempt, result))
        previousAttempts.append(result)
      else:
        print('Out of options')
  print('Guessed in %s attempts' % guessedIn)
  print('')
  return guessedIn

# This can be uncommented to test how the algorithm performs in general, current average attempts is ~4.752861
# nbGuessesSum = 0
# nbWords = 0
# hardestWord = None
# hardestWordNbGuess = 0
# for word in lines:
#   nbGuesses = testAlgorithm(word, 20)
#   nbGuessesSum += nbGuesses
#   nbWords += 1
#   if hardestWordNbGuess < nbGuesses:
#     hardestWord = word
#     hardestWordNbGuess = nbGuesses
#   print('== Average guess amount so far is %f (#words tested %d, hardest word so far was %s in %d guesses) ==\n\n' % (nbGuessesSum / nbWords, nbWords, hardestWord, hardestWordNbGuess))

# The array contains the previous answers, basically you have to write the word with each letter followed by ':' for a green letter, '.' for a yellow one and ' ' for a black one
# print(getNextWord(parsePreviousAttempts(['C:A R E S ', 'C:L.I N K ', 'C:O:Y L:Y '])))
print(getNextWord(parsePreviousAttempts([])))