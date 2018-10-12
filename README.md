# HTGI
Human Trafficking Goods Indicator API

The purpose of this api is to determine if a good produced in a country is listed under Goods Produced by Child Labor or Forced Labor,
based on datasets provied by Department of Labor that contains information on child labor and forced labor worldwide from ILAB’s three flagship reports: https://www.dol.gov/agencies/ilab/reports/child-labor

## Infrastructure

Create infrastructure with Dynamodb and Api Gateway

sam package --template-file template.yaml --output-template-file serverless-output.yaml 

aws cloudformation  deploy --template-file serverless-output.yaml --stack-name HTGI --region us-east-1 --profile [profile name] --parameter-overrides IamRoleArnParameter=arn:aws:iam::[AccountID]:role/htgi-api-gateway-role

htgi-api-gateway-role
```json
{
    "Version": "2012-10-17",
    "Statement": {
        "Effect": "Allow",
        "Action": [
            "dynamodb:GetItem",
            "dynamodb:Query"
        ],
        "Resource": "*"
    }
}
```
## Load data into DynamoDb table

This data load script  will populate data  available at https://developer.dol.gov/others/sweat-and-toil/ into a Dynamo DB table.
The datasets contain information on child labor and forced labor worldwide from ILAB’s three flagship reports: 
Findings on the Worst Forms of Child Labor; List of Goods Produced by Child Labor or Forced Labor ; 
To use the API you must register at https://devtools.dol.gov/developer and request an API key for each application that will access the API. 
Registration and API keys are free.
Once you have the API key, create an environment variable DOL_API_KEY with it's value.

```
python human_trafficking_data_load.py --profile_name [AWS profile name] --region [AWS Region]
```

## The API

GET /human-trafficking-indicator/country/{country}/good/{good} 

country - ISO 3166-1 alpha-2 codes
good - good name

### Response

200 - When data is found for the country and good

Example:
GET /human-trafficking-indicator/country/IN/good/coffee

```json
{
  "good": "coffee",
  "sector": "Agriculture",
  "child_labor": "Yes",
  "forced_child_labor": "No",
  "forced_labor": "No",
  "year": "2017",
  "advancement_level": "Significant Advancement",
  "advancement_description": "In 2017, India made a significant advancement in efforts to eliminate the worst forms of child labor. The government ratified both ILO Convention 182 and Convention 138 and amended the Child Labor Act to prohibit children under age 18 from working in hazardous occupations and processes. The government also launched the Platform for Effective Enforcement for No Child Labor to more effectively enforce child labor laws and implement the National Child Labor Program. In addition, the government released a new National Plan of Action for Children that implements the National Policy for Children, which includes a focus on child laborers, trafficked children, and other vulnerable children. However, children in India engage in the worst forms of child labor, including in forced labor producing garments and quarrying stones. Children also perform dangerous tasks producing bricks. The Child Labor Actâs hazardous work prohibitions do not include all occupations in which children work in unsafe and unhealthy environments for long periods of time. Penalties for employing children are insufficient to deter violations, and the recruitment of children by non-state armed groups is not criminally prohibited."
}
```

404 - When there is no data for the country / good combination
