import requests
import re
import jsonfinder
import json

file_locations = "links"
base = "https://www.datacentermap.com"
country = "spain"

with open(file_locations) as file:
    locations = file.read().splitlines()
    print("\nStarted parsing datacenter locations...")
    count = 0

    for location_url in locations:
        print("\nLocation:", location_url)
        print("DCs with Individual Servers:\n")
        before_count = count
        r_loc = requests.get(str(location_url))
        pre_datacenters = re.findall(r"class=\"ui card card1\" href=\"\/spain\/\S+\/", r_loc.text)
        for pre_dc in pre_datacenters:
            datacenters = re.findall(r"\/spain\/\S+\/", pre_dc)
            for dc in datacenters:
                dc = base + dc
                r_dc = requests.get(dc)
                if "Individual Servers" in r_dc.text:
                    visit_url = re.sub('/' + country + '\/[a-z,-]*', '/visit/datacenter', dc)
                    visit_url_get = requests.get(str(visit_url))
                    try:
                        visit_json = jsonfinder.only_json(visit_url_get.text)
                    except ValueError:
                        print('      More than 1 JSON: ' + str(visit_url))
                        break
                    full_json = json.loads(json.dumps(visit_json))
                    print('      ' + full_json[2]["props"]["pageProps"]["url"])
                    count += 1
        if count == before_count:
            print("      No DCs with Individual Servers")
    print("\n" + str(count), "datacenters found with Individual Servers feature")

# https://www.datacentermap.com/visit/datacenter/kheops-2/

# <a class="ui card card1" href="/brazil/
# <a class="ui card card1" href="/brazil/sao-paulo/rua-papa-joao-paulo-ii-4-building-2/">

# url = 'https://datacentermap.com/brazil/brasilia/'
# r = requests.get(url)
# pre_datacenters = re.findall(r"class=\"ui card card1\" href=\"\/brazil\/\S+\/", r.text)
# print()

# for dc in pre_datacenters:
#     datacenters = re.findall(r"\/brazil\/\S+\/", dc)   
#     print(datacenters)
#     for dc in datacenters:
#                 dc = base + dc
#                 print(dc)
                # r_dc = requests.get(dc)
                # print(r_dc)


# if "Individual Servers" in r.text:
#     print("Found!")
# else:
#     print("Not found!")