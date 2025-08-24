import requests

url = "https://www.shein.com.vn/bff-api/product/search/v3/get_keywords?_ver=1.1.8&_lang=en&word_type=2&scene=home"

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "armortoken": "T0_3.8.2_aCVU9t692W3Glc9m72P-vbpjZyMh2Jk9MVJSMqbr1Y5jBUK0eIHKkq8SoqpH2SLau0smdt-UyXPSYnstykixNCAyewb6FAWG_TXDxcZrTBdBhO_gViObJz-r5E9MZdyGIMzACFDNdWUXYtnjBgXD3YXuy1X0qvSt0hBtL_iUKQz3ANBb2GdDsFhDi6k0DVZ__1755999172953",
    "priority": "u=1, i",
    "referer": "https://www.shein.com.vn/pdsearch/turtle",
    "sec-ch-ua": "\"Not;A=Brand\";v=\"99\", \"Microsoft Edge\";v=\"139\", \"Chromium\";v=\"139\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "smdeviceid": "WHJMrwNw1k/GGHk7Zc/BmmymSJA43a0azqEth+DO5F6rWXc9fwKScT0/T2H0dQJw8uqb2eTZRtutxiAOnudeH2w8qwONy1BWDdCW1tldyDzmQI99+chXEihXOBOhkJ06E9lCUKKcsmkR3KAhq3N/faTYmmmXo8LlTkQE5YcNLqNriNYPfoOP/bkZ2IDwYrIyWFRRuSg/X1FURTkAd7H/eWg3vWKWV694HqUQFnByzBOM5Tz2fR+FVIA2VVwB0PnwFfUGgIqCuSLQ=1487582755342",
    "uber-trace-id": "ff6d8b3e8e600927:ff6d8b3e8e600927:0:0",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
    "webversion": "13.3.4",
    "x-ad-flag": "8FkZa3NuCnoO+IBsqSDbVeWpkW71nzyxJdF18svBILmZ0k+h6+rK67aH0c1E5efGgWYq61YJe9rvWC5xPj7ZVVYoP3i9GVpBfVkWfa8EsrsGa2KgaixOSZmJfGKy6YI874yU0pb2l85B3RSMhSMlbQ==",
    "x-csrf-token": "E0UmSCIr-wIO69TD_HcDu40eHi12jqJezpQU",
    "x-gw-auth": "a=xjqHR52UWJdjKJ0x6QrCsus66rNXR9@2.0.13&b=1755999193233&d=06942fbc37be6a98b8dee877d03ae8f6&e=YcREOZjg0OThjZmY0NzExN2I5YjEyYjVkMDdkYjcyMDhjN2Q3N2Y4ZTI1NjBlNTRkNTJhMGMzYTJhODVjNmYxMzdhNg%3D%3D",
    "x-oest": "MEM0MTNEMDBfQ0FGQ18xOUM0X0ZCMUZfQUM0NkE2OUQyMzNEfDE3NTU5OTkxOTMyMjl8",
    "x-requested-with": "XMLHttpRequest"
}

cookies = {
    "armorUuid": "20250823232957165eaf44073da1ace36002582979b73e001a320d0053c79500",
    "sessionID_shein": "s%3Ai4x5UwqD5P-9KvAIEbqK6BeMHZscDXFW.8v0vXpvdFOzWBkO5Js103V5ynhZNQPWzGq2VmRspsQ0",
    "AT": "MDEwMDE.eyJiIjo3LCJnIjoxNzU1OTYyOTk3LCJyIjoiRHBDRXhxIiwidCI6MX0.71b7d0f49663d1d8",
    "smidV2": "2025082322295923ec656b0a3d948b175acf498dcd78ca00d07a8c5e72e4590",
    "zpnvSrwrNdywdz": "center",
    "_gcl_au": "1.1.1094138113.1755963002",
    "_fbp": "fb.2.1755963002362.76501977180300767",
    "_pin_unauth": "dWlkPVpERmxNVGt4Tm1FdFlXWTRZeTAwTWprMkxUazBPV1l0Wm1FME9USTNPVFpqTkdJeQ",
    "_cbp": "fb.2.1755963002875.1391512685",
    "jump_to_vn": "1",
    "fita.sid.shein": "jGAMwtTuVyQG2J41Ypy5M8bQS7L83G_V",
    "_gcl_gs": "2.1.k1$i1755996777$u100074972",
    "fita.short_sid.shein": "7hAUCpC1KELclAEtThdC-GsEbr6IYIaZ",
    "_gcl_aw": "GCL.1755998036.Cj0KCQjwzaXFBhDlARIsAFPv-u9RsMv4g8aivCjtbzuMDOt8Ev8qr9Wax-x0EKOmy3fWKJPiveunlykaApyBEALw_wcB",
    "_uetsid": "092871d0803611f08bfaa7a056dfb627",
    "_uetvid": "0928b8f0803611f08838c5c17908faa3",
    "_derived_epik": "dj0yJnU9c0pUZlVod0JGVnF6alkzbjQ3VEhLMnA4bGczMnR6dDMmbj1uSzdpb0dhU3dNLV9TYktZMkNHR0xBJm09MSZ0PUFBQUFBR2lxYThRJnJtPTEmcnQ9QUFBQUFHaXFhOFEmc3A9NQ"
}


response = requests.get(url, headers=headers, cookies=cookies)
print(response.text)