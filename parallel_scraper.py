import multiprocessing
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

import time
import numpy as np
import pandas as pd
import sys

def scrape_linkedin(job_query, len_jobs):
    start = time.time()
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver = webdriver.Chrome()
    url = f"https://ph.linkedin.com/jobs/{job_query}-jobs"

    try:
        driver.get(url)
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        job_list = driver.find_elements(By.XPATH, "//ul[@class='jobs-search__results-list']/li")
        
        if len(job_list) == 0:
            print("No jobs found for this query in Linkedin.")

            empty_df = pd.DataFrame(columns=[
                'title', 'link', 'location', 'company', 'emp_type', 'job_func', 'job_desc', 'posted'
            ])
            empty_df.to_csv('linkedin.csv', index=False)

            driver.quit()
            return 

        # job catalog scraping
        jobs_scraped = np.array([])
        for job in job_list:
            descs = []
            try:
                job_title = job.find_element(By.XPATH, ".//h3[@class='base-search-card__title']").get_attribute('innerHTML').strip()
                card = job.find_element(By.XPATH, ".//a[@data-tracking-control-name='public_jobs_jserp-result_search-card']")
                link = card.get_attribute('href')
                descs = [job_title, link]
            except:
                continue
        
            try:
                location = job.find_element(By.XPATH, ".//span[@class='job-search-card__location']").get_attribute('innerHTML')
                location = location.replace('\n', '').strip()
                descs.append(location)
            except:
                descs.append('')
            
            try: 
                company = job.find_element(By.XPATH, ".//h4[@class='base-search-card__subtitle']/a").get_attribute('innerHTML').strip()
                descs.append(company)
            except:
                try:
                    company = job.find_element(By.XPATH, ".//h4[@class='base-search-card__subtitle']").get_attribute('innerHTML').strip()
                    descs.append(company)
                except:
                    descs.append('')
                    
            if len(jobs_scraped) == 0:
                jobs_scraped = np.append(jobs_scraped, descs)
            else:
                jobs_scraped = np.vstack([jobs_scraped, descs])

            # limit to max len_jobs only
            if len(jobs_scraped) >= len_jobs:
                break
        
        # if there is only 1 scraped job
        if jobs_scraped.shape == (4,):
            jobs_scraped = np.array([list(jobs_scraped)])
            
        # individual job scraping
        job_descs = np.array([])
        for job in jobs_scraped:
            descs = []
            try:
                # scraping emp_type, job_func, job_desc, posted ago
                driver.get(job[1])
                wait = WebDriverWait(driver, timeout=2)
                desc_job = wait.until(EC.presence_of_all_elements_located((By.XPATH, ".//ul[@class='description__job-criteria-list']/li")))
                descs = [job[1]]
                for i in [1,2]:
                    try:
                        detail = desc_job[i].find_element(By.XPATH, ".//span")
                        detail = detail.get_attribute('innerHTML').replace('\n', '').strip()
                        descs.append(detail)
                    except:
                        descs.append('')
                try:
                    desc_gen = driver.find_element(By.XPATH, "//div[@class='description__text description__text--rich']/section/div")
                    desc_gen = desc_gen.get_attribute('innerHTML')
                    descs.append(desc_gen)
                except:
                    descs.append('')
                try:
                    posted_ago = driver.find_element(By.XPATH, "//span[@class='posted-time-ago__text topcard__flavor--metadata']")
                    posted_ago = posted_ago.get_attribute('innerHTML').replace('\n','').strip()
                    descs.append(posted_ago)
                except:
                    descs.append('')
            except: 
                descs = [job[3],'','','','']
            if len(job_descs) == 0:
                job_descs = np.append(job_descs, descs)
            else:
                job_descs = np.vstack([job_descs, descs])
            time.sleep(2)
        
        # merging
        jobs_df = pd.DataFrame(jobs_scraped)
        jobs_df.columns = ['title','link', 'location', 'company']
        job_descs_df = pd.DataFrame(job_descs)
        
        # if there is only 1 scraped job
        if job_descs_df.shape == (5,1):
            job_descs_df = job_descs_df.T
        
        job_descs_df.columns = ['link','emp_type', 'job_func', 'job_desc', 'posted']
        linkedin_df = jobs_df.merge(job_descs_df, on='link', how='left')
        linkedin_df.to_csv(f'linkedin.csv')
    except:
        print("Unable to Scrape Linkedin")
    finally:
        # close driver
        try:
            driver.quit()
        except:
            print("Unable to Scrape Linkedin")
        
    end = time.time()
    print("Linkedin Scraping Time", end-start)

