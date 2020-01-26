from selenium import webdriver
import sys, traceback
import requests
import selenium.webdriver.support.ui as ui
from time import sleep
from utils import check_exists_by_xpath
from utils import sort_and_remove_duplicates_from_list

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities as dc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import DesiredCapabilities
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from datetime import datetime
import random
from time import time
from lxml import etree
from dotenv import load_dotenv
load_dotenv()

import pyautogui
from fake_useragent import UserAgent

from utils import generate_random_proxy
from utils import filter_proxies
import os
import json

cwd = os.getcwd()
files = os.listdir(cwd)
sleep_increment = 3.5
website = os.getenv("WEBSITE")

# get random proxy
proxy_address = generate_random_proxy('{}/assests/proxy_list.txt'.format(cwd))
def fetch_with_random_proxy(endpoint):
    session = requests.Session()
    session.headers = {'User-agent': 'Mozilla/5.0'}
    proxy = generate_random_proxy("./assets/filtered_uk_proxies.txt")
    print("using {}".format(proxy))
    session.proxies = {
        'http' : 'http://{}'.format(proxy),
        }
    response = session.get(endpoint, stream = True)
    return response

def setup_firefox_driver(mode):
    options = Options()

    if mode == "headless":
        options.headless = True

    profile = webdriver.FirefoxProfile()
    profile.set_preference("network.proxy.type", 1)
    profile.set_preference("network.proxy.http", "{}".format(generate_random_proxy('{}/assets/filtered_uk_proxies.txt'.format(cwd))))
    profile.set_preference("network.proxy.http_port", 80)
    profile.update_preferences() 

    driver = webdriver.Firefox(options = options, executable_path="{}/assets/geckodriver".format(cwd))
    driver.set_window_size(1080, 1920)
    caps = dc().FIREFOX
    caps["marionette"] = False
    return driver

def setup_chrome_webdriver(mode):
    options = webdriver.ChromeOptions()
    options.add_argument('--proxy-server={}'.format(proxy_address))

    if mode == "headless":
        options.add_argument('headless')

    return webdriver.Chrome('soccer_scrape/assets/chromedriver_73', options=options)

# for help with the dropdowns
# go through this again, pay attention to notes in csv
table_1_headers = "match_id, league, league_id, home_team, away_team, home_team_id, away_team_id, date, location, venue, attendance, referee, home_goal, home_ball_possession, home_total_shots, home_shots_on_target, home_blocked_shots, home_corner_kicks, home_offsides, home_fouls, home_yellow_cards, home_big_chances, home_big_chances_missed, home_hit_woodwork, home_shots_inside_box, home_shots_outside_box, home_goalkeeper_saves, home_passes, home_accurate_passes, home_long_balls, home_crosses, home_dribbles, home_dispossessed, home_duels_won, home_arials_won, home_tackles, home_interceptions, home_clearances, home_player_1_id, home_player_2_id, home_player_3_id, home_player_4_id, home_player_5_id, home_player_6_id, home_player_7_id, home_player_8_id, home_player_9_id, home_player_10_id, home_player_11_id, home_formation, home_captain_id, home_manager_name, home_manager_id, home_sub_1_id, home_sub_2_id, home_sub_3_id, odds_who_will_win_1, odds_who_will_win_x, odds_who_will_win_2, odds_full_time_1, odds_full_time_x, odds_full_time_2, odds_double_chance1, odds_double_chance_x, odds_double_chance_2, odds_first_half, odds_1st_half_x, odds_first_half_2, odds_draw_no_bet_1, odds_draw_no_bet_2, odds_both_team_score_yes, odds_1st_team_score_1, odds_1st_team_score_2, odds_asian_handicap_1, odds_asian_handicap_2,odds_over_15, odds_under_15, odds_over_25, odds_under_25, odds_over_35, odds_under_35, odds_over_45, odds_under_45, odds_over_55, odds_under_55, odds_over_65, odds_under_65, odds_over_75, odds_under_75"
def return_identifier(stats_json):
  parsed = json.loads(stats_json)
  event_data = parsed["players"][0]["eventData"]
  match_id = event_data["id"]
  slug = "_".join(event_data["slug"].split("-"))
  identifier = "{}_{}".format(slug, match_id)
  return identifier

