"""
WA module for scraping and processing text from https://leg.wa.gov 

# Status, as of January 1, 2022

Current Coverage (In Active Development):
    [X] Committee Hearings (Audio Links) (2015 - 2020)

Planned Coverage:
    [ ] Committee Hearings (Video Links) (2000 - 2014)
    [ ] Floor Speeches (Video Links)

# WA Work Flow

CLASS Scrape

    - wa_scrape_links by desired committee and legislative session. 
    Function filters TVW archives by function parameters
    for links to each individual committee meeting for that calendar year
    
    - wa_scrape_audio by wa_scrape_links output 
    Function downloads audio files to local drive
    Renames the file names by committee name and date (YYYYMMDD) (e.g. wa_education_20200305.mp3)

CLASS Process

    - wa_speech_to_text
    Function gives the user option to convert audio file to a text transcript through DeepSpeech
    Uses mp3 links directly to process the transcripts
    Downloads the transcript in json form, single json for each committee/legislative session
    
    - wa_text_clean
    Function conducts tests and run light cleaning to ensure transcript is ready for text analysis

"""

from datetime import datetime
import os
import sys
import re
import time

from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

#TESTING 

dir_chrome_webdriver = "/Users/katherinechang/Google Drive/My Drive/State Legislatures/StateLegiscraper/statelegiscraper/assets/chromedriver/chromedriver_v96_m1"

param_committee = "House Education"

param_year = "2017"

