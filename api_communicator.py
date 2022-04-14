import os

import requests


def search(search_params):
    if type(search_params[0]) is tuple:
        params = {
            'theme': search_params[0][1],
            'character': search_params[1][1],
            'act': search_params[2][1],
            'scene': search_params[3][1]

        }

    else:
        params = {
            'id': []
        }
        for num in search_params:
            params["id"].append(num)

    try:
        quotations = requests.get(url='http://macbeth-quote-api.herokuapp.com/search', params=params,
                                  headers={'key': os.getenv("API_KEY")})
        quotations.raise_for_status()
        return quotations.json()

    except requests.exceptions.HTTPError as errh:
        return str(errh)
    except requests.exceptions.ConnectionError as errc:
        return str(errc)
    except requests.exceptions.Timeout as errt:
        return str(errt)
    except requests.exceptions.RequestException as err:
        return str(err)
    except:
        return "An unidentified error has occurred."
