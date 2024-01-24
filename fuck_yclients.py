import argparse
import os
import requests
import http.cookies as c
import random
from time import sleep
import colorama

# master url
# url = 'https://b804383.yclients.com/api/v1/comments/754280/2219969' #Валентина Гичева
url = 'https://b804383.yclients.com/api/v1/comments/754280/2923220' #Ульяна Бадина

# must be taken from real cookies
headers = {
    "Authorization": "Bearer gtcwf654agufy25gsadh, User 9dd6e2b8d78aaf7a11b99507d4355dc6"
}

# all the options
cookies_filename = 'cookies.txt'
reviews_filename = 'reviews.txt'
names_filename = 'names.txt'
responses_filename = 'responses.txt'
wait_min = 8 # in seconds
wait_max = 34 # in seconds
SUCCESS_STATUS_CODE = 201
MARK = 5


def send_reviews():
    with requests.session() as s, \
        open(cookies_filename, 'r') as file_cookie, \
        open(responses_filename, 'a') as file_responses, \
        open(reviews_filename, 'r', encoding='utf-8') as file_reviews:
        total = 1
        
        cookie_raw = file_cookie.read()
        simple_cookie = c.SimpleCookie(cookie_raw)
        cookie_jar = requests.cookies.RequestsCookieJar()
        cookie_jar.update(simple_cookie)

        reviews = file_reviews.read().splitlines()
        print('[multi] Sending ' + colorama.Back.MAGENTA + str(len(reviews)) + colorama.Style.RESET_ALL + ' reviews...')
        user_warning = input('\nDo you want to continue? (' + colorama.Fore.GREEN + 'y' + colorama.Style.RESET_ALL + '/n): ').lower()
        if user_warning == 'y':
            for review in reviews:
                # creating payload
                payload = {
                    "name": str(get_name()),
                    "mark": MARK,
                    "text": str(review)
                }
                # sending actual response
                print('\nSending review #' + str(total) + '...')
                print('\n' + str(payload))
                # response = s.post(url, cookies=cookie_jar, data=payload, headers=headers)
                # file_responses.write('\n\n' + str(response.status_code) + '\n' + str(response.headers) + '\n\n' + str(response.text))
                # if response.status_code == 201:
                #     print('Success!')
                # else:
                #     print('Failed')
                total += 1
                # waiting before sending the next review
                wait_time = random.randint(wait_min, wait_max)
                print('Waiting... ' + str(wait_time) + 's')
                sleep(wait_time)
        else:
            print('Stopping...')
            return


def get_name():
    with open(names_filename, 'r', encoding='utf-8') as file_names:
        names_raw = file_names.read().splitlines()
        return random.choice(names_raw)


def send_single_review(rname: str, rtext: str):
    with requests.session() as s, \
        open(cookies_filename, 'r') as file_cookie, \
        open(responses_filename, 'a') as file_responses:
        cookie_raw = file_cookie.read()
        simple_cookie = c.SimpleCookie(cookie_raw)
        cookie_jar = requests.cookies.RequestsCookieJar()
        cookie_jar.update(simple_cookie)

        payload = {
            "name": str(rname),
            "mark": MARK,
            "text": str(rtext)
        }

        # sending actual response
        print('\nSending single review...')
        print('\n' + str(payload))
        # response = s.post(url, cookies=cookie_jar, data=payload, headers=headers)
        # file_responses.write('\n\n' + str(response.status_code) + '\n' + str(response.headers) + '\n\n' + str(response.text))
        if response.status_code == SUCCESS_STATUS_CODE:
            print('Success!')
        else:
            print('Failed')
        # would be probably needed for win task scheduler
        return 0


def main():
    colorama.init(autoreset=True)
    parser = argparse.ArgumentParser(description='fuck yclients!')
    parser.add_argument('Name', type=str, nargs='?', default=None, help='Name for the review')
    parser.add_argument('Text', type=str, nargs='?', default='', help='Text for the review')
    
    # checking if files exist
    if os.path.exists(cookies_filename):
        print('\n[cookies]', colorama.Fore.GREEN + '  +')
    else:
        print('\n[cookies]', colorama.Fore.RED + '  not found!')
        return
    if os.path.exists(names_filename):
        print('[names]', colorama.Fore.GREEN + '    +')
    else:
        print('[names]', colorama.Fore.RED + '    not found!')
        return
    if os.path.exists(reviews_filename):
        print('[reviews]', colorama.Fore.GREEN + '  +\n')
    else:
        print('[reviews]', colorama.Fore.RED + '  not found!\n')
        return

    args = parser.parse_args()
    if args.Name is not None:
        rname = args.Name
        rtext = args.Text
        print('[main] Entering ' + colorama.Fore.MAGENTA + 'single-send ' + colorama.Style.RESET_ALL + 'mode...')
        send_single_review(str(rname), str(rtext))
    else:
        print('[main] Entering ' + colorama.Fore.MAGENTA + 'multi-send ' + colorama.Style.RESET_ALL + 'mode...')
        send_reviews()


if __name__ == "__main__":
    main()