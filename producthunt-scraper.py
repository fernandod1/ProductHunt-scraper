#!/usr/bin/env python3.5

# Copyright (c) 2019 Fernando
# Url: https://github.com/dlfernando/
# License: MIT

from bs4 import BeautifulSoup
import requests
import re
import time
import xlwt 
from xlwt import Workbook


EXCEL_FILE = "sample.xls"
TOTALPOSTSTOGET = 50
FROM = 50
TRACK404 = 0 # not modify this var


def parse_html(url):
    html_doc = requests.get(url)
    soup = BeautifulSoup(html_doc.text, "html.parser")
    return soup

def scrap_all_posts_links(soup):
    all_links = []
    links=soup.find_all("a")
    for link in links:
        if "/posts/" in link.attrs['href']:
            if link.attrs['href'] not in all_links :
                all_links.append(str(link.attrs['href']))
    return all_links

def list_clean(txt):
    txt = txt.replace('["','')
    txt = txt.replace('"]','')
    txt = txt.split('","')
    return txt

def scrap_post_content(post_id,ii,sheet):
    global TRACK404
    post_data = {}
    soup0 = parse_html("https://www.producthunt.com/posts/"+str(post_id))
    soup = str(soup0)
    if "flagged for removal" in soup:
        print("Info: this post DOES NOT EXISTS") 
        TRACK404=TRACK404+1
    elif "Page Not Found" in soup:
        print("Info: this post DOES NOT EXISTS") 
        TRACK404=TRACK404+1
    else:
        title = soup0.find("meta",  property="og:title")
        short_description=title["content"].split(" - ")[1]
        post_data["title"] = title["content"].split(" - ")[0]
        post_data["short_description"]=short_description.split("| ")[0]
        categories = re.search('applicationCategory":(.*?),"author', soup)
        if categories is not None:            
            categories = list_clean(categories.group(1))
            categories_cs = ""
            for onecat in categories:
                categories_cs = categories_cs+","+onecat
            if categories_cs==",[]":
                post_data["categories"] = ""
            else:
                post_data["categories"] = categories_cs
        else:
            print("Info: post doesnt contains categories")
            post_data["categories"] = ""   
        image = soup0.find("meta",  property="og:image")
        post_data["logo"] = image["content"]
        try:
            if "aggregateRating" in soup: 
                images = re.search('screenshot":(.*?),"aggregateRating', soup)
                if images is not None:   
                    images = list_clean(images.group(1))
                    images_cs = ""
                    for oneimg in images:
                        images_cs = images_cs+","+oneimg
                    if images_cs==",[]":
                        post_data["images"] = ""
                    else:    
                        post_data["images"] = images_cs
                else:
                    post_data["images"] = ""
            else:
                images = re.search('screenshot":(.*?),"operatingSystem', soup)
                if images is not None:   
                    images = list_clean(images.group(1))
                    images_cs = ""
                    for oneimg in images:
                        images_cs = images_cs+","+oneimg
                    if images_cs==",[]":
                        post_data["images"] = ""
                    else:    
                        post_data["images"] = images_cs
                else:
                    post_data["images"] = ""
        except:
            print("Info: post doesnt contains aditional images.")
        upvote = re.search('<span class="bigButtonCount_(.*)">(.*)</span></span></button>', soup)
        if upvote is None:
            print("Info: post doesnt contains upvote")
            post_data["upvotes"] = ""
        else:
            post_data["upvotes"] = upvote.group(2)  
        description = soup0.find("meta",  property="og:description")
        post_data["description"] = description["content"]
        post_date = re.search('"created_at":"(.*?)","', soup)
        if post_date is not None:
            post_data["postdate"] = post_date.group(1)[0:10]
        else:
            print("Info: post doesnt contains post_date")
            post_data["postdate"] = ""
        website = re.search('"website_name":"(.*?)","devices"', soup)
        if website is None:
            print("Info: post doesnt contains website")
            post_data["product_web"] = ""
        else:
            post_data["product_web"] = website.group(1)  
        badge_check = re.search('</path></g></svg></span><div class="side_(.*?)">(.*?)</span></div></div>', soup)
        if badge_check is not None:
            badge_div = badge_check.group(0).replace('</span><span',' </span><span')
            badge_div = re.sub('<[^<]+?>', '', badge_div)
            post_data["badge"] = ' '.join(badge_div.split()[:5])
            badge_date = badge_div.replace(post_data["badge"], "")
            post_data["badge_date"] = badge_date.replace(' ','')
        else:            
            post_data["badge"] = ""
            post_data["badge_date"]  = ""
        reviews = re.search('"disabled_when_scheduled":true,"reviews_rating":(.*?),"reviews_count"', soup)
        if reviews is None:
            print("Info: post doesnt contains reviews")
            post_data["reviews"] = ""
        else:
            post_data["reviews"] = (reviews.group(1))
        n_reviews = re.search('"reviews_count":(.*?),"can_manage":', soup)
        if n_reviews is None:
            print("Info: post doesnt contains n_reviews")
            post_data["n_reviews"] = ""
        else:
            post_data["n_reviews"] = (n_reviews.group(1))
        hunter_url = re.findall('<a class="card_(.*?)" href="/@(.*?)"><div class="userImage', soup)
        if hunter_url is not None:
            i=0
            maker_url=""
            for unno in hunter_url:
                if i>0:
                    maker_url=maker_url+",https://www.producthunt.com/@"+unno[1]
                i=i+1
            post_data["hunter_url"] = "https://www.producthunt.com/@"+hunter_url[0][1]
            post_data["maker_url"] = maker_url
        else:
            print("Info: post doesnt contains hunter_url/maker_url")
            post_data["hunter_url"] = ""
            post_data["maker_url"] = ""
        url = soup0.find("meta",  property="og:url")
        post_data["product_hunt_url"] = url["content"]

        print (str(post_id)+" - "+str(post_data["product_hunt_url"])+" -> DONE")
        pointer = ii-TRACK404
        fill_excel(post_data,pointer,sheet)

    


