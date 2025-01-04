import json
from urllib import parse

import requests

from utils.df_util import new_df
from utils.logging_util import logger

log = logger.get_logger('request_post')


def handle_cookie(cookies):
    cookies = parse.unquote(cookies)
    return cookies.encode("utf-8").decode("latin1")


def request_post(request_url, json_params, headers=None):
    log.debug('url:{}, params:{}'.format(request_url, json_params))
    if isinstance(json_params, list):
        log.info('request_params.size:{}'.format(len(json_params)))
    if headers is not None:
        for k, v in headers.items():
            if k == 'Cookie':
                cookies = parse.unquote(v)
                cookies = cookies.encode("utf-8").decode("latin1")
                headers[k] = cookies
            headers[k] = v
    else:
        headers = {}
    headers['Accept'] = 'application/json'
    headers['User-Agent'] = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/104.0.0.0 Safari/537.36')
    response = requests.post(request_url, json=json_params, headers=headers)
    response_text = response.text
    if response_text is None or len(response_text) == 0:
        response_text = '{}'
    log.debug('response_text:{}'.format(response_text))
    result_str = json.loads(response_text)
    return result_str


if __name__ == '__main__':
    code_nums = []
    months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    for month in months:
        url = 'http://insight.sf-express.com/topt/api/develope_indicator_online/code/detail'
        param = {"date_type": "month", "start_time": "2021-{}-01".format(month), "end_time": "2021-{}-31".format(month),
                 "center": "10043308", "team": "", "have_more": True, "emp_type": "", "position_name": "",
                 "current_page": 1, "page_size": 100, "sort_type": "", "sort_field": "", "export": False}
        _cookies = 'a_authorization_login=01404679; wps_domain=sf-express.com; csrf=Z565RKjyFsADebGCSZyiKzpxGGREjRXJ; sensorsdata2015session=%7B%7D; a_authorization_prd_login=01404679; tlb-1l9wib67-5923=9736cd98068f749613c4a2697bbbad2f; a_authorization_prd=712d5b60-0036-4da9-8eb7-d3ee8d19f310/78cb5357-3c65-4d22-8280-6b2f864310e6/5B6AA1E60BB9C63CB77F0DEFF6A685DD; a_authorization=d1f323fd-8026-4174-b285-eb376c1925f2/49635774-ebe1-4e81-b688-9538427a6273/959A07F706BDF2C9B887DEE09C78565D; BDPSESSION=ea4df92d-838b-4f87-900c-e9096c255094; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2201404679%22%2C%22first_id%22%3A%221838e067de1acf-0cea285058c6568-26021c51-2073600-1838e067de273c%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%2C%22platform%22%3A%22Web%22%2C%22platform_type%22%3A%22Web%22%2C%22platform_name%22%3A%22Web%E6%B5%8F%E8%A7%88%E5%99%A8%22%2C%22system_code%22%3A%22ITAO-SFTI-CORE%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTgzOGUwNjdkZTFhY2YtMGNlYTI4NTA1OGM2NTY4LTI2MDIxYzUxLTIwNzM2MDAtMTgzOGUwNjdkZTI3M2MiLCIkaWRlbnRpdHlfbG9naW5faWQiOiIwMTQwNDY3OSJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%2201404679%22%7D%2C%22%24device_id%22%3A%221838e067de1acf-0cea285058c6568-26021c51-2073600-1838e067de273c%22%7D; access_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2NzA1NzMwODksImV4cCI6MTY3MTE3Nzg4OSwidXNlcl9pZCI6IjAxNDA0Njc5In0.fIRf_Fxw1BmpBSLf_OTNAZAisc7KTSmUwuwKvtV2DZI; ticket=ST-73358-TPAtXGbGiGLdGuvDHlcT-casnode1; user_id=01404679; JSESSIONID=9169434065C80F9850FFE567C5E01536'
        result = request_post(url, param, _cookies)
        # print(result)
        res = result['data']['rows']
        code_nums.extend(res)
    print(code_nums)
    data = new_df(code_nums)
    data.to_excel(r'D:\user\downloads\代码统计-2021.xlsx')
