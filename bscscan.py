import requests
import random
from bs4 import BeautifulSoup
from time import sleep
import json
import pandas

def pick_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"
        "Mozilla/5.0 (X11; Linux i686; rv:97.0) Gecko/20100101 Firefox/97.0"
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 12.2; rv:97.0) Gecko/20100101 Firefox/97.0"
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15"
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 OPR/83.0.4254.27"
        "Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 OPR/83.0.4254.27"
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 OPR/83.0.4254.27"
    ]

    header = {"user-agent": random.choice(user_agents)}

    return header


def get_bscscan():
    header = pick_random_user_agent()

    while True:
        response = requests.get(
            "https://bscscan.com/contractsVerified?ps=100", headers=header, timeout=5
        )

        if response.status_code == 200:
            break
        else:
            header = pick_random_user_agent()

    return response.content


def parse_body(body):
    parsed_body = pandas.read_html(body)[0]

    results_array = []
    for i, row in parsed_body.iterrows():
        contract = {
            "position": i,
            "name": row["Contract Name"],
            "compiler": row["Compiler"],
            "compiler_version": row["Version"],
            "license": row["License"],
            "balance": row["Balance"],
            "transactions": row["Txns"],
            "address": row["Address"],
            "contract_url": "https://bscscan.com/address/" + row['Address'],
            "token_url":
            "https://bscscan.com/token/" + row['Address'] + "#balances",
            "holders_url":
            "https://bscscan.com/token/tokenholderchart/"
            + row['Address']
            + "?range=500",
        }
        results_array.append(contract)

    return results_array


def get_token_page(link):
    header = pick_random_user_agent()

    while True:
        response = requests.get(link, headers=header, timeout=5)

        if response.status_code == 200:
            break
        else:
            header = pick_random_user_agent()

    return response.content


def parse_token_page(body):

    token_page = get_token_page(body["token_url"])

    sleep(0.5)

    parsed_body = BeautifulSoup(token_page, "html.parser")

    page_dictionary = {}

    name_element = parsed_body.select_one(".media-body .small")
    if name_element is None:
        page_dictionary = "Not Existing"
    elif name_element is not None:
        page_dictionary["name"] = name_element.text[:-1]

        overview_element = parsed_body.select_one(
            ".card:has(#ContentPlaceHolder1_tr_valuepertoken)"
        )
        if overview_element is not None:

            overview_dictionary = {}

            token_standart = overview_element.select_one(".ml-1 b")
            if token_standart is not None:
                overview_dictionary["token_standart"] = token_standart.text

            token_price = overview_element.select_one(".d-block span:nth-child(1)")
            if token_price is not None:
                overview_dictionary["token_price"] = float(token_price.text.replace('$', ''))

            token_marketcap = overview_element.select_one("#pricebutton")
            if token_marketcap is not None:
                overview_dictionary["token_marketcap"] = float(
                    token_marketcap.text[2:-1].replace('$', '')
                )

            token_supply = overview_element.select_one(".hash-tag")
            if token_supply is not None:
                overview_dictionary["token_supply"] = float(
                    token_supply.text.replace(",", "")
                )

            token_holders = overview_element.select_one(
                "#ContentPlaceHolder1_tr_tokenHolders .mr-3"
            )
            if token_holders is not None:
                overview_dictionary["token_holders"] = int(token_holders.text[1:-11].replace(',', ''))

            token_transfers = overview_element.select_one("#totaltxns")
            if token_transfers is not None:
                overview_dictionary["token_transfers"] = int(token_transfers.text.replace(',', '')) if token_transfers.text != '-' else 0
            token_socials = overview_element.select_one(
                "#ContentPlaceHolder1_trDecimals+ div .col-md-8"
            )
            if token_socials is not None:
                overview_dictionary["token_socials"] = token_socials.text

            if overview_dictionary["token_holders"] != 0:
                parsed_body = BeautifulSoup(
                    get_token_page(body["holders_url"]), "html.parser"
                )

                holders_dictionary = {}

                holder_addresses = parsed_body.select(
                    "#ContentPlaceHolder1_resultrows a"
                )
                holder_quantities = parsed_body.select("td:nth-child(3)")
                holder_percentages = parsed_body.select("td:nth-child(4)")

                for rank in range(len(holder_addresses)):
                    holders_dictionary[rank] = {}

                    holders_dictionary[rank]["address"] = holder_addresses[rank].text
                    holders_dictionary[rank]["quantity"] = float(
                        holder_quantities[rank].text.replace(",", "")
                    )
                    holders_dictionary[rank]["percentage"] = float(
                        holder_percentages[rank].text[:-1].replace(",", "")
                    )

                page_dictionary["holders_dictionary"] = holders_dictionary

            page_dictionary["overview_dictionary"] = overview_dictionary

    return page_dictionary


body = get_bscscan()
results_array = parse_body(body)
for token_dictionary in results_array:
    page_dictionary = parse_token_page(token_dictionary)

    token_dictionary["page_dictionary"] = page_dictionary

    print(token_dictionary)


with open("results.json", "w+") as f:
    json.dump(results_array, f, indent=2)
