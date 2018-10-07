'''
This data load script  will populate data  available at https://developer.dol.gov/others/sweat-and-toil/ into a Dynamo DB table.
The datasets contain information on child labor and forced labor worldwide from ILAB’s three flagship reports: 
Findings on the Worst Forms of Child Labor; List of Goods Produced by Child Labor or Forced Labor ; 

To use the API you must register at https://devtools.dol.gov/developer and request an API key for each application that will access the API. 
Registration and API keys are free.

Once you have the API key, create an environment variable DOL_API_KEY with it's value.

python human_trafficking_data_load.py --profile_name [AWS profile name] -- region [AWS region]

'''

from __future__ import print_function # Python 2/3 compatibility
import argparse
import boto3
import json
import decimal
import requests
import os
import pycountry

country_assessments = []
goods = []
api_key_header = {"X-API-KEY" : os.environ.get('DOL_API_KEY') }

# initiate the parser
parser = argparse.ArgumentParser()

# add long and short argument
parser.add_argument("--profile_name", "-p", help="AWS profile")
parser.add_argument("--region", "-r", help="AWS Region")

# read arguments from the command line
args = parser.parse_args()

'''
Get the Country assessment summary description
'''
def get_assessment_data():
  global country_assessments, api_key_header
  print(api_key_header)
  api_url = 'https://data.dol.gov/get/SweatToilAllAssessments/limit/200';
  response = requests.get(api_url, headers=api_key_header)
  country_assessments = json.loads(response.content.decode('utf-8'))

'''
Get assessment per country
'''
def get_assessment_country_data(assessment_id):
  country_assessment = next((country_assessment for country_assessment in country_assessments if country_assessment["id"] == assessment_id),False)
  return country_assessment

'''
Get List of Goods Produced by Child Labor or Forced Labor ; and List of Products Produced by Forced or Indentured Child Labor.
'''
def get_goods_data():
  global goods, api_key_header
  api_url = 'https://data.dol.gov/get/SweatToilAllGoods/limit/200';
  response = requests.get(api_url, headers=api_key_header)
  goods = json.loads(response.content.decode('utf-8'))  

'''
Get Sector name for the good
'''
def get_sector_good_data(good_id):
  sector = next((good for good in goods if good["id"] == good_id),False)
  return sector

'''
Get the countrywise report for Goods that involve Child Labor, Forced Child Labor, Forced Labor
'''
def get_report_data(offset=0):
  global api_key_header
  api_url = 'https://data.dol.gov/get/SweatToilAllCountryGoods/limit/200/offset/' + str(offset)

  response = requests.get(api_url, headers=api_key_header)
  if response.status_code == 200 and response.content:
    return json.loads(response.content.decode('utf-8'))
  else:
    return None

'''
Get coutry code based on country name
'''
def get_country_code(country_name):
  country_dict = {"Burma":"BU","Congo, Democratic Republic of the":"CD","Bolivia":"BO","Macedonia":"MK","Kosovo":"XK","SÃ£o TomÃ© and PrÃ­ncipe":"ST"}
  if country_name in country_dict:
    return country_dict[country_name]

  for country in pycountry.countries:
    if country_name == country.name:
      return country.alpha_2
      break

  return country_name

'''
load aggregated data into DynamoDB
'''
def load_dynamo_db_table(profile_name,region_name):
  session = boto3.session.Session(profile_name)
  dynamodb = session.resource('dynamodb', region_name)

  table = dynamodb.Table('human_trafficking_indicator')

  offset = 0 

  while True:
    report = get_report_data(offset)

    if not report:
      break

    for data in report:
        print("Adding country:", data['country'], data['good'], get_country_code(data['country']))

        advancement_data = get_assessment_country_data(data['assessment_id'])

        if not advancement_data:
          advancement_level = 'NA'
          advancement_description = 'NA'
        else:
          advancement_level = advancement_data["advancement_level"]
          advancement_description = advancement_data["description"]

        table.put_item(
           Item={
               'country': data['country'],
               'country_code': get_country_code(data['country']),
               'region_name': data['regionname'],
               'sector': get_sector_good_data(data['good_id'])["sector"],
               'good': data['good'].lower(),
               'report_year': data['year'],
               'child_labor': data['child_labor'],
               'forced_labor': data['forced_labor'],
               'forced_child_labor': data['forced_child_labor'],
               'advancement_level' : advancement_level,
               'advancement_description' : advancement_description
            }
        )

    offset += 200

if __name__ == '__main__':
  get_assessment_data()
  get_goods_data()
  load_dynamo_db_table(args.profile_name,args.region)
  