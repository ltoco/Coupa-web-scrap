import csv
import re
import requests


from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin

def get_next_page_url(soup):  
    """
    This function would return a part of the url for the next page if it exists, 
    else None is returned.

    Args:
        soup: The Soup object that would be parsed to fetch the next
        page's url.

    Returns:
        partial_url: This partial_url if exists would be joined with base_url 
        to form complete ext age url.
    """

    l = soup.select_one("div[class='colorful'][style='float:left;']")
    a_tags = l.find_all('a')
    print(a_tags)
    partial_url = None
    for a_tag in a_tags:
        if 'Next Page' in a_tag.text:
            partial_url = a_tag['href']

    return partial_url


def combine_data(base_url, url):
    """
    This function would scrape the page that contains list of colleges and
    would combine the scraped data and appened it to a list.

    Args:
        url: The url to different pages of the webiste that contain list of colleges

    Returns:
        data: A list of dictionary that containes the scraped data
        partial_url: Partial url of the next page when combined with base_url will form
        the next page url.
    """

    data = []
    r = requests.get(url).text
    soup = bs(r, features='lxml')
    table_body = soup.find('table', class_="resultsTable")
    table_rows = table_body.select('tr[class*=results]')
    for i, table_row in enumerate(table_rows):
        td = table_row.find('td')
        college_url_partial = td.next_sibling.a['href']
        print(base_url+college_url_partial)
        data.append(get_college_data_next_page(base_url, college_url_partial))
        print(i+1)

    partial_url = get_next_page_url(soup)
    return data, partial_url

def get_college_data_next_page(base_url, college_url_partial):
    """
    This function would visit the college details page and would parse the required data
    returning a dictionary

    Args:
        college_url_partial: This college_partial_url will be joined with base_url to
        form the full url from which college details would be scrapped.

    Returns:
        college_dict: A dictionary containing college data.
    """
    college_url_full = base_url + college_url_partial
    r_text =  requests.get(college_url_full).text
    college_soup = bs(r_text, 'lxml')
    college_name = college_soup.select_one('span[style="position:relative"]>span.headerlg').text
    college_address = college_soup.select_one('span[style="position:relative"]').text
    college_address = college_address.replace(college_name, '')
    table = college_soup.find('table', {'class': 'layouttab'})

    # college_dict would store data for each record
    # this dict would be stored in a list
    college_dict = {}
    college_dict['Name'] = college_name
    # college_address = 4900 Meridian Street, Normal, Alabama 35762
    college_dict['Street'] = college_address.split(',')[0] # 4900 Meridian Street
    college_dict['City'] = college_address.split(',')[1] # Normal
    college_dict['State'] = college_address.split()[-2] # Alabama
    college_dict['Zip'] = college_address.split()[-1] # 35762
    
    tr = table.find('tr')

    college_dict['Phone'] = tr.find("td").next_sibling.text

    sibiling1 = tr.next_sibling
    college_dict['Website'] = sibiling1.find("td").next_sibling.text

    sibiling2 = sibiling1.next_sibling
    college_dict['Type'] = sibiling2.find("td").next_sibling.text

    sibiling3 = sibiling2.next_sibling
    awards_info = sibiling3.find("td").next_sibling.text
    college_dict['Awards'] =  re.sub(r"(\w)([A-Z])", r"\1, \2", awards_info)

    sibiling4 = sibiling3.next_sibling
    college_dict['Campus Setting'] = sibiling4.find("td").next_sibling.text

    sibiling5 = sibiling4.next_sibling
    college_dict['Campus Housing'] = sibiling5.find("td").next_sibling.text

    sibiling6 = sibiling5.next_sibling
    student_population = sibiling6.find("td").next_sibling
    college_dict['Student Population'] = student_population.text if student_population else None

    try:
        sibiling7 = sibiling6.next_sibling
        college_dict['Student to Faculty Ratio'] = sibiling7.find("td").next_sibling.text
    except:
        college_dict['Student to Faculty Ratio'] = None

    print(college_dict)

    return college_dict
    

def main():
    """
    This is the main function which would call the required functions and get the data scrapped

    Returns:
        entire_data: A list of dictionary which would contain the entire required data
    """
    base_url = 'https://nces.ed.gov/collegenavigator/'
    partial_url = '?s=all&sp=4&pg=1'

    entire_data = []
    count_of_records = 1
    while partial_url:
        print(count_of_records)
        count_of_records = count_of_records+1

        # Scrape data and return list of dict
        website_url = base_url + partial_url
        data, partial_url = combine_data(base_url, website_url)

        # combine data
        entire_data.extend(data)

    return entire_data
    
if __name__ == '__main__':
    data = main()
    print(f'Number of records: {len(data)}')

    # Writing to csv
    keys = data[0].keys()

    with open('college_data.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