class Scrape:
    """
    Scrape functions for Washington State Legislature website
    Current coverage includes committee hearing audio links 
    """

    def wa_scrape_links(param_committee, param_year, dir_chrome_webdriver, dir_save):
        """
        Webscrape function for Washington State Legislature Website for 2015-2020 sessions 
        
        Parameters
        ----------
        param_committee : String
            Standing committee hearing name.
            See available list through package assets
            "from statelegiscraper.assets.package import wa_names"
        param_year : String
            Calendar year (Current coverage limited to 2015-2021).
        dir_chrome_webdriver : String
            Local directory that contains the appropriate Chrome Webdriver.
        dir_save : String
            Local directory to save JSON with audio links.
    
        Returns
        -------
        A JSON file saved locally with selected committee and year audio links
    
        """
        
        if not isinstance(param_committee, str):
            raise ValueError("Committee name must be a string")
        else:
            pass

        if not isinstance(param_year, str):
            raise ValueError("Year selection must be a string")
        else:
            pass

        if not os.path.exists(dir_chrome_webdriver):
            raise ValueError("Chrome Webdriver not found")
        else:
            pass

        if not os.path.exists(dir_save):
            raise ValueError("Save directory not found")
        else:
            pass

        ############
        
        #--> DRIVER SETUP
        service = Service(dir_chrome_webdriver)
        options = webdriver.ChromeOptions()
        # Chrome runs headless, 
        # comment out "options.add_argument('headless')"
        # to see the action
        # options.add_argument('headless')
        driver = webdriver.Chrome(service=service, options=options)
        
        ############
        
        #--> OPEN TO TVW ARCHIVES 
        driver.get("https://tvw.org/video-search/")
        time.sleep(5)
        
        ############
        
        #--> CLICK CATEGORIES TO OPEN 
        driver.find_element(By.CLASS_NAME, "MuiGrid-grid-xs-12").click()
        
        # INPUT COMMITTEE NAME
        input_search = driver.find_element(By.XPATH, "//input[contains(@class, 'MuiInputBase-input MuiInput-input')]")
        input_search.send_keys(param_committee)
        
        #TEST NOTE: Need to check that this specific div class is clickable for each committee selection
        committee_script_list =["//div[@class='MuiListItemText-root jss3 jss4 MuiListItemText-multiline'",
                                " and @title='",
                                param_committee,
                                "']"]
        separator = ""     
        committee_script = separator.join(committee_script_list)
        
        # SELECT COMMITTEE NAME FROM DROP DOWN
        driver.find_element(By.XPATH, committee_script).click()
        
        # CHECK THAT COMMITTEE NAME FROM DROP DOWN IS SELECTED
        committee_name_assert = driver.find_element(By.XPATH, "//span[@class='MuiChip-label']").get_attribute("innerHTML")
        
        #Ensure amp is the same
        if re.search("&amp;", committee_name_assert):
            committee_name_assert = committee_name_assert.replace("&amp;", "&")
        else:
            pass
            
        assert committee_name_assert == param_committee, "Committee Name Not Selected"

        ############
        
        #--> SELECT START DATE BY LEGISLATIVE SESSION (JANUARY 1-3, WHICHEVER FALLS ON WEEKDAY)
        # Date is reliant on current date, start month set to January 1st of cal year
        calendar_dropdown = driver.find_elements(By.XPATH, "//div[@class='react-datepicker__input-container']")        

        calendar_dropdown[0].click() 
        
        date_elements = driver.find_elements(By.XPATH, "//input[@class='css-13hc3dd']")
        start_date = date_elements[0].get_attribute("value")
        start_datetime = datetime.strptime(start_date, '%m/%d/%Y').date()
        
        previous_month_click = "//button[@class='react-datepicker__navigation react-datepicker__navigation--previous']"
       
        def _loop_january(driver, upper_range: int) -> ():
            if upper_range == 0:
                return
            for i in range(0, upper_range):
                driver.find_element(By.XPATH, previous_month_click).click()

        def _loop_first():
            try:
                driver.find_element(By.XPATH, "//div[@class='react-datepicker__day react-datepicker__day--001']").click() 
            except:
                try:
                    driver.find_element(By.XPATH, "//div[@class='react-datepicker__day react-datepicker__day--002']").click()
                except:
                    try:
                        driver.find_element(By.XPATH, "//div[@class='react-datepicker__day react-datepicker__day--003']").click()
                    except:
                        pass
     
        _loop_january(driver, start_datetime.month-1)
        _loop_first()
        
        if driver.find_element(By.XPATH, "//div[@class='react-datepicker__header']"):
            calendar_dropdown[0].click() 
        else:
            pass
        
        param_dates = driver.find_elements(By.XPATH, "//input[@class='css-13hc3dd']")
        param_start_date = param_dates[0].get_attribute("value")        
        param_start_datetime = datetime.strptime(param_start_date, '%m/%d/%Y').date()
        assert (param_start_datetime.month == 1), "Start Date not set to January"
        assert (param_start_datetime.day <=3), "Start Date not set between January 1-3"
        
        #--> SELECT START YEAR (ESTABLISHED BY PARAM_YEAR)
        
        #check if dropdown is down
        
        try:
            calendar_dropdown[0].click() 
        except:
            calendar_dropdown = driver.find_elements(By.XPATH, "//div[@class='react-datepicker__input-container']")   
            calendar_dropdown[0].click() 
        
        date_elements = driver.find_elements(By.XPATH, "//input[@class='css-13hc3dd']")
        year_date = date_elements[0].get_attribute("value")
        year_datetime = datetime.strptime(year_date, '%m/%d/%Y').date()   
        
        driver.find_element(By.XPATH, "//div[@class='react-datepicker__header']").click() 
        
        #Year dropdown is dynamic according to date, code clicks according to present values  
        #BUG: Needs to scroll to previous so year appears on the dropdown to click. Q: How to click on A CLASS
        year_list = driver.find_elements(By.XPATH, "//div[@class='react-datepicker__year-option']")
        year_list_values=[]
        
        for y in range(len(year_list)):
            year_list_values.append(year_list[y].get_attribute("innerHTML"))
        
        def _year_select(param_year):
            #Click according to the param_year
            if param_year == "2021":
                param_y = year_list_values.index("2021")
                year_list[param_y].click()
            elif param_year == "2020":
                param_y = year_list_values.index("2020")
                year_list[param_y].click()
            elif param_year == "2019":
                param_y = year_list_values.index("2019")
                year_list[param_y].click()
            elif param_year == "2018":
                param_y = year_list_values.index("2018")
                year_list[param_y].click()
            elif param_year == "2017":
                param_y = year_list_values.index("2017")
                year_list[param_y].click()
            elif param_year == "2016":
                param_y = year_list_values.index("2016")
                year_list[param_y].click()
            elif param_year == "2015":
                param_y = year_list_values.index("2015")
                year_list[param_y].click()
            else:
                "Invalid Year. Current coverage limited to 2015 to 2021"
                
        if (year_datetime.year != int(param_year)):
            _year_select(param_year)
            _loop_first()
        else:
            pass
        
        param_dates = driver.find_elements(By.XPATH, "//input[@class='css-13hc3dd']")
        param_start_date = param_dates[0].get_attribute("value")        
        param_start_datetime = datetime.strptime(param_start_date, '%m/%d/%Y').date()
        assert (param_start_datetime.year == int(param_year)), "Start Date not set to param_year"
        assert (param_start_datetime.day <=3), "Start Date not set between January 1-3"
        
        ############
        
        #--> SELECT END DATE BY LEGISLATIVE SESSION (DECEMBER)
        
        calendar_dropdown[1].click() 
        date_elements = driver.find_elements(By.XPATH, "//input[@class='css-13hc3dd']")
        end_date = date_elements[1].get_attribute("value")        
        end_datetime = datetime.strptime(end_date, '%m/%d/%Y').date()
        
        next_month_click = "//button[@class='react-datepicker__navigation react-datepicker__navigation--next']"
      
        def _loop_december(driver, upper_range: int) -> ():
            if upper_range == 12:
                 return
            for i in range(0, (12-upper_range)):
                driver.find_element(By.XPATH, next_month_click).click()
                
        def _loop_end():
            try:
                driver.find_element(By.XPATH, "//div[@class='react-datepicker__day react-datepicker__day--031']").click() 
            except:
                try:
                    driver.find_element(By.XPATH, "//div[@class='react-datepicker__day react-datepicker__day--030']").click()
                except:
                    try:
                        driver.find_element(By.XPATH, "//div[@class='react-datepicker__day react-datepicker__day--029']").click()
                    except:
                        pass
   
        _loop_december(driver, end_datetime.month)
        _loop_end()
        
        param_dates = driver.find_elements(By.XPATH, "//input[@class='css-13hc3dd']")
        param_end_date = param_dates[1].get_attribute("value")        
        param_end_datetime = datetime.strptime(param_end_date, '%m/%d/%Y').date()
        assert (param_end_datetime.month == int(12)), "End Date not set to December"
        assert (param_end_datetime.day >=29), "End Date not set between December 29-31"
            
        #--> SELECT END YEAR (ESTABLISHED BY PARAM_YEAR)
        
        calendar_dropdown[1].click() 

        date_elements = driver.find_elements(By.XPATH, "//input[@class='css-13hc3dd']")
        end_year_date = date_elements[1].get_attribute("value")
        end_year_datetime = datetime.strptime(year_date, '%m/%d/%Y').date()
        
        driver.find_element(By.XPATH, "//div[@class='react-datepicker__header']").click() 
       
        #Year dropdown is dynamic according to date, code clicks according to present values  
        year_list = driver.find_elements(By.XPATH, "//div[@class='react-datepicker__year-option']")
        
        year_list_values=[]
       
        for y in range(len(year_list)):
            year_list_values.append(year_list[y].get_attribute("innerHTML"))
        
        #Click previous until year appears on year_list
        #while not param_year in year_list:
        #    driver.find_element(By.XPATH, "//a[@class='react-datepicker__navigation react-datepicker__navigation--years react-datepicker__navigation--years-previous']").click()
        #    year_list = driver.find_elements(By.XPATH, "//div[@class='react-datepicker__year-option']")
        #    year_list_values=[]
        #    for y in range(len(year_list)):
        #        year_list_values.append(year_list[y].get_attribute("innerHTML"))
        
        if (end_year_datetime.year != int(param_year)):
             _year_select(param_year)
             _loop_end()
        else:
             calendar_dropdown[1].click()
        
        param_dates = driver.find_elements(By.XPATH, "//input[@class='css-13hc3dd']")
        param_end_date = param_dates[1].get_attribute("value")        
        param_end_datetime = datetime.strptime(param_end_date, '%m/%d/%Y').date()
        assert (param_end_datetime.year == int(param_year)), "End Date not set to param_year"
        assert (param_end_datetime.day >=29), "End Date not set between December 29-31"

        ############
             
        #--> PRESS SUBMIT 
        driver.find_element(By.XPATH, "//button[@class='filter__form-submit css-1l4j2co']").click()
         
        ############
         
        # SAVE HTML FOR MULTIPLE PAGES
 
        url_html = []
        
        url_html.append(driver.page_source) #CURRENT PAGE, PAGE 1
        
        #url_link = driver.find_element(By.XPATH, "//div[@class='pagination__Pagination-sc-gi8rtp-0 efVChy pagination']")
        #url_pages_innerhtml = url_link.get_attribute("innerHTML")
        url_page_numbers= driver.find_elements(By.XPATH, "//button[@class='pagination__Button-sc-gi8rtp-2 hFycqx pagination__button css-18u3ks8']")
        url_page_length = len(url_page_numbers)
        
        if url_page_length > 1:
            for page_num in range(url_page_length): #length + 1, since it doesn't include first page (currently loaded page)
                url_page_loop= driver.find_elements(By.XPATH, "//button[@class='pagination__Button-sc-gi8rtp-2 hFycqx pagination__button css-18u3ks8']")
                url_page_loop[page_num].click() 
                time.sleep(5)
                url_html.append(driver.page_source) 
                url_page_home= driver.find_elements(By.XPATH, "//button[@class='pagination__Button-sc-gi8rtp-2 hFycqx pagination__button css-18u3ks8']")
                url_page_home[0].click()
                time.sleep(5)
        else:
            pass
        
        assert len(url_html) > 0, "Check that there's content in the html list"
        
        driver.close()
        
        ####
        
        # FOR EACH PAGE SOURCE SEARCH FOR A HREF TAG ENDING IN .MP3 TO CREATE A LIST OF AUDIO LINKS, 
        
        soup_html = BeautifulSoup(url_html[0])

        div_table = soup_html.find_all('div', {'class': re.compile(r'table__Metadata-.*')})

        committee_links=[]
        committee_dates=[]
        
        for url_page in range(len(url_html)):
            soup_html = BeautifulSoup(url_html[url_page])
            div_table = soup_html.find_all('div', {'class': re.compile(r'table__Metadata-.*')})

    def wa_scrape_audio():
    
      """
        Webscrape function for Washington State Legislature Website for 2015-2020 sessions 
        
        Parameters
        ----------
        webscrape_links : LIST
            List of direct link(s) to WA committee video pages.
            Can also use list generated by wa_committee_links() 
        dir_chrome_webdriver : STRING
            Local directory that has Chrome Webdriver.
        dir_save : STRING
            Local directory to save audio files
    
        Returns
        -------
        All audio files found on the webscrape_links, either as an object or saved on local dir_save.
        
        """
        
        if download:
        
            folder_location = dir_save
            
            for link in mp3_files:
                filename = os.path.join(folder_location,"_".join(link.split('/')[4:]))
                urllib.request.urlretrieve(link, filename)
        
        return(mp3_files)

