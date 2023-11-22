import requests
import time
import json

MAILTM_HEADERS = {   
    "Accept": "application/json",
    "Content-Type": "application/json" 
}

class MailTmError(Exception):
    pass

def _make_mailtm_request(request_fn, timeout = 600):
    tstart = time.monotonic()
    error = None
    status_code = None
    while time.monotonic() - tstart < timeout:
        try:
            r = request_fn()
            status_code = r.status_code
            if status_code == 200 or status_code == 201:
                return r.json()
            if status_code != 429:
                break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            error = e
        time.sleep(1.0)
    
    if error is not None:
        raise MailTmError(e) from e
    if status_code is not None:
        raise MailTmError(f"Status code: {status_code}")
    if time.monotonic() - tstart >= timeout:
        raise MailTmError("timeout")
    raise MailTmError("unknown error")

def get_mailtm_domains():
    def _domain_req():
        return requests.get("https://api.mail.tm/domains", headers = MAILTM_HEADERS)
    
    r = _make_mailtm_request(_domain_req)

    return [ x['domain'] for x in r ]

def create_mailtm_account(address, password):
    account = json.dumps({"address": address, "password": password})   
    def _acc_req():
        return requests.post("https://api.mail.tm/accounts", data=account, headers=MAILTM_HEADERS)

    r = _make_mailtm_request(_acc_req)
    assert len(r['id']) > 0


#list emails w/ pagination of headers
def get_mailtm_headers(account_id, token):
    headers=[]
    page = 1

    while True:
        def _header_req():
            return requests.get(f"https://api.mail.tm/messages?page=1?", headers = {
                "Accept": "application/json",
                "Content-Type":"application/json",
                "Authorization": f"Bearer {token}"
                })
    
        r = _make_mailtm_request(_header_req)

        headers.extend(r['hydra:member'])

        if 'hydra:next' not in r:
            break
        page +=1

    return headers


#replace acct_id and token with your actual id,token
# code needs to have a function to read an email
def read_email(account_id, token,message_id):
    def _read_req():
        return requests.get(f"https://api.mail.tm/{message_id}", headers = {
                "Accept": "application/json",
                "Content-Type":"application/json",
                "Authorization": f"Bearer {token}"
                })
    r = _make_mailtm_request(_read_req)

    return r

#Your main loop needs to check if new mail has arrived every minute and print it
def main():
    account_id = "your acct id"
    token = "your token"
    processed_message_ids = set()

    while True:
        headers = get_mailtm_headers(account_id, token)

        for header in headers:
            message_id = header['id']

            if message_id not in processed_message_ids:
                email = read_email(account_id, token, message_id)
                print(email)
                processed_message_ids.add(message_id)

        time.sleep(60)


if __name__ == "__main__":
    main()

            




    
    
    




