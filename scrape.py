import sys

import urllib
from urllib2 import urlopen
from urllib2 import HTTPError, URLError

from bs4 import BeautifulSoup
import datetime, time

def get_soup(link):
    try:
        html = urlopen(link)
    except HTTPError as e: # The page is not found on the server
        print("ERROR: Internal server error!", e)
        return None 
    except URLError as e:
        print("ERROR: The server could not be found!", e)
        return None 
    else:
        return BeautifulSoup(html.read(), "html.parser")

def scrape_hep(list_of_record_ids):
    ''' Scrape the HEP jobs market '''
    start_link = "https://inspirehep.net/search?ln=en&cc=Jobs&rg=0"
    soup = get_soup(start_link)
    if soup == None:
        print('ERROR: No soup object received')
        return 

    list_of_jobs = soup.findAll("div", {"class": "record_body"})
    print('N = ', len(list_of_jobs))
    records = []
    for job in list_of_jobs:
        job_info = {'posting_date': '', 'record_link': ''}
        strong_tag = job.find("strong")
        if strong_tag:
            job_info['posting_date'] = strong_tag.text
        else:
            print("WARNING: No posting date found?")

        a_tags = job.findAll("a")
        if a_tags[1]:
            job_info['institute'] = a_tags[1].text
            job_info['position'] = a_tags[1].findNext("span").text
        else:
            print("WARNING: No institute found?")

        if a_tags[0] and a_tags[0].attrs['href'].rsplit('/', 1)[0] == 'https://inspirehep.net/record':
            job_info['record_link'] = a_tags[0].attrs['href']
            job_info['record_id'] = a_tags[0].attrs['href'].rsplit('/', 1)[1]
            job_info['short_description'] = a_tags[0].text
            # Only further process records which are new (this way we miss all record updates!)
            if job_info['record_id'] not in list_of_record_ids:
                records.append(job_info)
        else:
            print("WARNING: No record link found?")
    print("len(records) = ", len(records))

    # Test different possible patterns for the application deadline field
    application_deadline_patterns = ['%Y-%m-%d', '%Y-%m-%d  (PASSED)']
    
    for i, record in enumerate(records):
        time.sleep(1)
        soup = get_soup(record['record_link'])
        if soup == None:
            print('ERROR: No soup object received for record %d' % i)
        else:
            record_details = soup.find("div", {"class": "detailed_record_info"})
            job_description_identifier = record_details.find("strong", text="Job description: ")
            description = job_description_identifier.parent
            if description:
                record['description'] = str(description).replace('<strong>Job description: </strong><br/>', '')
            else:
                print('WARNING: No description found')

            # Sometimes there are multiple names here... we only scarpe the first one
            contact_identifier = soup.find("strong", text="Contact: ")
            if contact_identifier:
                contact_atag = contact_identifier.findNext('a')
                record['contact_name'] = contact_atag.text
            else:
                record['contact_name'] = ''

            email_identifier = soup.find("strong", text="Email: ")
            if email_identifier:
                email_atag = email_identifier.findNext('a')
                record['contact_email'] = email_atag.text
            else:
                record['contact_email'] = ''

            url_identifier = soup.find("strong", text="More Information: ")
            if url_identifier:
                url_atag = url_identifier.findNext('a')
                record['related_url'] = url_atag.text
            else:
                record['related_url'] = ''

            fields_identifier = soup.find("strong", text="Field of Interest: ")
            if fields_identifier:
                record['fields'] = fields_identifier.next_sibling

            deadline_identifier = soup.find("strong", text="Deadline: ")
            if deadline_identifier:
                for pattern in application_deadline_patterns:
                    try:
                        application_deadline = datetime.datetime.strptime(deadline_identifier.next_sibling, pattern)
                        application_time = datetime.time(12, 0, 0);
                        record['deadline_date'] = datetime.datetime.combine(application_deadline, application_time)
                        break # accept first pattern match
                    except:
                        pass
            print("record['record_id'] = ", record['record_id'])
    return records