def scrape_foundit(job_query, len_jobs):
    start = time.time()
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver = webdriver.Chrome()
    url = f"https://www.foundit.com.ph/search/{job_query}-jobs"

    try:
        jobs_scraped = np.array([])
        page_num = 1
        while True:
            #driver.get(f"{url}{f"-{page_num}" if page_num > 1 else ''}")
            driver.get(f"{url}{'-' + str(page_num) if page_num > 1 else ''}")

            job_list = driver.find_elements(By.XPATH, "//div[@class='srpResultCard']/div")
            
            if len(job_list) <= 1:
                print("No jobs found for this query on Foundit.")

                # Save an empty DataFrame with the correct columns
                empty_df = pd.DataFrame(columns=[
                    'title', 'company', 'link', 'location', 'posted',
                    'emp_type', 'job_func', 'job_desc'
                ])
                empty_df.to_csv('foundit.csv', index=False)

                driver.quit()
                return 


            job_list = job_list[1:] # remove the header
            for job in job_list:
                # scraping title, company, url
                try:
                    job_title = job.find_element(By.XPATH, ".//a[@title]")
                    link = job_title.get_attribute('href')
                    job_title = job_title.get_attribute('innerHTML').replace('\n', '').strip()
                except:
                    continue
                try:
                    company = job.find_element(By.XPATH, ".//div[@class='companyName']/span")
                    company = company.get_attribute('innerHTML').replace('\n', '').strip()
                except: 
                    company = ''
                descs = [job_title, company, link]
            
                # scraping location, posted ago
                job.find_element(By.XPATH, './/div[@onclick]/div').click()
                wait = WebDriverWait(driver, 5)
                try:
                    desc_job = wait.until(EC.presence_of_all_elements_located((By.XPATH, ".//div[@id='jobHighlight']/div/div/div")))
                    for i in [0,2]:
                        if i != 2:
                            detail = desc_job[i].find_element(By.XPATH, ".//div[@class='details']")
                            detail = detail.get_attribute('innerHTML').replace('\n', '').strip()
                        else: 
                            detail = desc_job[i].find_element(By.XPATH, ".//span[@class='btnHighighlights']")
                            detail = detail.get_attribute('innerHTML').replace('\n', '').split('</i>')
                            detail = detail[1].strip()
                        descs.append(detail)
                except:
                    descs.append('','','')
            
                # scraping emp_type, job function, general job_desc
                try:
                    desc_job_2 = wait.until(EC.visibility_of_all_elements_located((By.XPATH, ".//div[@id='jobDetail']/div/div")))
                    for i in [0,2]:
                        try:
                            detail = desc_job_2[i].find_element(By.XPATH, ".//div[@class='jobDesc']")
                            detail = detail.get_attribute('innerHTML').replace('\n', '').strip()
                            descs.append(detail)
                        except:
                            descs.append('')
                except:
                    descs.extend(['',''])
                try:
                    desc_gen = wait.until(EC.visibility_of_element_located((By.XPATH, ".//p[@class='jobDescInfo']")))
                    desc_gen = desc_gen.get_attribute('innerHTML')
                    descs.append(desc_gen)
                except:
                    descs.append('')
                    
                if len(jobs_scraped) == 0:
                    jobs_scraped = np.append(jobs_scraped, descs)
                else:
                    jobs_scraped = np.vstack([jobs_scraped, descs])

            # limit to max len_jobs only
            if len(jobs_scraped) >= len_jobs:
                break
            page_num += 1

        # converting to DataFrame
        if jobs_scraped.shape == (8,):
            jobs_scraped = np.array([list(jobs_scraped)])
        
        foundit_df = pd.DataFrame(jobs_scraped)
        foundit_df.columns = ['title','company','link','location','posted','emp_type','job_func','job_desc']
        foundit_df.to_csv(f'foundit.csv')
    except:
        print("Unable to Scrape Foundit")
    finally:
        # close driver
        try:
            driver.quit()
        except:
            print("Unable to Scrape Foundit")
        
    end = time.time()
    print("Foundit Scraping Time", end-start)

