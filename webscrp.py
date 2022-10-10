from lxml import html
from json import dump, loads
from requests import get
import json
import csv
import re
from re import sub
from dateutil import parser as dateparser
from time import sleep
from lxml.etree import ParserError
import argparse
import traceback
import random


def ParseReviews(asin):
    # This script has only been tested with Amazon.com
    amazon_url = 'http://www.amazon.com/dp/' + asin
    # Add some recent user agent to prevent amazon from blocking the request
    # Find some chrome user agent strings  here https://udger.com/resources/ua-list/browser-detail?browser=Chrome

    user_agents_list = [
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
        'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8',
        'Mozilla/5.0 (X11; OpenBSD i386) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/534.59.10 (KHTML, like Gecko) Version/5.1.9 Safari/534.59.10',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/601.7.8 (KHTML, like Gecko)',
        'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_4; de-de) AppleWebKit/525.18 (KHTML, like Gecko) Version/3.1.2 Safari/525.20.1',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9a1) Gecko/20070308 Minefield/3.0a1',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko)',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/604.5.6 (KHTML, like Gecko) Version/11.0.3 Safari/604.5.6',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.1 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15'
        ]

    # user_agents_list = ['Mozilla/5.0 (X11; CrOS i686 1193.158.0) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.75 Safari/535.7']
    lists = []
    for i in range(0, 100):
        user_agent = random.choice(user_agents_list)
        if user_agent not in lists:
            lists.append(user_agent)
            # print(count)
            headers = {'User-Agent': user_agent}
            response = get(amazon_url, headers=headers, timeout=30, verify=False)
            # sleep(10)
            print("Request #%d\nUser-Agent Sent:%s\nUser Agent Recevied by HTTPBin:" % (i, user_agent))
            print(response.content)
            print("-------------------\n\n")

        if response.status_code == 404:
            return {"url": amazon_url, "error": "page not found"}
        if response.status_code == 403:
            raise ValueError("Captcha Found")
        if response.status_code != 200:
            continue
        # print(response.text)
        # print(response.status_code)

        # Removing the null bytes from the response.
        cleaned_response = response.text.replace('\x00', '')
        parser = html.fromstring(cleaned_response)

        XPATH_AGGREGATE = '//span[@id="acrCustomerReviewText"]/text()'
        XPATH_REVIEW_SECTION_1 = '//div[contains(@id,"reviews-summary")]'
        XPATH_REVIEW_SECTION_2 = '//div[@data-hook="review"]'
        # XPATH_AGGREGATE_RATING = '//table[@id="histogramTable"]//tr'
        XPATH_PRODUCT_NAME = '//h1//span[@id="productTitle"]//text()'
        XPATH_PRODUCT_PRICE = '//span[@id="priceblock_ourprice"]/text()'
        XPATH_Review_count = '//div[@data-hook="total-review-count"]'
        XPATH_FEATURES = '//div[@id="featurebullets_feature_div"]'
        XPATH_AVG_STAR = '//i[@data-hook="average-star-rating"]//text()'
        XPATH_BRAND = '//*[@id="bylineInfo"]//text()'
        XPATH_CATEGORY = '//*[@id="wayfinding-breadcrumbs_feature_div"]/ul/li[1]/span/a//text()'
        XPATH_ASIN = '//div[@id="cerberus-data-metrics"]'
        XPATH_PRODUCTDESCRIPTION = '//div[@id="productDescription"]'
        XPATH_PRODUCTDESCRIPTION1 = '//div[@id="dpx-aplus-3p-product-description_feature_div"]'

        raw_product_price = parser.xpath(XPATH_PRODUCT_PRICE)
        raw_product_name = parser.xpath(XPATH_PRODUCT_NAME)
        # total_ratings  = parser.xpath(XPATH_AGGREGATE_RATING)
        reviews = parser.xpath(XPATH_REVIEW_SECTION_1)
        raw_reviews_count = parser.xpath(XPATH_Review_count)
        raw_category = parser.xpath(XPATH_CATEGORY)
        Features = parser.xpath(XPATH_FEATURES)
        raw_Avg_star = parser.xpath(XPATH_AVG_STAR)
        raw_brand = parser.xpath(XPATH_BRAND)
        #raw_Product_Asins = parser.xpath(XPATH_ASIN)[0].attrib['data-asin']

        # productdescription
        try:
            raw_productDescription = parser.xpath(XPATH_PRODUCTDESCRIPTION)[0].itertext()
            productDescription = ''.join(raw_productDescription).strip() if raw_productDescription else None
        except:
            if XPATH_PRODUCTDESCRIPTION1:
                raw_productDescription = parser.xpath(XPATH_PRODUCTDESCRIPTION1)
                for raw_PD in raw_productDescription:
                    XPATH_PD = './/p[contains(@class, "a-spacing-base")]//text()'
                    PD = raw_PD.xpath(XPATH_PD)
                    productDescription = ''.join(PD).strip() if PD else None

        product_price = ''.join(raw_product_price).replace(',', '')
        product_name = ''.join(raw_product_name).strip()
        # reviews_count = ''.join(raw_reviews_count).replace(',', '')
        Average_star_rating = ''.join(raw_Avg_star).replace('out of 5 stars', '')
        Brand = ''.join(raw_brand).strip()
        category_p = ''.join(raw_category).strip() if raw_category else None
        #Product_Asins = ''.join(raw_Product_Asins) if raw_Product_Asins else None

        for reviews_count in raw_reviews_count:
            XPATH_Total_Review = './/span[@class="a-size-base a-color-secondary"]//text()'
            raw_count = reviews_count.xpath(XPATH_Total_Review)
            try:
                total_review_count = ' '.join(raw_count).strip()
            except:
                total_review_count = None

        '''for category in PRODUCT_CATEGORY:
                XPATH_Categories = '//*[@id="wayfinding-breadcrumbs_feature_div"]/ul/li[1]/span/a//text()'
                raw_category = category.xpath(XPATH_Categories)
                category_p = ' '.join(''.join(raw_category).strip()) if raw_category else None'''

        for feature in Features:
            XPATH_Feature = './/span[@class="a-list-item"]//text()'
            raw_feature = feature.xpath(XPATH_Feature)
            try:
                feature_s = ''.join(raw_feature).strip()
            except:
                feature_s = None

        if not reviews:
            reviews = parser.xpath(XPATH_REVIEW_SECTION_2)

        reviews_list = []

        # Parsing individual reviews
        for review in reviews:
            XPATH_RATING = './/i[@data-hook="review-star-rating"]//text()'
            XPATH_REVIEW_HEADER = './/a[@data-hook="review-title"]//text()'
            XPATH_REVIEW_POSTED_DATE = './/span[@data-hook="review-date"]//text()'
            XPATH_REVIEW_TEXT_1 = './/div[@data-hook="review-collapsed"]//text()'
            XPATH_REVIEW_TEXT_2 = './/div//span[@data-action="columnbalancing-showfullreview"]/@data-columnbalancing-showfullreview'
            XPATH_REVIEW_COMMENTS = './/span[@data-hook="review-comment"]//text()'
            XPATH_AUTHOR = './/span[contains(@class,"profile-name")]//text()'
            XPATH_REVIEW_TEXT_3 = './/div[contains(@id,"dpReviews")]/div/text()'
            XPATH_helpful = './/span[@data-hook="helpful-vote-statement"]//text()'
            XPATH_VERIFIED = './/span[@data-hook="avp-badge-linkless"]//text()'

            raw_review_author = review.xpath(XPATH_AUTHOR)
            raw_review_rating = review.xpath(XPATH_RATING)
            raw_review_header = review.xpath(XPATH_REVIEW_HEADER)
            raw_review_posted_date = review.xpath(XPATH_REVIEW_POSTED_DATE)
            raw_review_text1 = review.xpath(XPATH_REVIEW_TEXT_1)
            raw_review_text2 = review.xpath(XPATH_REVIEW_TEXT_2)
            raw_review_text3 = review.xpath(XPATH_REVIEW_TEXT_3)
            raw_review_helpful = review.xpath(XPATH_helpful)
            raw_verified = review.xpath(XPATH_VERIFIED)

            # Cleaning data
            author = ' '.join(' '.join(raw_review_author).split())
            review_rating = ''.join(raw_review_rating).replace('out of 5 stars', '')
            review_header = ' '.join(' '.join(raw_review_header).split())
            review_helpful = ' '.join(' '.join(raw_review_helpful).split())
            review_verified = ' '.join(' '.join(raw_verified).split())

            try:
                review_posted_date = ' '.join(''.join(raw_review_posted_date).split())
            except:
                review_posted_date = None
            review_text = ' '.join(' '.join(raw_review_text1).split())

            # Grabbing hidden comments if present
            if raw_review_text2:
                json_loaded_review_data = loads(raw_review_text2[0])
                json_loaded_review_data_text = json_loaded_review_data['rest']
                cleaned_json_loaded_review_data_text = re.sub('<.*?>', '', json_loaded_review_data_text)
                full_review_text = review_text + cleaned_json_loaded_review_data_text
            else:
                full_review_text = review_text
            if not raw_review_text1:
                full_review_text = ' '.join(' '.join(raw_review_text3).split())

            raw_review_comments = review.xpath(XPATH_REVIEW_COMMENTS)
            review_comments = ''.join(raw_review_comments)
            review_comments = sub('[A-Za-z]', '', review_comments).strip()
            review_dict = {
                # 'review_comment_count': review_comments,
                'review_text': full_review_text,
                'review_posted_date': review_posted_date,
                'review_Title': review_header,
                'review_rating': review_rating,
                'review_username': author,
                'review_verify': review_verified,
                'found_helpful': review_helpful

            }
            reviews_list.append(review_dict)

        data = {
            'name': product_name,
            'brand': Brand,
            'category': category_p,
            'price': product_price,
            'url': amazon_url,
            #'total_review': total_review_count,
            'Average_stars': Average_star_rating,
            # 'ASIN' : Product_Asins,
            'Features': feature_s,
            'Product_Description': productDescription,
            'reviews': reviews_list

        }
        return data

    return {"error": "failed to process the page", "url": amazon_url}
    return list


def ReadAsin():
    # Add your own ASINs here
    AsinList = ['B07N4M9TL9']

    extracted_data = []

    for asin in AsinList:
        print("Downloading and processing page http://www.amazon.com/dp/" + asin)

        extracted_data.append(ParseReviews(asin))
        sleep(20)
    f = open('../productDetailf.json', 'w')
    dump(extracted_data, f, indent=4)
    f.close()


if __name__ == '__main__':
    ReadAsin()