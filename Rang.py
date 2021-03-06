import math
import random
import html as html_lib
import requests
import webbrowser
import sys

from bs4 import BeautifulSoup


inf = float("inf")
real_range = (-1*inf,inf)


def in_range(range_tuple,value):
    if len(range_tuple) != 2 or range_tuple[0] > range_tuple[1]:
        raise ValueError("Invalid range tuple")
    return value >= range_tuple[0] and value <= range_tuple[1]


def get_random_latitude_and_longitude(degrees=False,lat_range=real_range,lon_range=real_range):
    lat,lon = None,None
    while lat is None or lon is None or (lat_range is not None and not in_range(lat_range,lat)) \
        or (lon_range is not None and not in_range(lon_range,lon)):
        lon = random.uniform(-1,1)*(180 if degrees else math.pi)
        cos_theta = random.uniform(-1,1)
        theta = (math.acos(cos_theta) - math.pi * 1.0/2)
        lat = theta * (90/(math.pi*1.0/2) if degrees else 1)

    return (lat,lon)


def get_populous_us_cities(n_cities):
    # current page, subject to breaking randomly
    # wikipedia_url = "https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population"

    # static revision, if I can get it to work for one of them
    wikipedia_url = "https://en.wikipedia.org/w/index.php?title=List_of_United_States_cities_by_population&oldid=854477638"
    print("using revision as of 2018-08-11")

    html = requests.get(wikipedia_url).text
    soup = BeautifulSoup(html, "html5lib")
    tables = soup.find_all("table", attrs={"class": "wikitable sortable"})
    table = tables[0]
    trs = table.find_all("tr")
    cities = []
    for tr in trs[1:]:
        tds = tr.find_all("td")
        city_td = tds[1]
        city = city_td.find("a").text.strip()
        state_td = tds[2]
        state = state_td.text.replace("\u00A0", "").strip()  # remove &nbsp;
        new_str = u"{}, {}".format(city, state)
        # print(new_str.encode("utf-8"))
        cities.append(new_str)

    assert all(x in cities for x in ["New York, New York", "Chicago, Illinois", "Memphis, Tennessee"]), cities
    return random.sample(cities, n_cities)


def open_location_in_google_maps(lat, lon):
    zoom_level = 6  # int, bigger is zoomed farther in
    url = "http://www.google.com/maps/place/{lat},{lon}/@{lat},{lon},{zoom_level}z".format(**locals())
    webbrowser.open(url)


def confirm(string):
    x = input(string + " (y/n, default = n)")
    return x.strip().lower() == "y"


if __name__ == "__main__":
    args = sys.argv

    try:
        open_in_browser = args[2] == "y"
    except IndexError:
        open_in_browser = None
    confirm_open = lambda: open_in_browser if open_in_browser is not None else confirm("open in browser?")

    try:
        mode = args[1]
    except IndexError:
        mode = input("Select mode:\n"
            "1. World\n"
            "2. Continental US (approx.)\n"
            "3. US cities over 100,000 people\n")
    if mode == "1":
        loc = get_random_latitude_and_longitude(degrees=True)
        print(loc)
        if confirm_open():
            open_location_in_google_maps(*loc)
    elif mode == "2":
        loc = get_random_latitude_and_longitude(degrees=True,lat_range=(24.5,49.5),lon_range=(-125,-66))
        print(loc)
        if confirm_open():
            open_location_in_google_maps(*loc)
    elif mode == "3":
        n_cities = int(input("How many cities? "))
        for city in get_populous_us_cities(n_cities):
            print(city)

# TODO: rang road trip, between cities and/or points


