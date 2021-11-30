import json
import logging
from requests_html import HTMLSession
import os, shutil

logging.basicConfig(filename='app.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
session = HTMLSession()
base_url = "https://www.makaan.com"
price_trends = "/price-trends/property-rates-for-buy-in-bangalore?page={pgno}"


def get_table_data(locality_id, page_num=1):
    """
    Pass
    :param locality_id: type of locality id i.e. apartment, villa, plot, builder_floor
    :param page_num: page number where data is found
    :return:
    """
    logging.info("-----------------------------------------------------------------------------------")
    logging.info(f"Fetching data on {locality_id}")
    logging.info("Hitting URL::", base_url + price_trends.format(pgno=page_num))
    table_data = []
    r = session.get(base_url + price_trends.format(pgno=page_num))
    # Find all rows
    rows = r.html.find(f"#{locality_id} .tbl tr[itemtype='http://schema.org/Place']")

    # Find necessary tds for all rows
    for row in rows:
        try:
            row_data = dict()
            href = row.find("td[data-source='locality']>a", first=True).attrs['href']
            row_data['locality_link'] = href
            row_data['location'] = row.find("td[data-source='locality']>a>span", first=True).text
            row_data['location_code'] = row.find("td.link-td.ta-c[data-source='See Trends']", first=True).attrs[
                'data-id']
            min_price = row.find("td.ta-r>span[itemprop='minPrice']", first=True)
            max_price = row.find("td.ta-r>span[itemprop='maxPrice']", first=True)
            avg_price = row.find("td.ta-r:nth-child(3)", first=True)
            growth_percent = row.find("td:nth-child(4)", first=True)
            view_ppt = row.find("td[data-source='View Properties']:not(.disabled)", first=True)

            row_data['min_price'] = min_price.text if min_price is not None else "NA"
            row_data['max_price'] = max_price.text[:-7] if max_price is not None else "NA"
            row_data['avg_price'] = avg_price.text[:-7] if avg_price is not None and avg_price.text != '-' else "NA"
            row_data['growth'] = growth_percent.text[:-1] if growth_percent is not None else "NA"
            row_data['view_ppt_link'] = view_ppt.attrs['data-url'] if view_ppt is not None else "NA"
            row_data['no_of_properties'] = view_ppt.text.split()[1] if view_ppt is not None else "NA"
            # logging.info(row_data)
            table_data.append(row_data)
            # logging.info("**********************************************************")
        except Exception as e:
            logging.error(f"Error in {href}. Exception:{e}")
    logging.info(f"LOCALITY_ID::{table_data}")
    return table_data


def get_property_rows(location, property_url, page_num=1):
    """
    Function to get the details of the properties from each locality
    :param location:
    :param property_url:
    :param page_num:
    :return:
    """
    logging.info("-----------------------------------------------------------------------------------")
    logging.info(f"Fetching data for location {location} in page {page_num}")
    url = base_url + property_url + "&page={pgno}".format(pgno=page_num)
    logging.info("Hitting URL::", url)
    table_data = []
    r = session.get(url)
    # Find all rows
    rows = r.html.find("li.cardholder")

    # Find necessary tds for all rows
    for i, row in enumerate(rows):
        try:
            row_data = dict()
            script = row.find("div>script", first=True)
            row_data.update(json.loads(script.text))
            # Get other details like facing, # of bathrooms,
            for list_det in row.find("div[data-type=listing-card] .listing-details>li"):
                row_data.update(
                    {
                        (list_det.attrs.get('title').lower() if list_det.attrs.get(
                            'title') else "new_resale"): list_det.text
                    }
                )
            proj_details = row.find("div[data-type=listing-card] .projName", first=True)

            row_data['proj_name'] = proj_details.text if proj_details is not None else "NA"
            row_data['proj_href'] = proj_details.attrs['href'] if proj_details and proj_details.attrs.get(
                'href') else "NA"
            table_data.append(row_data)
            # logging.info("**********************************************************")
        except Exception as e:
            logging.error(f"Error in {url} \nRow {i + 1}:{row_data['companyName']}. Exception:{e}\n")
    logging.info(f"LOCALITY_ID::{table_data}")
    return table_data


def clean_folder(folder_path):
    """
    Delete files in the folder before creating new files
    :param folder_path:
    :return:
    """
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logging.error('Failed to delete %s. Reason: %s' % (file_path, e))
    logging.info("Output folder cleaned")


def get_no_of_pages(url):
    """
    Get number of pages in the website for crawling all the pages
    :param url:
    :return:
    """
    r = session.get(url.format(pgno=1))
    pages_ele = r.html.find(".pagination li")
    pages = pages_ele[len(pages_ele) - 2].text
    logging.info(f"There are {pages} pages to be crawled")
    return int(pages)


def get_locality_details():
    output_folder = r'C:\Users\k0l05t5\PycharmProjects\WebScraping\output\locality'
    clean_folder(output_folder)
    locality_type_ids = ['locality_apartment', 'locality_villa', 'locality_plot', 'locality_builderfloor']
    for locality in locality_type_ids:
        data = []
        for pgno in range(1, get_no_of_pages(base_url + price_trends) + 1):
            data.extend(get_table_data(locality, pgno))
        op_file = output_folder + os.sep + locality.split('_')[1] + ".json"
        with open(op_file, "a+") as op_file:
            json.dump(data, op_file)
            logging.info(f"Data for {locality} written into file {op_file.name}")


def check_fetched_records_match(expected, actual):
    """
    Check if all the records are fetched
    :param expected:
    :param actual:
    :return:
    """
    logging.info(f"Expected:{expected} | Fetched records:{actual}")
    if (diff := expected - actual) > 0:
        logging.info(f"{diff} records missing")
    elif (diff := actual - expected) > 0:
        logging.info(f"{diff} more records found")
    else:
        logging.info("All records are fetched")


def get_property_details():
    output_folder = r'C:\Users\k0l05t5\PycharmProjects\WebScraping\output\property_details'
    locality_details_folder = r"C:\Users\k0l05t5\PycharmProjects\WebScraping\output\locality"
    clean_folder(output_folder)

    # ppt_type_ids = ['apartment', 'villa', 'residential_plot', 'independent_floor']
    # for ppt_type in ppt_type_ids:

    # Read locality data
    with open(locality_details_folder + os.sep + "apartment.json") as inp_file:
        locality_details_json = json.load(inp_file)
    for locality in locality_details_json:
        data = []
        page_number = get_no_of_pages(base_url + locality['view_ppt_link'] + "&page={pgno}")
        for pgno in range(1, page_number + 1):
            data.extend(get_property_rows(locality['location'], locality['view_ppt_link'], pgno))
        check_fetched_records_match(int(locality['no_of_properties']), len(data))
        op_file_name = locality['view_ppt_link'][locality['view_ppt_link'].rfind("=") + 1:] + "_" + locality[
            "location"] + ".json"
        logging.info(data, file=open(output_folder + os.sep + op_file_name, "w+"))
        logging.info(f"Data for {locality['location']} written into file {op_file_name}\n")
        logging.info("*****************************************************************************")


if __name__ == '__main__':
    # get_locality_details()
    get_property_details()