def fetch_endpoints(event_id):
    odds_endpoint = "https://api.{}/api/v1/event/{}/odds/1/all?_={}" # format with event id and 9 digit timestamp eg "157028500"
    general_endpoint = "https://www.{}/event/{}/general/json?_={}" # format with event id and 9 digit timestamp
    standings_endpoint = "https://www.{}/tournament/1/23776/standings/tables/json?_={}" # format with league id?
    matches_endpoint = "https://www.{}/event/{}/matches/json?_={}" # format with event id and 9 digit timestamp
    line_ups_endpoint = "https://www.{}/event/{}/lineups/json?_={}" # format with event id and 9 digit timestamp
    statistics_endpoint = "https://www.{}/event/{}/statistics/players/json?_={}" # format with event id and 9 digit timestamp

    end_points = [odds_endpoint, general_endpoint, matches_endpoint, line_ups_endpoint, statistics_endpoint]
    endpoint_strings = ["odds", "general", "matches", "line_ups", "statisitcs"]
    
    i = 0

    timestamp_short = str(int(time()))[0:-1]
    
    odds = fetch_with_random_proxy(odds_endpoint.format(website, event_id, timestamp_short))
    general = fetch_with_random_proxy(general_endpoint.format(website, event_id, timestamp_short))
    standings = fetch_with_random_proxy(standings_endpoint.format(website, event_id, timestamp_short))
    matches = fetch_with_random_proxy(matches_endpoint.format(website, event_id, timestamp_short))
    line_ups = fetch_with_random_proxy(line_ups_endpoint.format(website, event_id, timestamp_short))
    statistics = fetch_with_random_proxy(statistics_endpoint.format(website, event_id, timestamp_short))

    return {
        "odds" : odds.text,
        "general" : general.text,
        "matches" : matches.text,
        "lineups" : line_ups.text,
        "stats" : statistics.text
    }

def save_to_file(data, folder_name):
    os.mkdir("./data/{}".format(folder_name))
    identifier = return_identifier(data['stats'])
    for key, value in data:
        with open("./data/{}/{}_{}.json".format(folder_name, key, identifier), "w+") as file:
            file.write(value)

