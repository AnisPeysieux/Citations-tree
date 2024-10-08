import requests
import time

doi = "DOI:10.1145/3544838"
maxDepth = 1
baseURL = 'https://api.semanticscholar.org/graph/v1/paper/'

def makeNode(data):
    #print("data=",data)
    #ret = "title: " + data["title"] + "\n" + "authors:"
    ret = "title: " + data["title"] + " | " + "authors:"
    for a in data["authors"]:
        ret += " " + a["name"]
    ret += " | year: " + str(data["year"]) + " | paperId: " + str(data["paperId"])
    return ret

url = baseURL + doi

#Define which details about the paper you would like to receive in the response
paperDataQueryParams = {'fields': 'title,year,authors.name,references.title,references.authors,references.externalIds,references.year'}

#Send the API request and store the response in a variable
while True:
    response = requests.get(url, params=paperDataQueryParams)
    if response.status_code == 200:
        break
    else:
        print(f"seed response failed with errorcode:{response.status_code}")
        time.sleep(1)

response = response.json()


seedId = response["paperId"]

paperIdFixes = {
}


pile = [seedId]
pileDepth = [0]
papers_done = []
connectivity = {}
failed = 0
success = 0
total_refs=0
while len(pile) > 0:
    paperId = pile.pop()
    paperDepth = pileDepth.pop()
    if paperId in papers_done:
        continue
    url = baseURL + paperId
    print("url = " + url + " depth = " + str(paperDepth))
    while True:
        print("request paper")
        response = requests.get(url, params=paperDataQueryParams)
        time.sleep(1)
        if response.status_code == 200:
            print("paper response succeed")
            success += 1
            papers_done.append(paperId)
            response = response.json()
            paperNode = makeNode(response)
            if paperNode not in connectivity:
                connectivity[paperNode] = []
                total_refs += len(response["references"])
                for ref in response["references"]:
                    if ref["paperId"] in paperIdFixes:
                        print("fix " + ref["paperId"])
                        urlfix = baseURL + paperIdFixes[ref["paperId"]]
                        while True:
                            print("request fix")
                            time.sleep(1)
                            ref = requests.get(urlfix, params=paperDataQueryParams)
                            if ref.status_code == 200:
                                print("fix response succeed")
                                ref = ref.json()
                                break;
                            else:
                                print(f"fix response failed with errorcode:{ref.status_code}")

                    connectivity[paperNode].append(makeNode(ref))
                    if ref["paperId"] != None:
                        if (maxDepth != None and paperDepth+1 <= maxDepth) or maxDepth == None:
                            pile.append(ref["paperId"])
                            pileDepth.append(paperDepth+1)
            break;
        else:
            failed += 1
            print(f"paper response failed with errorcode:{response.status_code}")
    print(f"success: {success/(success+failed)}({success}) papers: {len(papers_done)} refs: {total_refs/len(papers_done)}({total_refs})")

f = open("connectivity.csv", "a")
f.write("\"influenced\",\"influenced_lab\",\"influencer\",\"influencer_lab\"\n")
for key in connectivity.keys():
    for value in connectivity[key]:
        f.write(f"\"{key}\",\"{key}\",\"{value}\",\"{value}\"\n")
f.close()
