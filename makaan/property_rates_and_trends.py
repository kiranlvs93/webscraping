import json

from requests_html import HTMLSession
import os, shutil, pathlib

session = HTMLSession()
base_url = "https://www.makaan.com/price-trends/property-rates-for-buy-in-bangalore?page={pgno}"
output_folder = r'C:\Users\k0l05t5\PycharmProjects\WebScraping\output'


def get_table_data(locality_id, page_num: 1):
    print("-----------------------------------------------------------------------------------")
    print(f"Fetching data on {locality_id}")
    print("Hitting URL::", base_url.format(pgno=page_num))
    table_data = []
    r = session.get(base_url.format(pgno=page_num))
    # Find all rows
    rows = r.html.find(f"#{locality_id} .tbl tr[itemtype='http://schema.org/Place']")

    # Find necessary tds for all rows
    for row in rows:
        try:
            row_data = dict()
            href = row.find("td[data-source='locality']>a", first=True).attrs['href']
            row_data['locality_link'] = href
            row_data['location'] = row.find("td[data-source='locality']>a>span", first=True).text
            row_data['location_code'] = row.find("td.link-td.ta-c[data-source='See Trends']", first=True).attrs['data-id']
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
            # print(row_data)
            table_data.append(row_data)
            # print("**********************************************************")
        except Exception as e:
            print(f"Error in {href}. Exception:{e}")
    print(f"LOCALITY_ID::{table_data}")
    return table_data


def clean_output_folder():
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    print("Output folder cleaned")


def get_no_of_pages():
    r = session.get(base_url.format(pgno=1))
    pages = r.html.find('.pagination li:nth-of-type(7)', first=True).text
    print(f"There are {pages} pages to be crawled")
    return int(pages)


if __name__ == '__main__':
    clean_output_folder()
    locality_type_ids = ['locality_apartment', 'locality_villa', 'locality_plot', 'locality_builderfloor']
    for locality in locality_type_ids:
        data = []
        for pgno in range(1, get_no_of_pages() + 1):
            data.extend(get_table_data(locality, pgno))
        op_file = output_folder + os.sep + locality.split('_')[1] + ".json"
        with open(op_file, "a+") as op_file:
            json.dump(data, op_file)
            print(f"Data for {locality} written into file {op_file.name}")