def get_all_event_ids(driver, by_rounds = False, test=False):

    # xpaths and vars
    if test:
        base_url = "file:///Users/bibbycodes/Documents/Projects/soccer_scrape/test_html/base_league.htm" # 
    else:
        base_url = "https://www.{}/tournament/football/england/premier-league/17".format(website)

    season_btn_xpath = "//div[@class='cell']//button"
    tournament_event_list_xpath = "//div[@class = 'tournament-event-list tournament-event-list--box']//a[contains(@class, 'js-event-link')]"
    previous_btn_xpath = "//div[contains(@class, 'show-previous-week')]"
    next_button_xpath = "//div[contains(@class, 'show-next-week')]"
    rounds_button_xpath = "//label[@class = 'js-tournament-page-events-select-round radio-switch__item']"
    week_btn_xpath = "//div[contains(@class, 'select-events-by-week')]//button"
    weeks_dropdown_xpath = "//ul[@class='dropdown-menu dropdown__menu dropdown__menu--compact dropdown__menu--box-events js-select-week-dropdown js-select-events-dropdown-inner u-h400 ps-container ps-active-y']//li"
    session_number_xpath = "//div[@class = 'event-list-table-wrapper js-event-list-table-wrapper']//div[@class = 'cell cell--justified u-pV4 ff-medium u-text-upper u-t2']//div[@class='cell__section']"
    weeks_menu_xpath = "//div[contains(@class, 'select-events-by-week')]//ul"
    rounds_menu_xpath = "//div[contains(@class, 'select-events-by-round')]//button"
    driver.get(base_url)
    num_seasons = len(driver.find_elements_by_xpath("//div[@class='cell']//li"))

    # for each season / year
    for i in range(num_seasons)[7:]:
        sleep(sleep_increment)

        # open seasons dropdown
        driver.find_element_by_xpath(season_btn_xpath).click()
        season_number = "-".join(driver.find_element_by_xpath(season_btn_xpath).text.split("/"))
        ith_season_xpath = "//div[@class='cell']//li[%d]" % i
        
        # click season
        if (len(driver.find_elements_by_xpath(ith_season_xpath)) > 0):
            driver.find_element_by_xpath(ith_season_xpath).click()
            sleep(sleep_increment)

        # scroll down
        for _ in range(2):
            actions = ActionChains(driver)
            actions.send_keys(Keys.SPACE)
            actions.perform()
            sleep(4)

        if by_rounds:
            menu_xpath = rounds_menu_xpath
            rounds_button = driver.find_element_by_xpath(rounds_button_xpath)
            rounds_button.click()
            sleep(2)
        else:
            menu_xpath = weeks_menu_xpath
            driver.find_element_by_xpath(week_btn_xpath).click()

        session_number = driver.find_element_by_xpath(session_number_xpath).text.split(" ")[1]
        print(session_number)
        # determine whether to click previous or next
        if(int(session_number) > 1):
            num_weeks = int(session_number)
            pagination_button_xpath = previous_btn_xpath
        elif(int(session_number) == 1):
            # does this need to be programitc?
            # week number should be elemnt at end of list
            num_weeks = int(session_number)
            pagination_button_xpath = next_button_xpath
        else:
            print("whats going on lol")

        
        # for each week
        for i in range(num_weeks):
            event_ids = []
            tournament_table = driver.find_elements_by_xpath(tournament_event_list_xpath)

            # for each match
            for count, match in enumerate(tournament_table):
                try:
                    date_xpath = "//a[contains(@class, 'pointer list-event')][{}]/div[1]".format(count + 1)
                    teams_xpath = "//a[contains(@class, 'pointer list-event')][{}]/div[3]".format(count + 1)
                    date = driver.find_element_by_xpath(date_xpath).text.replace(" ", "_").split("\n")[0]
                    teams = "-".join(driver.find_element_by_xpath(teams_xpath).text.replace(" ", "_").split("\n"))
                    event_id = match.get_attribute("data-id")
                    print({
                        "event_id" : event_id,
                        "date" : date,
                        "teams" : teams
                    })
                    event_ids.append(event_id)
                except:
                    continue
            
            sleep(sleep_increment)
                    
            try:
                driver.find_element_by_xpath(pagination_button_xpath).click()
                session_number = driver.find_element_by_xpath(week_btn_xpath).text.split(" ")[1]
                print("Got week {} event_ids".format(session_number))

            except:
                print("Cycle Over for season {}".format(season_number))
        
        season_number = "-".join(driver.find_element_by_xpath(season_btn_xpath).text.split("/"))
        with open("./Event_ids/season_{}_ids.json".format(season_number), "a+") as file:
                sorted_events = sort_and_remove_duplicates_from_list(event_ids)
                file.write(json.dumps(sorted_events))
                print(sorted_events)

