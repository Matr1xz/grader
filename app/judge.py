import datetime
import json
import logging
import optparse
import os
import time
import traceback
from urllib.parse import urlparse

from parsing_grade import parsing_gradedata
from parsing_grade import STATUS_WFN

import requests
from flask import jsonify

from app import UPLOAD_FOLDER
from instructor_grade import instructor_grade_lab

import InstructorLogging
# logger = InstructorLogging.InstructorLogging("./tmp/instructor.log")


logger = logging.getLogger(__name__)


def download_file(link, ext=None):
    try:
        my_file = requests.get(link)
        file_path = '{}/{}'.format(UPLOAD_FOLDER, os.path.basename(link))
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        open(file_path, 'wb').write(my_file.content)
        return file_path
    except:
        logger.debug(traceback.format_exc())
        return None


if __name__ == '__main__':
    parser = optparse.OptionParser()

    parser.add_option('--id', help='id', type='string', default='PTIT')
    parser.add_option('--server', help='id', type='string', default='http://127.0.0.1:8000')
    parser.add_option('--key', help='key', type='string', default=None)
    opts, args = parser.parse_args()

    judge_id = opts.id
    judge_key = opts.key
    server = opts.server
    i = 0
    while True:
        date_license = datetime.date(2042, 5, 25)
        date_now = datetime.datetime.now().date()
        if date_now > date_license:
            time.sleep(20)
            continue
        headers = {
            'User-Agent': 'JUDGE ONLINE',
            'Connection': 'close',
            'Judge-Id': judge_id,
            'Judge-Key': judge_key,
        }
        print(server)
        try:
            r = requests.get('{}/api/submission'.format(server), headers=headers)
            text = r.text
        except:
            continue
        print(text)
        # text = '{"code":0,"solution":{"id":3082,"question_id":2907,"question_code":"nmap-ssh","upload_file_name":"longnt.B18DCAT146_at_stu.ptit.edu.vn.nmap-ssh.lab"}}'

        res_json = json.loads(text)
        if (res_json.get('code', -1) == 0):
            solution = res_json.get('solution', {})
            if solution is not None:
                username = solution.get('username', None)
                my_file = requests.get('{}/api/submission/{}'.format(server, solution.get('id')))
                if my_file == 404:
                    continue
                filepath = '{}/{}'.format(UPLOAD_FOLDER, os.path.basename(solution.get('upload_file_name')))
                directory = os.path.dirname(filepath)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                open(filepath, 'wb').write(my_file.content)

                wrong_file = False
                # resp = instructor_grade_lab(filepath)
                try:
                    resp = instructor_grade_lab(filepath)
                except:
                    print("An exception occurred for instructor_grade_lab(filepath)")
                    resp = 'An exception occurred'

                # score = dict()
                # for jtem in resp:
                #     sv = resp[jtem]
                #     temp = jtem.split('.')
                #     score['Student email '] = jtem.replace("." + temp[-1], "")
                #     score['Lab name'] = temp[-1]
                #     score['Score'] = "%.1f" % 0
                #     score['Note'] = ''
                #     if sv['actualwatermark'] != sv['expectedwatermark']:
                #         score['Note'] = 'copy from other!'
                #     else:
                #         # Cham diem
                #         sv_grades = sv['grades']
                #         sum = 0
                #         for item in sv_grades:
                #             if type(sv_grades[item]) == bool:
                #                 if sv_grades[item] == True:
                #                     sum += 1
                #             else:
                #                 if type(sv_grades[item]) == int:
                #                     if sv_grades[item] > 0:
                #                         sum += 1
                #         sv_score = "%.1f" % round(10 * sum / len(sv_grades), 1)
                #         score['Score'] = sv_score

                print(username)
                # check liệu có upload nhầm file không?
                question_code = solution.get('question_code') + '.lab'
                upload_file_name = solution.get('upload_file_name')

                # logger.debug('username %s' % (username))
                # logger.debug('question_code %s' % (question_code))
                # logger.debug('upload_file_name %s' % (upload_file_name))
                # logger.error('username %s' % (username))
                # logger.error('question_code %s' % (question_code))
                # logger.error('upload_file_name %s' % (upload_file_name))

                # if not solution.get('upload_file_name').startswith(username) and not username.startswith('sinhvien'): # sinh vien la test account
                correct_filename = username + '.' + question_code
                correct_filename_lower = correct_filename.lower()
                upload_file_name_lower = upload_file_name.lower()
                # if  not upload_file_name.endswith(question_code) and not upload_file_name.startswith(username) and not username.startswith(
                #         'sinhvien'):  # sinh vien la test account
                if correct_filename_lower != upload_file_name_lower:
                    resp = 'wrong_student_or_wrong_filename'
                    logger.error('wrong_student_or_wrong_filename %s != %s' % (correct_filename_lower, upload_file_name_lower))
                    # print('upload_file_name = ', upload_file_name)
                    # correct_filename = username + '.' + question_code
                    detail_result = '[{"output": "", "input_file": "Current upload file is ' + upload_file_name + '. Need filename like ' + correct_filename + '" , "status": '+ str(STATUS_WFN) + '}]' # Ma loi 4: sai ten file
                else:
                    detail_result = parsing_gradedata(resp)

                report = {
                    'submission-id': solution.get('id'),
                    'result': resp,
                    'score': 0,
                    'detail': detail_result
                }

                print(report)
                try:
                    requests.post('{}/api/submission_report'.format(server), json=report,
                                  headers=headers)
                except Exception:
                    traceback.print_exc()
            else:
                if i == 60:
                    # print(text)
                    i = 0
        i = i + 1
        time.sleep(10)
