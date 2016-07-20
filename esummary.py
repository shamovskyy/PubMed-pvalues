import requests
import lxml
import xml.etree.ElementTree as et
#create a function that gets UID from date http://www.ncbi.nlm.nih.gov/pubmed?term=1997%2F10%2F06/ <= thjat's a sample query

def UIDfromdate(date):
    query="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmax=1000&term={}[edat]".format(date)
    get_query=requests.get(query)
    content=get_query.content
    with open('temp.xml','wb') as f:
        f.write(content)
    e= et.parse('temp.xml').getroot()
    return e
    
def getuidsfromquery(results):
    list_ids=[]
    for id in results.find('IdList').getchildren():
        list_ids.append(id.text)
    return list_ids

def getUIDfromdate(date):
    a=UIDfromdate(date)
    return getuidsfromquery(a)

def query(uID):
    query="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={}&version=2.0".format(uID)
    get_query=requests.get(query)
    content=get_query.content
    with open('temp.xml','wb') as f:
        f.write(content)
    e= et.parse('temp.xml').getroot()
    return e

def getcitationsfromquery(results):
    citations=results.find('DocumentSummarySet').find('DocumentSummary').find('PmcRefCount').text
    return citations

def getcitations(uID):
    x=query(uID)
    return int (getcitationsfromquery(x))


def extractAuthors(authors):
    values=[]
    columns = []
    for author in authors:
        values.append(author[0].text)
        columns.append(author[0].tag)
        print authors.tag,tuple(columns),tuple(values)
        check_insert_select('id','authors',tuple(columns),tuple(values))
    return authors.tag,tuple(columns),tuple(values)


def extractArticleIds(articleIds):
    values = []
    for articleId in articleIds:
        subvalues = []
        columns = []
        for tag in articleId:
            subvalues.append(tag.text)
            columns.append(tag.tag)
        values.append([articleIds.tag,tuple(columns),tuple(subvalues)])
    print values
    check_insert('id','papers',tuple(columns),tuple(subvalues))
    return values


def getallfromquery(root):
    list_tags=['Authors','ArticleIds']
    doc_summary = root.find('DocumentSummarySet').find('DocumentSummary')
    rec={}
    for child in doc_summary:
        if child.tag == 'Authors':
            extractAuthors(child)
        elif child.tag == 'ArticleIds':
            extractArticleIds(child)
        else:
            rec[child.tag] = child.text
    return rec


def getall(uID):
    return getallfromquery(query(uID))



#dict_cur.execute("INSERT INTO books (idex query) VALUES (%s,%s, %s,%s, %s, %s)",(index, query, book.title,
#       book.author, book.link_to_copies, libHash))






def getotherthingsfromquery(results):
    otherthings=results.find('DocumentSummarySet').find('DocumentSummary').find('Authors').text
    return otherthings



def getothers(uID):
    a=query(uID)
    return str (getotherthingsfromquery(a))





def finding_abstracts(uID):
    a=requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={}'.format(uID))
    if str(a)=='<Response [200]>':
        content=a.content
        if content.find('Error')>=0 and content.find('Error')<10:
            print uID
            print 'Error'
            return
        b=content.find('abstract "')
        if b==-1:
            print uID
            print 'no abstract'
            return
        print b,'b'
        length=content[b+10:].find('"')
        print length,'length'
        abstract=content[b+10:b+length+10]
        abstract=abstract.replace('\n','')
        abstract=abstract.replace('"','').replace("'","")
        return abstract





def getarticleinfo(minuID,maxuID):
    for i in range(minuID,maxuID):
        abstract=finding_abstracts(i)
        citations=getcitations(i)
        print i,abstract,citations


def check_insert(values_wanted, database_name, colnames=(), values=()):
        results = select(values_wanted, database_name, colnames, values)
        if results == []:
            insert(database_name, colnames, values)
        return