def scrape_match_info(driver):
    match_info_xpath = "//div[contains(@class, 'sc-kgoBCf cWoebe')]//p"
    data_event_xpath = "//span[contains(@class, 'pointer page-title-action js-follow-event')]"

    teams_image_xpath = "//div[@class = 'cell__section details__emblem-container']//img"

    teams = driver.find_elements_by_xpath(teams_image_xpath)
    home_team = teams[0].get_attribute("title")
    away_team = teams[1].get_attribute("title")

    match_id = driver.find_element_by_xpath(
        data_event_xpath).get_attribute("data-event-id")
    league_id = driver.find_element_by_xpath(
        data_event_xpath).get_attribute("data-league-id")
    home_team_id = driver.find_element_by_xpath(
        data_event_xpath).get_attribute("data-hometeam-id")
    away_team_id = driver.find_element_by_xpath(
        data_event_xpath).get_attribute("data-awayteam-id")

    match_info = driver.find_elements_by_xpath(match_info_xpath)

    start_date = str(datetime.strptime(
        match_info[0].text.split("Start date: ")[1], "%d. %b %Y, %H:%M"))
    location = match_info[1].text.split(": ")[2]
    referee = match_info[2].text.split(",")[0].split(": ")[1]

    avg_cards_red = float(match_info[3].text[12:16])
    avg_cards_yellow = float(match_info[3].text[16:])

    match_info_dict = {
        'league_id': league_id,
        'match_id': match_id,
        'home_team_id': home_team_id,
        'away_team_id': away_team_id,
        'home_team': home_team,
        'away_team': away_team,
        'start_date': start_date,
        'location': location,
        'referee': referee,
        'avg_cards_red': avg_cards_red,
        'avg_cards_yellow': avg_cards_yellow
    }

    return match_info_dict

def scrape_player_stats_table(driver):
    sleep(sleep_increment)
    tabs = ["summary", "attack", "defence", "passing", "duels", "goalkeeper"]
    #tabs = ["defence"]
    table_as_list = []
    for i in range(len(tabs)):
        table_xpath = "//div[contains(@class, 'player-stats')]/div[contains(@id, '%s')]//tbody//tr" % tabs[i]
        table = driver.find_elements_by_xpath(table_xpath)

        print("Stats For " + tabs[i].capitalize() + " Tab")
        print("-----------------------------------------")

        for item in table:
            if type(item) == list:
                print(item)
                continue
            stats = item.get_attribute('innerText').split()

            # removes first value, joins first name and last name
            # check if second element is a name or number

            stats.pop(0)
            try:
                number = int(stats[1])
                
            except:
                stats[0] = stats[0] + " " + stats[1]
                stats.pop(1)

            if tabs[i] == "summary":
                accurate_passes = stats[4] + stats[5]
                stats[4] = accurate_passes

                duels_won = stats[6] + stats[7]
                stats[6] = duels_won

                stats.pop(7)
                stats.pop(5)

            # joins dribble(attempts) column

            if tabs[i] == "attack":

                dribble_attempts = stats[4] + stats[5]
                stats[4] = dribble_attempts
                stats.pop(5)

                notes_array = (stats[5:-2])
                notes = " ".join(notes_array)

                for j in range(len(notes_array) - 1):
                    stats.remove(notes_array[j])

                stats[5] = notes

            # joins tackles(won) column

            if tabs[i] == "defence":
                tackles_won = stats[4] + stats[5]
                stats[4] = tackles_won
                stats.pop(5)

                notes_array = (stats[6:-2])
                notes = " ".join(notes_array)

                for j in range(len(notes_array) - 1):
                    stats.remove(notes_array[j])

                stats[6] = notes

            # joins accurate passes, crosses(acc), long balls(acc) columns

            if tabs[i] == "passing":
                accurate_passes = stats[1] + stats[2]
                stats[1] = accurate_passes

                crosses_acc = stats[4] + stats[5]
                stats[4] = crosses_acc

                long_balls_acc = stats[6] + stats[7]
                stats[6] = long_balls_acc

                stats.pop(7)
                stats.pop(5)
                stats.pop(2)

                notes_array = (stats[5:-2])
                notes = " ".join(notes_array)

                for j in range(len(notes_array) - 1):
                    stats.remove(notes_array[j])

                stats[6] = notes

            # joins duels won

            if tabs[i] == "duels":
                duels_won = stats[1] + stats[2]
                stats[1] = duels_won
                stats.pop(2)

            # joins run outs(succ) column, joins notes column

            if tabs[i] == "goalkeeper":
                runs_out_succ = stats[3] + stats[4]
                stats[3] = runs_out_succ

                gk_notes_array = (stats[6:-2])
                gk_notes = " ".join(gk_notes_array)

                stats.pop(4)

                for j in range(len(gk_notes_array) - 1):
                    stats.remove(gk_notes_array[j])

                stats[5] = gk_notes

            # gets rid of weird utf8 error
            for value in stats:
                if value == "\xe2\x80\x93":
                    index = stats.index(value)
                    stats[index] = "-"
            table.append(stats)
    print(table_as_list)
    print("\n")

    # will need stats for first and second half also
    # stats for fouls seem to be missing for 1st and 2nd half but are within all
    # stats that are noted are not uniform accross all matches

