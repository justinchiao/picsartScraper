import requests
import string
import re
import csv
from bs4 import BeautifulSoup
import selenium
from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.chrome.service import Service as ChromeService 
from webdriver_manager.chrome import ChromeDriverManager 
import numpy as np
import time
import random
import copy
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import pandas as pd

def sitemap():
    url = 'https://picsart.com/blog/sitemap.xml'
    #Pulls page HTML
    page = requests.get(url)
    #creates soup object
    soup = BeautifulSoup(page.content, "lxml-xml")

    subMaps = []
    for xml in soup.find_all('loc'):
        subMaps = subMaps + [xml.text]
    subMaps = subMaps[1:]
    posts = []
    for xml in subMaps:
        #Pulls page HTML
        page = requests.get(xml)
        #print(page.content)
        #creates soup object
        soup = BeautifulSoup(page.content, "lxml-xml")

        for html in soup.find_all('loc'):
            posts = posts + [html.text]
    df = pd.DataFrame(posts)
    df.to_csv('masterList.csv', mode='w', index=False, header=False)
    return posts

def scrapePost(url):
    #Pulls page HTML
    page = requests.get(url)
    #creates soup object
    soupPage = BeautifulSoup(page.content, "html.parser")

    title = soupPage.find("h1").text
    textList = []
    for bod in soupPage.find_all(['p', 'h2', 'h3', 'h4']):
            textList = textList + [' ' + bod.text]
    
    if textList[-1] == ' This website is using cookies to improve your user experience. By continuing, you agree to our Cookie Policy.':
              del textList[-1]
    
    text = ''
    for i in range(len(textList)): 
        text = text + textList[i]
    text = textCleaner(text + '' + title)
    return text

def textCleaner(inputString):
    '''returns list of one word strings without any extra spaces, line breaks, or special characters.'''

    #remove punctuation and conver to all lowercase
    noPunc = inputString.translate(str.maketrans('', '', string.punctuation)).lower()

    #removes extra spaces and line breaks
    res = ""
    res2 = ""
    for i in range(len(noPunc)):
        if (noPunc[i] == " " and noPunc[i-1] == " " ) or ord(noPunc[i]) == 10:
            pass
        else:
            res += noPunc[i]
    for i in range(len(res)):
        if (res[i] == " " and res[i-1] == " ") or ord(res[i]) == 10:
            pass
        else:
            res2 += res[i]    
    
    #remove emojis/special char
    wordList = makeList(res2)
    for i in range(len(wordList)):
        if not wordList[i].isalnum():
            newWord=""
            for k in range(len(wordList[i])):
                if wordList[i][k].isalnum():
                    newWord = newWord + wordList[i][k]
            wordList[i] = newWord
    return wordList

def makeList(string):
    return list(string.split(" "))

count = {} #{word,frequency}
def counter(url):
    '''Stores frequency of every word in the main post and comments in dictionary count'''
    allWords = scrapePost(url)
    for i in range(len(allWords)):
        if allWords[i] in count: #if this word has already been encountered add one to its dictionary value
            count[allWords[i]] = count[allWords[i]] + 1
        else: #if this is the first time this word has been encountered, create dictionary item with word as key and value equal to one
            count[allWords[i]] = 1

def countAllPages(list):
    '''Iterates counter on all URLS in list'''
    for i in range(len(list)):
        counter(list[i])

def filterDictRemove(dict):
    '''filters dictionary to exclude unwanted words'''
    with open('noiseWords.csv', newline='') as f:
        search = list(csv.reader(f))
    noiseWords = []
    for i in range(len(search)):
        noiseWords.append(search[i][0])

    keys = list(dict.keys())
    staticKeys = copy.deepcopy(keys)
    for i in range(len(staticKeys)):
        if  keys[i] in noiseWords:
            del dict[staticKeys[i]]

def filterDictKeep(dict):
    '''filters dictionary to exclude unwanted words'''
    with open('keepWords.csv', newline='') as f:
        search = list(csv.reader(f))
    keepWords = []
    for i in range(len(search)):
        keepWords.append(search[i][0])

    keys = list(dict.keys())
    staticKeys = copy.deepcopy(keys)
    for i in range(len(staticKeys)):
        if  keys[i] not in keepWords:
            del dict[staticKeys[i]]

def exportCSV(dict, name):
    '''exports dict as CSV'''

    with open(name, 'w', newline='', encoding = 'utf-8') as csvfile:
        header_key = ['word', 'freq']
        new_val = csv.DictWriter(csvfile, fieldnames=header_key)

        new_val.writeheader()
        for new_k in dict:
            new_val.writerow({'word': new_k, 'freq': dict[new_k]})

def wordCloud(dict):
    '''creates wordcloud using dictioanry keys as words and dictionary value as frequency'''
    text = ''
    key = list(dict.keys())
    for i in range(len(key)):
        text = text + ((key[i] + ' ')* dict[key[i]])

    word_cloud = WordCloud(
        width=3000,
        height=2000,
        random_state=1,
        background_color="black",
        colormap="Pastel1",
        collocations=False,
        stopwords=STOPWORDS,
        ).generate(text)

def main():
    print('Update Blog posts?\n')
    userInput = input('Y/N\n')
    if userInput in ['Y','y']:
        start_time = time.time()
        posts = sitemap()
        print('Blog post list updated')
        countAllPages(posts)
        print('words counted')
    elif userInput in ['N','n']:
        start_time = time.time()
        with open('masterList.csv', newline='') as f:
            search = list(csv.reader(f))
        posts = []
        for i in range(len(search)):
            posts.append(search[i][0])
        print('masterList opened')
        countAllPages(posts)
        print('words counted')
    else:
        main()

    exportCSV(count, "wordFrequency.csv")
    print('full csv exported')   
    filterDictKeep(count)
    print('words filtered')
    exportCSV(count, "wordFrequencyFiltered.csv")
    print('filtered csv exported')
    print("--- %s seconds ---" % (time.time() - start_time))
    wordCloud(count)

if __name__ == "__main__":
    main()