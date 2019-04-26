#各种import， time，json, Review是另外一个class（原来这个东西是python 2.7的所以有新建class）
import time
import json
import Review
from bs4 import BeautifulSoup

#selenium是爬一个网站多个subdirectory必备，它可以搞定登录这些事情，记得下载chromedriver这东西
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import csv

#这账号是我建的，直接用
username = "1002423907@qq.com" # your email here
password = "1234567890" # your password here

# Manual options for the company, num pages to scrape, and URL
#这东西后面有company list的话就可以写成function了
#page数量先设成1 好debug
pages = 1
companyName = "microsoft"
companyURL = "https://www.glassdoor.com/Interview/Microsoft-Software-Development-Engineer-Interview-Questions-EI_IE1651.0,9_KO10,39.htm"

#obj_dict和json_export是要连起来用，但是似乎效果并不好
def obj_dict(obj):
    return obj.__dict__


def json_export(data):

    jsonFile = open(companyName + ".json", "w")
    for i in data:
        jsonFile.write(json.dumps(i, indent=4, separators=(',', ': '), default=obj_dict).encode('utf-8'))
    jsonFile.close()
#enddef

#csv export我写的但是和json一样有bytes写不了的问题，就是quesitons 里面有一些bytes没有变成string或者过滤掉
#但现在csv可以把file 写出来
def csv_export(data):
	csv=open(companyName+".csv",'w')
	for content in data:
		row= content.date+','+content.role+','+content.gotOffer+','+content.experience+','+content.difficulty+','+content.length+','+content.details+','
		for x in content.questions:
			try:
				row=row+x
				row+=','
			except:
				pass
		row.replace(row[-1],'\n')
		csv.write(row)
	csv.close()	


#这里就是初始化driver
def init_driver():
    driver = webdriver.Chrome(executable_path = "./chromedriver")
    driver.wait = WebDriverWait(driver, 10)
    return driver
#enddef


def login(driver, username, password):
    driver.get("http://www.glassdoor.com/profile/login_input.htm")
    try:
		#注意那些located，这些都是直接进网站里面根据html attribute搞出来的
		user_field = driver.wait.until(EC.presence_of_element_located((By.NAME, "username")))
		pw_field = driver.find_element_by_id("userPassword")
        #login_button = driver.find_element_by_class_name("gd-btn gd-btn-1 minWidthBtn")
		user_field.send_keys(username)
		user_field.send_keys(Keys.TAB)
		time.sleep(1)
		pw_field.send_keys(password)
		time.sleep(1)
        #login_button.click()
		driver.find_element_by_xpath('//button[@type="submit"]').click()

    except TimeoutException:
        print("TimeoutException! Username/password field or login button not found on glassdoor.com")
#enddef

#一个parse的function，还是根据html tag attribute 找到对应的地方然后把tag 里面的内容拉出来parse，这个比较具体
#没什么东西要变因为网站架构没怎么变
def parse_reviews_HTML(reviews, data):
	for review in reviews:
		length = "-"
		gotOffer = "-"
		experience = "-"
		difficulty = "-"
		date = review.find("time", { "class" : "date" }).getText().strip()
		role = review.find("span", { "class" : "reviewer"}).getText().strip()
		outcomes = review.find_all("div", { "class" : ["tightLt", "col"] })
		if (len(outcomes) > 0):
			gotOffer = outcomes[0].find("span", { "class" : "middle"}).getText().strip()
		#endif
		if (len(outcomes) > 1):
			experience = outcomes[1].find("span", { "class" : "middle"}).getText().strip()
		#endif
		if (len(outcomes) > 2):
			difficulty = outcomes[2].find("span", { "class" : "middle"}).getText().strip()
		#endif
		appDetails = review.find("p", { "class" : "applicationDetails mainText truncateThis wrapToggleStr "})
		if (appDetails):
			appDetails = appDetails.getText().strip()
			tookFormat = appDetails.find("took ")
			if (tookFormat >= 0):
				start = appDetails.find("took ") + 5
				length = appDetails[start :].split('.', 1)[0]
			#endif
		else:
			appDetails = "-"
		#endif
		details = review.find("p", { "class" : "interviewDetails"})
		if (details):
			s = details.find("span", { "class" : ["link", "moreLink"] })
			if (s):
				s.extract() # Remove the "Show More" text and link if it exists
			#endif
			details = details.getText().strip()
		#endif
		questions = []
		qs = review.find_all("span", { "class" : "interviewQuestion"})
		if (qs):
			for q in qs:
				s = q.find("span", { "class" : ["link", "moreLink"] })
				if (s):
					s.extract() # Remove the "Show More" text and link if it exists
				#endif
				questions.append(q.getText().encode('utf-8').strip())
				#print(questions[0])
			#endfor
		#endif
		r = Review.Review(date, role, gotOffer, experience, difficulty, length, details, questions)
    
		data.append(r)
	#endfor
	return data
#enddef

#这个就是爬的过程
def get_data(driver, URL, startPage, endPage, data, refresh):
	if (startPage > endPage):
		return data
	#endif
	print ("\nPage " + str(startPage) + " of " + str(endPage))
	currentURL = URL + "_IP" + str(startPage) + ".htm"
	time.sleep(2)
	#endif
	if (refresh):
		driver.get(currentURL)
		print ("Getting " + currentURL)
	#endif
	time.sleep(2)
	HTML = driver.page_source
	soup = BeautifulSoup(HTML, "html.parser")
	reviews = soup.find_all("li", { "class" : ["empReview", "padVert"] })
	if (reviews):
		data = parse_reviews_HTML(reviews, data)
		print ("Page " + str(startPage) + " scraped.")
		if (startPage % 10 == 0):
			print ("\nTaking a breather for a few seconds ...")
			time.sleep(10)
		#endif
		get_data(driver, URL, startPage + 1, endPage, data, True)
	else:
		print ("Waiting ... page still loading or CAPTCHA input required")
		time.sleep(3)
		get_data(driver, URL, startPage, endPage, data, False)
	#endif
	return data
#enddef

if __name__ == "__main__":
	driver = init_driver()
	time.sleep(3)
	print ("Logging into Glassdoor account ...")
	login(driver, username, password)
	time.sleep(5)
	print ("\nStarting data scraping ...")
	data = get_data(driver, companyURL[:-4], 1, pages, [], True)
	print ("\nExporting data to " + companyName + ".csv")
	csv_export(data)
	driver.quit()