def scrape_jobstreet(job_query, len_jobs):
    start = time.time()
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver = webdriver.Chrome()
    url = f"https://ph.jobstreet.com/{job_query}-jobs"

    try:
        driver.get(url)
        
        # job catalog scraping
        jobs_scraped = np.array([])
        wait = WebDriverWait(driver, 5)
        while True:
            try:
                job_list = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//article[@data-automation='normalJob']")))

                if len(job_list) == 0:
                    print("No jobs found for this query on JobStreet.")

                    empty_df = pd.DataFrame(columns=[
                        'title', 'link', 'company', 'posted',
                        'location', 'job_func', 'emp_type', 'job_desc'
                    ])
                    empty_df.to_csv('jobstreet.csv', index=False)

                    driver.quit()
                    return  

                for job in job_list:
                    descs = []
                    # scraping title, company, link
                    try:
                        job_title = job.find_element(By.XPATH, ".//a[@data-automation='jobTitle']")
                        link = job_title.get_attribute('href')
                        job_title = job_title.get_attribute('innerHTML').replace('\n','').strip()
                        company = job.find_element(By.XPATH, ".//a[@data-type='company']")
                        company = company.get_attribute('innerHTML').replace('\n', '').strip()
                        descs.append(job_title)
                        descs.append(link)
                        descs.append(company)
                    except:
                        continue

                    try:
                        posted_ago = job.find_element(By.XPATH, ".//span[@data-automation='jobListingDate']")
                        posted_ago = posted_ago.get_attribute('innerHTML').replace('\n','').strip()
                        descs.append(posted_ago)
                    except:
                        descs.append('')
                    
                    if len(jobs_scraped) == 0:
                        jobs_scraped = np.append(jobs_scraped, descs)
                    else:
                        jobs_scraped = np.vstack([jobs_scraped, descs])
                        
                # limit to max len_jobs only
                if len(jobs_scraped) >= len_jobs:
                    jobs_scraped = jobs_scraped[:len_jobs]
                    break
                    
                next_button = driver.find_element(By.XPATH, ".//a[@aria-label='Next']")
                next_button.click()
            except:
                break
        
        if jobs_scraped.shape == (4,):
            jobs_scraped = np.array([list(jobs_scraped)])
        
        # individual job scraping
        job_descs = np.array([])
        for job in jobs_scraped:
            try:
                driver.get(job[1])
                descs = [job[1]]
                try:
                    location = driver.find_element(By.XPATH, "//span[@data-automation='job-detail-location']/a")
                    location = location.get_attribute('innerHTML').replace('\n','').strip()
                    descs.append(location)
                except:
                    descs.append('')
                try:
                    job_func = driver.find_element(By.XPATH, "//span[@data-automation='job-detail-classifications']/a")
                    job_func = job_func.get_attribute('innerHTML').replace('\n','').strip()
                    descs.append(job_func)
                except:
                    descs.append('')
                try:
                    emp_type = driver.find_element(By.XPATH, "//span[@data-automation='job-detail-work-type']/a")
                    emp_type = emp_type.get_attribute('innerHTML').replace('\n','').strip()
                    descs.append(emp_type)
                except:
                    descs.append('')
                try:
                    job_desc = driver.find_element(By.XPATH, "//div[@data-automation='jobAdDetails']/div")
                    job_desc = job_desc.get_attribute('innerHTML').replace('\n','').strip()
                    descs.append(job_desc)
                except:
                    descs.append('')
            except:
                descs = [job[2], '', '', '', '']
            if len(job_descs) == 0:
                job_descs = np.append(job_descs, descs)
            else:
                job_descs = np.vstack([job_descs, descs])
        
        # merging
        jobs_df = pd.DataFrame(jobs_scraped)
        jobs_df.columns = ['title', 'link', 'company', 'posted']
        job_descs_df = pd.DataFrame(job_descs)
        
        # if there is only 1 scraped job
        if job_descs_df.shape == (5,1):
            job_descs_df = job_descs_df.T
        
        job_descs_df.columns = ['link', 'location', 'job_func', 'emp_type', 'job_desc']
        jobstreet_df = jobs_df.merge(job_descs_df, on='link', how='left')
        jobstreet_df.to_csv(f'jobstreet.csv')
    except:
        print("Unable to Scrape Jobstreet")
    finally:
        # close the driver
        try:
            driver.quit()
        except:
            print("Unable to Scrape Jobstreet")
    end = time.time()
    print("Jobstreet Scraping Time", end-start)