def scrape_statistics_table(driver):
    sleep(sleep_increment)
    stats_xpath = "//div[@class = 'stat-group-event']"
    all_btn_xpath = "//div[@class = 'statistics-container']//li[1]"
    first_btn_xpath = "//div[@class = 'statistics-container']//li[2]"
    second_btn_xpath = "//div[@class = 'statistics-container']//li[3]"

    stats = driver.find_elements_by_xpath(stats_xpath)
    separated_stats = []

    for stat in stats:
        item = stat.text.split("\n")
        if len(item) > 3:
            i = 0
            while i < len(item):
                if (i + 1) % 3 == 0:
                    separated_stats.append(item[i-2:i+1])
                i += 1
        elif stat.text == "":
            continue
        else:
            separated_stats.append(item)

    stats_array = []

    print(len(separated_stats))

    for stat in separated_stats:
        print("----")
        print([stat[0],stat[2]])
        stats_array.append([stat[0],stat[2]])

    all_stats = {
        "ball possession" : stats_array[0],
        "total shots" : stats[1],
        "shots on target" : stats[2],
        "shots off target" : stats[3],
        "blocked shots" : stats[4],
        "corner kicks" : stats[5],
        "offsides" : stats[6],
        "fouls" : stats[7],
        "yellow cards" :stats[8],
        "big chance" : stats[9],
        "big chance missed" : stats[10],
        "counter attacks" : stats[11],
        "shots inside box" : stats[12],
        "shouts outside box" : stats[13],
        "goalkeeper saves" : stats[14],
        "passes" : stats[15],
        "accurate passes" : stats[16],
        "long balls": stats[17],
        "crosses" : stats[18],
        "dribbles" : stats[19],
        "possesoion lost" : stats[20],
        "duels won" : stats[21],
        "arials won" :stats[22],
        "tackles" : stats[23],
        "interceptions" : stats[24],
        "clearances" : stats[25]
    }

    print(all_stats)
    return all_stats

#index out of range!
def scrape_incidents_table(driver):
    incidents_table_xpath = "//div[@class = 'incidents-container']/div[contains(@class, 'cell')]"
    incidents_table = driver.find_elements_by_xpath(incidents_table_xpath)
    incidents_array = []

    for item in incidents_table:
        # print(item.text.encode('utf8'))
        incidents_array.append(item.text)

    #incidents_array = incidents_table.split("\n")[::-1]
    for incident in incidents_array:
        print(" ".join(incident.split("\n")))

