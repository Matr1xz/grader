import os
import shutil

from fastapi import File, UploadFile
from fastapi.responses import JSONResponse

from app import UPLOAD_FOLDER, app, normalize_filename
from instructor_grade import instructor_grade_lab
from parsing_grade import parsing_gradedata

ALLOWED_EXTENSIONS = {'zib', 'lab'}

is_debug = True

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.post('/file-upload')
def upload_file(file: UploadFile | None = File(default=None)):
	# check if the post request has the file part
	if file is None:
		return JSONResponse({'message': 'No file part in the request'}, status_code=400)
	filename = normalize_filename(file.filename)
	if filename == '':
		return JSONResponse({'message': 'No file selected for uploading'}, status_code=400)
	if file and allowed_file(filename):
		filepath = os.path.join(UPLOAD_FOLDER, filename)
		with open(filepath, 'wb') as buffer:
			shutil.copyfileobj(file.file, buffer)
		# resp = jsonify({'message' : 'File successfully uploaded'})
		have_exception = False
		if is_debug:
			print('bắt đầu chạy instructor_grade_lab(filepath): \n')
		try:
			ret = instructor_grade_lab(filepath)
		except Exception:
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
		return JSONResponse(ret, status_code=201)
	else:
		return JSONResponse({'message': 'Allowed file types are .zib, .lab'}, status_code=400)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=5001)