def scrape_kalibrr(job_query, len_jobs):
    start = time.time()
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver = webdriver.Chrome()
    url = f"https://www.kalibrr.com/home/te/{job_query}"

    try:
        driver.get(url)
        job_list = []
        # load job list 
        while len(job_list) < len_jobs:
            # click button to load more jobs until job_list > len_jobs
            try:
                # Re-evaluate job_list after each load
                wait = WebDriverWait(driver, 5)
                job_list = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='k-font-dm-sans k-rounded-lg k-bg-white k-border-solid k-border hover:k-border-2 hover:k-border-primary-color k-border k-group k-flex k-flex-col k-justify-between css-1otdiuc']")))
                
                load_more = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@class='k-btn-primary']")))
                load_more.click()
            except:
                break

        # If no jobs loaded at all
        if len(job_list) == 0:
            print("No jobs found for this query on Kalibrr.")

            # Save empty DataFrame with column headers
            empty_df = pd.DataFrame(columns=[
                'title', 'link', 'company', 'emp_type', 'location',
                'job_func', 'posted', 'job_desc'
            ])
            empty_df.to_csv('kalibrr.csv', index=False)

            driver.quit()
            return  

        
        job_list[:len_jobs]
        
        # job catalog scraping
        jobs_scraped = np.array([])
        i = 0
        for job in job_list:
            i += 1
            descs = []
            # scraping job title, company, emp_type, location
            try:
                job_title = job.find_element(By.XPATH, ".//h2[@data-tooltip-id='job-title-tooltip-[object Object]']/a")
                url = job_title.get_attribute('href')
                job_title = job_title.get_attribute('innerHTML').replace('\n', '').strip()
                descs.append(job_title)
                descs.append(url)
            except:
                continue
        
            try:
                company = job.find_element(By.XPATH, ".//span[@class='k-inline-flex k-items-center k-mb-1']/a")
                company = company.text.replace('\n', '').strip()
                descs.append(company)
            except:
                descs.append('')
                
            try:
                emp_type = job.find_element(By.XPATH, "./div[@class='k-relative']/div/span/span[@class='k-text-gray-500']")
                emp_type = emp_type.get_attribute('innerHTML').replace('\n', '').strip()
                descs.append(emp_type)
            except:
                descs.append('')
        
            try:
                location = job.find_element(By.XPATH, "./div[@class='k-relative']/div/span/span[@class='k-text-gray-500 k-block k-pointer-events-none']")
                location = location.get_attribute('innerHTML').replace('\n', '').strip()
                descs.append(location)
            except:
                descs.append('')
                
            if len(jobs_scraped) == 0:
                jobs_scraped = np.append(jobs_scraped, descs)
            else:
                jobs_scraped = np.vstack([jobs_scraped, descs])

            # limit to len_jobs only
            if len(jobs_scraped) >= len_jobs:
                break
        
        if jobs_scraped.shape == (5,):
            jobs_scraped = np.array([list(jobs_scraped)])
        
        # individual job scraping
        job_descs = np.array([])
        for job in jobs_scraped:
            descs = [job[1]]
            try:
                driver.get(job[1])
                # scrape job_func, posted
                try:
                    wait = WebDriverWait(driver, timeout=2)
                    job_func = wait.until(EC.presence_of_element_located((By.XPATH, ".//div[@class='md:k-flex']//dt[contains(text(),'Job Category')]/following-sibling::dd/a")))
                    job_func = job_func.get_attribute('innerHTML').replace('\n', '').strip()
                    descs.append(job_func)
                except:
                    descs.append('')
                try:
                    posted = driver.find_element(By.XPATH, ".//div[@class='k-text-subdued k-text-caption md:k-text-right md:k-absolute md:k-right-0 md:k-top-0 md:k-p-4']/p")
                    posted = posted.get_attribute('innerHTML').replace('\n', '').strip()
                    descs.append(posted)
                except:
                    descs.append('')
                # scrape desc
                job_desc = ''
                try:
                    job_desc = driver.find_element(By.XPATH, ".//div[@itemprop='description']")
                    job_desc = job_desc.get_attribute('innerHTML')
                    job_desc += job_desc
                except:
                    job_desc = job_desc
                try:
                    job_qual = driver.find_element(By.XPATH, ".//div[@itemprop='qualifications']")
                    job_qual = job_qual.get_attribute('innerHTML')
                    job_desc += job_qual
                except:
                    job_desc = job_desc
                try:
                    job_benef = driver.find_element(By.XPATH, ".//div[@itemprop='jobBenefits']")
                    job_benef = job_benef.get_attribute('innerHTML').replace('\n', '').strip()
                    job_desc += job_qual
                except:
                    job_desc = job_desc
                try:
                    job_skills = driver.find_element(By.XPATH, ".//ul")
                    job_skills = job_skills.get_attribute('innerHTML')
                    job_desc += job_skills
                except:
                    job_desc = job_desc
            
                descs.append(job_desc)
            
                if len(job_descs) == 0:
                    job_descs = np.append(job_descs, descs)
                else:
                    job_descs = np.vstack([job_descs, descs])
            except:
                continue
        
        jobs_df = pd.DataFrame(jobs_scraped)
        jobs_df.columns = ['title', 'link' ,'company', 'emp_type', 'location']
        
        job_descs_df = pd.DataFrame(job_descs)
        
        if job_descs_df.shape == (3, 1):
            job_descs_df = job_descs_df.T
        job_descs_df.columns = ['link', 'job_func', 'posted', 'job_desc']
        kalibrr_df = jobs_df.merge(job_descs_df, on='link', how='left')
        kalibrr_df.to_csv('kalibrr.csv')
    except:
        print("Unable to Scrape Kalibrr")
    finally:
        # close driver
        try:
            driver.quit()
        except:
            print("Unable to Scrape Kalibrr")

    end = time.time()
    print("Kalibrr Scraping Time", end-start)

if __name__ == '__main__':
    try:
        job_query = sys.argv[1]
        len_jobs = int(sys.argv[2])
        linkedin_p = multiprocessing.Process(target=scrape_linkedin, args=(job_query, len_jobs)) 
        foundit_p = multiprocessing.Process(target=scrape_foundit, args=(job_query, len_jobs))
        jobstreet_p = multiprocessing.Process(target=scrape_jobstreet, args=(job_query, len_jobs))
        kalibrr_p = multiprocessing.Process(target=scrape_kalibrr, args=(job_query, len_jobs))
        
        linkedin_p.start()
        foundit_p.start()
        jobstreet_p.start()
        kalibrr_p.start()

        linkedin_p.join()
        foundit_p.join()
        jobstreet_p.join()
        kalibrr_p.join()
    except:
        print("Invalid Arguments: Format must be 'job_query len_jobs'")