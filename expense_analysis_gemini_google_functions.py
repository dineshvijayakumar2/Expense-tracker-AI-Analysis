import functions_framework
from flask import Flask, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import PIL.Image
import pandas as pd
import requests
import json
import os
import warnings
warnings.filterwarnings("ignore")

import vertexai
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models

domain = "builderprogram-dvijayakumar.quickbase.com"
usertoken = os.environ.get("QB_USERTOKEN")
tableid = "btnwn8n6q"
reportid = "27"
headers = {'QB-Realm-Hostname': domain, 'User-Agent': 'PythonUtility', 'Authorization': 'QB-USER-TOKEN ' + usertoken}
perBatchRecordsCount = 50000


def getQBBatchDF(batchRecordCount, skipStart, firstIter):
    print("Generating the records from " + str(int(skipStart) + 1) + "...")
    url = 'https://api.quickbase.com/v1/reports/' + reportid + '/run?tableId=' + tableid + '&skip=' + str(
        skipStart) + '&top=' + str(batchRecordCount)
    queryBody = {
    }

    retryCount = 0
    qbdataDF = pd.DataFrame()
    qbrecordsDict = dict()
    qbfieldsDict = []

    try:
        print(url)
        rQuery = requests.post(url,
                               headers=headers,
                               json=queryBody,
                               verify=False
                               )

        if rQuery.status_code == 200:
            responseQuery = json.loads(json.dumps(rQuery.json(), indent=4))
            qbfieldsDict = list(responseQuery["fields"])
            qbrecordsDict = (responseQuery["data"])
            qbdataDF = pd.DataFrame.from_dict(qbrecordsDict, orient="columns")
            for col in qbdataDF.columns:
                qbdataDF[col] = pd.json_normalize(qbdataDF[col], max_level=0)
        else:
            print("Skipped the records from " + str(int(skipStart) + 1) + " to " + str(
                int(skipStart) + perBatchRecordsCount) + "...")

        return qbdataDF, qbfieldsDict, rQuery.status_code
    except IndexError as e:
        print(e)
        while retryCount < 3:
            retryCount += 1
            print("Retry "+str(retryCount))
            time.sleep(5)
            continue



def exportqbdata(batchRecordCount, skipStart):
    if len(str(batchRecordCount)) == 0:
        batchRecordCount = perBatchRecordsCount
    if (int(batchRecordCount) <= perBatchRecordsCount):
        outputdf, qbfieldsDict, statusCode = getQBBatchDF(batchRecordCount, skipStart, firstIter=True)
        #outputdf.to_csv("qbdata.csv", encoding="utf-8-sig")
    else:
        outputdf = pd.DataFrame()
        lastbatch = False
        skipStartIter = int(skipStart)
        firstIter = True
        print(batchRecordCount, skipStart)
        while lastbatch == False:
            qbbatchdf, qbfieldsDict, statusCode = getQBBatchDF(perBatchRecordsCount, skipStartIter, firstIter)
            print(statusCode)
            if statusCode == 200:
                firstIter = False
                outputdf = outputdf.append(qbbatchdf)
                #outputdf.to_csv("qbdata.csv", encoding="utf-8-sig")
                skipStartIter += perBatchRecordsCount
                if skipStartIter > (int(batchRecordCount)+int(skipStart)):
                    lastbatch = True
            else:
                continue

    qbfieldsDF = pd.DataFrame.from_dict(qbfieldsDict)
    qbfieldsDF.set_index("id", inplace=True)
    qbcols = outputdf.columns
    qbcolnames = []
    for col in qbcols:
        qbcolnames.append(qbfieldsDF["label"][int(col)])
    outputdf.columns = qbcolnames
    outputdf.reset_index(drop=True, inplace=True)
    print(outputdf.shape)
    #outputdf.to_csv("qbdata.csv", encoding="utf-8-sig")
    #print("Exporting "+str(batchRecordCount)+" records to a CSV file...")
    return outputdf


api_key = os.environ.get('GOOGLE_GEMINI_API_KEY', "No such environment variable")
print(api_key)
genai.configure(api_key=api_key)

batchRecordCount = "1000"
skipStart = "0"
expenses_data_df = exportqbdata(batchRecordCount, skipStart)
# Convert DataFrame to string with pipe separator for columns and newline for rows
formatted_data = expenses_data_df.to_csv(sep='|', index=False, lineterminator='\n')

# Initialize the Vertex AI and model configuration once when the server starts
vertexai.init(project="vegan-website-421304", location="us-central1")
textsi_1 = "You are a financial analyst, you need to answer questions based on the below data\n" + formatted_data

model = GenerativeModel(
    "gemini-1.0-pro",
    system_instruction=[textsi_1]
)

chat = model.start_chat()


@functions_framework.http
def hello_http(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)
    request_args = request.args

    headers = {
        'Access-Control-Allow-Origin': '*',  # Adjust for specific origins if needed
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type'
    }



    if request_json and 'user_input' in request_json:
        user_input = request_json['user_input']
    elif request_args and 'user_input' in request_args:
        user_input = request_args['user_input']
    else:
        user_input = 'hello'


    # Configuration for the generation process
    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 1,
        "top_p": 0.95,
    }

    # Safety settings to control content generation
    safety_settings = {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }

    # Send the user message to the chat and get the response
    response = chat.send_message(
        [user_input],
        generation_config=generation_config,
        safety_settings=safety_settings
    )

    # Extract the response
    formatted_response = response.candidates[0].content.parts[0].text
    return jsonify({'message': formatted_response}), 200, headers