def get_first_post_link(soup):
    if "Popular this month" in str(soup):
        first = soup.find_all('a', href=re.compile('^/posts/'))[6]['href']
    else:
        first = soup.find_all('a', href=re.compile('^/posts/'))[1]['href']
    return first

def get_post_ID(url):
    content=str(parse_html(url))
    idpost = re.search('post_id=(.*?)&amp;theme=light', content)
    if idpost is not None:
        id_post=idpost.group(1)   
    else:
        id_post=""
        print("ERROR: NOT POST ID FOUND.")
    return id_post

def fill_excel(d,i,sheet):    
    if i==0:
        style = xlwt.easyxf('font: bold 1')
        sheet.write(0, 0, 'Title', style) 
        sheet.write(0, 1, 'Short Description', style) 
        sheet.write(0, 2, 'Category', style) 
        sheet.write(0, 3, 'Logo URL', style) 
        sheet.write(0, 4, 'Gallery Image URLs', style) 
        sheet.write(0, 5, 'Upvote', style) 
        sheet.write(0, 6, 'description', style) 
        sheet.write(0, 7, 'Post Date', style) 
        sheet.write(0, 8, 'Product website URL', style) 
        sheet.write(0, 9, 'Badge', style) 
        sheet.write(0, 10, 'Badge Date', style) 
        sheet.write(0, 11, 'No. of reviews', style) 
        sheet.write(0, 12, 'Reviews', style) 
        sheet.write(0, 13, 'Hunter URL', style) 
        sheet.write(0, 14, 'Marker URL', style) 
        sheet.write(0, 15, 'Product Hunt URL', style)
    row = 1+i
    col = 0
    itemplus = ""
    for key in d.keys():
        for item in d[key]:
            itemplus=""+itemplus+""+item+""
        sheet.write(row, col, itemplus)
        itemplus = ""
        col += 1


try: 

    soup= parse_html("https://www.producthunt.com/newest")
    first_link = get_first_post_link(soup)
    post_id = int(get_post_ID("https://www.producthunt.com"+first_link+"/embed"))

    i=0
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("Sheet 1")
    if FROM>0:
        post_id = post_id-FROM
    while i!=TOTALPOSTSTOGET:
        print("-----------------------------------------------------")
        scrap_post_content(post_id,i,sheet)
        post_id=post_id-1
        i=i+1
        time.sleep(0.2)    
    workbook.save(EXCEL_FILE)


except:
    workbook.save(EXCEL_FILE)
    print("ERROR: there was a problem in main execution.")