#### WORK IN PROGRESS

class Process:
    """
    """
    def wa_speech_to_text(weblinks_mp3):
        """
        Function gives the user option to convert audio file to a text transcript through DeepSpeech package

        Parameters
        ----------
        weblinks_mp3 : TYPE
            DESCRIPTION.

        Returns
        -------
        Downloads the transcript in json form, single json for each committee/legislative session

        """
    
#STEP 1: Convert mp3 file to wav, 1600 frame rate, mono channel
        
        from pydub import AudioSegment
        os.chdir("/Users/katherinechang/Downloads") #Location of the saved mp3
        audio_org = "071722fb938c8e0a87505936941971725631c303_audio.mp3"
        audio_wav = "wa_house_ed_2_20_21.wav"
        sound = AudioSegment.from_mp3(audio_org)
        sound.export(audio_wav, format="wav")
        new_sound = sound.set_frame_rate(16000).set_channels(1)
        
        ## ISSUE: Converting to wav ends up with a large file size. Do it one at a time and then delete? Save the MP3s all together
        
        #audio_org = "071722fb938c8e0a87505936941971725631c303_audio.mp3" #weblinks_mp3
        #audio_wav = "wa_house_ed_2_20_21.wav"
        
        #---QUESTION: Best practices of running command line as part of functions? 
        #---QUESTION: HOW TO CALL VARIABLES TO CLI
        #!ffmpeg -i audio_org  -ar 16000 -ac 1  audio_wav
        #!ffmpeg -i 071722fb938c8e0a87505936941971725631c303_audio.mp3  -ar 16000 -ac 1 wa_house_ed_2_20_21.wav

#STEP 2: Run DeepSpeech for each converted wav file and save transcript in new output folder
#Model and vad_transcriber saved in statelegiscraper/assets 
#Depending on length, can run 15+ minutes per audio file. Should we do it one by one?

        start = time.time()
        !python3 DeepSpeech/vad_transcriber/audioTranscript_cmd.py --aggressive 1 --audio wa_house_ed_2_20_21.wav --model ./
        #Make a list of wav files, bash command constructed as an object, each iteration of the loop just replace the argumement of the flag
        #with the current value of the loop

"""
flags={"--aggressive": 1", "--audio": "filename", "--model: "./"}
for f in filenames:
  flags["--audio"] = f
  self.ExecuteThis(command, flags)
  
"""
        
        end = time.time()
        print("Total time: {:.2f}".format(end-start))

#STEP 3: Check to make sure .txt is saved
        

    def wa_text_clean(transcript):
        """

        Parameters
        ----------
        transcript : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        

