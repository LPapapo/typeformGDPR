import requests
import configparser
import os
import subprocess
import sys

api_workspaces_url = "https://api.typeform.com/workspaces"
workspaces_page_size = 200

api_forms_url = "https://api.typeform.com/forms/"
forms_page_size = 200


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def openLogFile():
    main_path = os.path.dirname(__file__)
    file_path = os.path.join(main_path, 'logs/logs.txt')
    return open(file_path, "w")


def openErrorFile():
    main_path = os.path.dirname(__file__)
    file_path = os.path.join(main_path, 'error/error.txt')
    return open(file_path, "w")


def openResultsFile():
    main_path = os.path.dirname(__file__)
    file_path = os.path.join(main_path, 'results/results.txt')
    return open(file_path, "w")


def writeLog(message):
    print(message)
    logFile.write(message + '\n')


def writeResult(message):
    resultFile.write(message + '\n')


def writeError(message):
    errorFile.write(message + '\n')


def setup_config():
    config_file = configparser.RawConfigParser()
    main_path = os.path.dirname(__file__)
    file_path = os.path.join(main_path, 'config/config.cfg')
    config_file.read(file_path)
    return config_file


def get_matching_data_in_responses(api_url, email):
    params = {
        'query': email
    }
    apiResponse = requests.get(api_url, headers=header, params=params)
    responses = apiResponse.json()
    return responses


def delete_response(response_id, form_id):
    params = {
        'included_response_ids': response_id,
    }
    requests.delete(api_forms_url + form_id + '/responses', headers=header, params=params)


def handle_email(email, formId, formName, workspaceName):
    apiResponseUrl = api_forms_url + formId + '/responses'
    response = get_matching_data_in_responses(apiResponseUrl, email)
    if response['total_items'] != 0:
        message = '------ FOUND email: ' + email + ' on workspace " ' + workspaceName + ' " and form " ' + formName+'. Number of occurrences " '+str(response['total_items'])+" ' "

        writeLog(message)
        writeResult(message)

        response_deletion_flag = config.getboolean('GeneralProperties', 'response.deletion')
        if response_deletion_flag:
            items = response['items']
            for item in items:
                delete_response(item['response_id'], formId)
                message = '--------DELETED response with email: ' + email + ' on workspace " ' + workspaceName + ' " and form " ' + formName+' "'

                writeLog(message)
                writeResult(message)


try:

    install('requests')

    config = setup_config()
    logFile = openLogFile()
    errorFile = openErrorFile()
    resultFile = openResultsFile()

    writeLog('TYPEFORM SCAN STARTED')

    if config.get('ApiSection', 'api.access.token').strip() == '':
        writeLog("No access token found")
        writeError("No access token found")


    header = {
        'Authorization': 'Bearer ' + config.get('ApiSection', 'api.access.token')
    }

    params = {
        'page_size': workspaces_page_size
    }
    apiResponse = requests.get(api_workspaces_url, headers=header, params=params)
    workspaces = apiResponse.json()['items']

    for workspace in workspaces:
        workspace_form_url = workspace['forms']['href']

        workspaceName = workspace['name']
        writeLog(workspaceName)

        params = {
            'page_size': forms_page_size
        }
        apiResponse = requests.get(workspace_form_url, headers=header, params=params)
        forms = apiResponse.json()['items']

        for form in forms:
            formId = form['id']
            formName = form['title']

            main_path = os.path.dirname(__file__)
            file_path = os.path.join(main_path, 'input/input.txt')
            with open(file_path) as f:
                for line in f:
                    handle_email(line.strip(), formId, formName, workspaceName)

            writeLog('----- ' + formName)

    writeLog('TYPEFORM SCAN COMPLETED')
    logFile.close()
    resultFile.close()
    errorFile.close()


except Exception as e:
    writeLog(e)
    writeError(e)
finally:
    logFile.close()
    resultFile.close()
    errorFile.close()
