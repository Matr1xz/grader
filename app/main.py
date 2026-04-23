import os
import urllib.request
from app import app
from flask import Flask, request, redirect, jsonify
from werkzeug.utils import secure_filename
from instructor_grade import *
from parsing_grade import parsing_gradedata

ALLOWED_EXTENSIONS = set(['zib', 'lab'])

is_debug = True

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/file-upload', methods=['POST'])
def upload_file():
	# check if the post request has the file part
	if 'file' not in request.files:
		resp = jsonify({'message' : 'No file part in the request'})
		resp.status_code = 400
		return resp
	file = request.files['file']
	if file.filename == '':
		resp = jsonify({'message' : 'No file selected for uploading'})
		resp.status_code = 400
		return resp
	if file and allowed_file(file.filename):
		filename = secure_filename(file.filename)
		filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
		file.save(filepath)
		# resp = jsonify({'message' : 'File successfully uploaded'})
		have_exception = False
		if is_debug:
			print('bắt đầu chạy instructor_grade_lab(filepath): \n')
		try:
			ret = instructor_grade_lab(filepath)
		except:
			print("An exception occurred for instructor_grade_lab(filepath)")
			have_exception = True
			ret = 'An exception occurred'

		# ret = json.dumps(ret)
		if is_debug:
			print('output của instructor_grade_lab(filepath): \n')
			print(ret, type(ret))
		ret = parsing_gradedata(ret)
		if is_debug:
			print('output của parsing_gradedata(ret): \n')
			print(ret)
		resp = jsonify(ret)
		resp.status_code = 201
		return resp
	else:
		resp = jsonify({'message' : 'Allowed file types are .zib, .lab'})
		resp.status_code = 400
		return resp

if __name__ == "__main__":
    app.run(port=5001)