def scrape_odds(driver):
    odds_container_xpath = "//div[@class ='js-event-page-odds-container']//table//td//span[contains(@class, 'js-odds-value-decimal')]"
    show_more_button = "//div[@class ='js-event-page-odds-container']//span[@class = 'collapsed']"
    driver.find_element_by_xpath(show_more_button).click()
    sleep(sleep_increment)
    odds = driver.find_elements_by_xpath(odds_container_xpath)
    odds_vals = []
    for odd in odds:
            odds_vals.append(float(odd.get_attribute('innerHTML').strip()))

    all_odds = {
        "full time" : odds_vals[0:3],
        "double chance" : odds_vals[3:6],
        "1st half" : odds_vals[6:9],
        "draw no Bet" : odds_vals[9:11],
        "both score" : odds_vals[11:13],
        "first to score" : odds_vals[13:16],
        "asian handicap" : odds_vals[16:18],
        "match goals" : odds_vals[18:35]
    }

    print("odds: ")
    print("\n")
    print(all_odds)

    return all_odds

def scrape_league(driver):
    urls = ["file://{}/HTML/westham.htm".format(cwd)]
    for url in urls:
        proxy_address = generate_random_proxy('{}/assets/filtered_uk_proxies.txt'.format(cwd))
        
        driver.get(url)
        sleep(sleep_increment)
        xpath = "//div[@class = 'js-event-widget-header-countdown-container']"

        try:
            if check_exists_by_xpath(driver, xpath):
                text = driver.find_element_by_xpath(xpath).text
                print(text)
                print("Future Match")
            else:
                scrape_odds(driver)
                print(scrape_match_info(driver))
                scrape_player_stats_table(driver)
                scrape_incidents_table(driver)
                
        except Exception as e:
            print(e)
            traceback.print_exc(file=sys.stdout)
        
    #scrape_statistics_table()
    driver.quit()

def get_matches(driver):
    base_url = "file://{}/HTML/league.htm".format(cwd)
    driver.get(base_url)

    season_btn_xpath = "//div[@class='cell']//button"
    # //div[@class = 'js-uniqueTournament-page-event-list-container event-list-container-tournament']//button[@class = 'btn dropdown__toggle dropdown__toggle--compact']
    week_btn_xpath = "//div[contains(@class, 'select-events-by-week')]//button"
    tournament_event_list_xpath = "//div[@class = 'tournament-event-list tournament-event-list--box']//a[contains(@class, 'js-event-link')]"
    previous_btn_xpath = "//div[contains(@class, 'show-previous-week')]"
    next_button_xpath = "//div[contains(@class, 'show-next-week')]"
    weeks_dropdown_xpath = "//ul[@class='dropdown-menu dropdown__menu dropdown__menu--compact dropdown__menu--box-events js-select-week-dropdown js-select-events-dropdown-inner u-h400 ps-container ps-active-y']//li"

    season = driver.find_elements_by_xpath(season_btn_xpath)
    print(season)

def check_ip_blocked(driver):
    blocked_ip_error_xpath = "//divc[@class= 'f-error-details']//h2" #Access denied
    message = driver.find_element_by_xpath(blocked_ip_error_xpath)
    if message == "Access denied":
        print("Access Denied, Try a new IP!")
        return True
    else:
        return False

def open_new_tab(driver, element):
    main_window = driver.current_window_handle
    sleep(sleep_increment)
    element.send_keys(Keys.COMMAND + "t")
    print("Clicking Element")
    driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.TAB)
    driver.switch_to.window(main_window)
    sleep(sleep_increment)
    #print(scrape_incidents_table(driver))
    # close tab
    driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + 'w')

def get_position(driver):
    season_btn_xpath = "//div[@class='cell']//button"
    #ith_season_xpath = "//div[@class='cell']//li[%d]" % i
    week_btn_xpath = "//div[contains(@class, 'select-events-by-week')]//button"
    match_event_list_xpath = "//div[@class = 'tournament-event-list tournament-event-list--box']//a[contains(@class, 'js-event-link')]"
    current_season = driver.find_element_by_xpath(season_btn_xpath).text
    current_session_number = int(driver.find_element_by_xpath(week_btn_xpath).text.split(" ")[1])
    match_links = driver.find_elements_by_xpath(match_event_list_xpath)
    for link in match_links:
        open_new_tab(driver, link)


driver = setup_firefox_driver('headless')
scrape_league()