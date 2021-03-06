import requests
import lxml
from xml.etree import ElementTree as et
from datetime import date, timedelta as td, datetime
import logging
import time
import psycopg2
from secret import dict_cur, conn
from psycohandler import *
import sys 
import csv
reload(sys)
sys.setdefaultencoding('utf-8')



#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)

def getUIDsfromCSV(filename):
    with open(filename, "rU") as f:
        reader=csv.reader(f)
        uids=[row[0] for row in reader if any(row)]
    return uids

def main(start_month=0, start_day=0, start_year=0, no_of_days_to_check=0):
    start_time=time.time()
    uids= getUIDsfromCSV("UIDsPvalues.csv")[601:700]
    # start_date = date(start_year,start_month,start_day)
    # for i in range(no_of_days_to_check + 1):
    #     uids=getUIDsFromDate( (start_date+td(days=i)).strftime("%Y/%m/%d"))
    #     print len(uids)
    for uID in uids:
        print uID
        tree= queryEsummaryByUID(uID)
        retries=0
        while not tree:
            retries+=1
            time.sleep(60)
            tree= queryEsummaryByUID(uID)
            if retries>=7:
                break
        abstract=getAbstractFromUID(uID)
        if abstract:
            getAllFromEsumXML(tree, uID)
            dict_cur.execute("UPDATE papers SET abstract='{}' WHERE uid='{}';".format(abstract, uID))


    print time.time()-start_time


def queryEsearchByDate(date, tries=0):
    query="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmax=10000&term={}[pdat]".format(date)
    print query
    get_query=requests.get(query)
    try:
        content=get_query.content        
        tree= et.fromstring(content)
        return tree


    except Exception as e:
        #logger.error("No content found for %s, %s. Exception %s thrown", date, query, e)
        print "No content found for %s, %s. Exception %s thrown", date, query, e
def getUIDsFromEsearchXML(tree):   
    list_ids=[]
    try:    
        for id in tree.find('IdList').getchildren():
            list_ids.append(id.text)

    except Exception as e:
        #logger.error("Cannot find id list for %s. Exception %s thrown", date, e)
        print "Cannot find id list for %s. Exception %s thrown", date, e
    return list_ids

def getUIDsFromDate(date):
    tree=queryEsearchByDate(date)
    return getUIDsFromEsearchXML(tree)


def queryEsummaryByUID(uID):
    query="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={}&version=2.0".format(uID)
    get_query=requests.get(query)
    try:
        content=get_query.content
        tree= et.fromstring(content)
        return tree

    except Exception as e:
        #logger.error("No content found for %s, %s. Exception %s thrown", uID, query, e)
        print "No content found for %s, %s. Exception %s thrown", uID, query, e        

def extractAuthors(authors, uid):
    for author in authors:
        authorName=author.find("Name").text.replace("'","").replace('"',"")
        authorID=check_insert_select('id','authors',("Name",),(authorName,))[0][0]
        check_insert("id", "Authors_Papers", ("AuthorId", "PaperId"), (authorID, uid))


def extractArticleIds(articleIds):
    columns=[]
    values = []
    for articleId in articleIds:
            columns.append(articleId.find("IdType").text.replace("-",""))
            values.append(articleId.find("Value").text)
    return columns, values


def getAllFromEsumXML(tree, uid):
    list_tags=['Authors','ArticleIds']
    doc_summary = tree.find('DocumentSummarySet').find('DocumentSummary')
    rec={}
    columns=["uid"]
    values=[uid]
    for child in doc_summary:
        if child.tag == 'Authors':
            authorIDs=extractAuthors(child, uid)
        elif child.tag == 'ArticleIds':
            artcolumns, artvalues=extractArticleIds(child)
            for i in range(len(artcolumns)): 
                if child.text!=None and not ("\n") in child.text and child.text!="null": 
                    rec[artcolumns[i]]=artvalues[i]
                    columns.append(artcolumns[i])
                    values.append(artvalues[i].replace("'",""))
        elif child.text!=None and not ("\n") in child.text and child.text!="null":
            rec[child.tag] = child.text
            columns.append(child.tag)
            values.append(child.text.replace("'","").replace('"',""))
            if child.tag=="FullJournalName":
                journalid=check_insert_select("id", "journals", ("name",), (child.text.replace("'","").replace('"',""),))[0][0]
                columns.append("journalid")
                values.append(journalid)
    values.append( values[columns.index("PubDate")])
    columns.append( "PubDateString")

    #logging.debug(columns, "columns")
    #logging.debug(values, "values")
    try:
        check_insert("uid","papers", tuple(columns),tuple(values))
    except psycopg2.DataError:
        if (values[columns.index("PubDate")].find("-")!=-1):
            date=values[columns.index("PubDate")][0:values[columns.index("PubDate")].index("-")]
        else:
            date=values[columns.index("PubDate")]

        if len(date.split())==1:
            date=date+" Jan"
        if len(date.split())==2:
            date=date+" 01"
        try:
            date=datetime.strptime(date,'%Y %b %d').strftime('%Y %m %d')
        except ValueError:
            date=datetime.strptime(date.split()[0]+" Jan 01", '%Y %b %d').strftime('%Y %m %d')
        values[columns.index("PubDate")]=date
        check_insert("uid","papers", tuple(columns),tuple(values))

    return rec



#dict_cur.execute("INSERT INTO books (idex query) VALUES (%s,%s, %s,%s, %s, %s)",(index, query, book.title,
#       book.author, book.link_to_copies, libHash))





'''
def getotherthingsfromquery(results):
    otherthings=results.find('DocumentSummarySet').find('DocumentSummary').find('Authors').text
    return otherthings



def getothers(uID):
    a=query(uID)
    return str (getotherthingsfromquery(a))

def getcitationsfromXML(tree):
    try:
        citations=tree.find('DocumentSummarySet').find('DocumentSummary').find('PmcRefCount').text
        return int(citations)

    except Exception as e:
        logger.error("Cannot find citations. Exception %s thrown", e)
        return None

def getCitationsFromUID(uID):
    tree= queryEsummaryByUID(uID)
    return getcitationsfromXML(tree)

'''


def getAbstractFromUID(uID):
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
        length=content[b+10:].find('",')
        abstract=content[b+10:b+length+10]
        abstract=abstract.replace('\n','')
        abstract=abstract.replace('"','').replace("'","")


        return abstract



def getarticleinfo(minuID,maxuID):
    for i in range(minuID,maxuID):
        abstract=finding_abstracts(i)
        citations=getcitations(i)
        print i,abstract,citations

#main()