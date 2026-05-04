import os
import shutil

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

import instructor_grade

app = FastAPI()

# === CONFIG ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'tmp', 'labs')
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {'lab', 'zib'}

def _parse_bool_env(value):
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized in {'1', 'true', 'yes', 'on'}:
        return True
    if normalized in {'0', 'false', 'no', 'off'}:
        return False
    return None


def _is_production_env():
    env_name = (os.getenv('APP_ENV') or os.getenv('FLASK_ENV') or os.getenv('ENV') or '').strip().lower()
    return env_name == 'production'


def _should_cleanup_artifacts():
    # Override cleanup behavior with env var: true/false
    configured = _parse_bool_env(os.getenv('GRADE_CLEANUP_ARTIFACTS'))
    if configured is not None:
        return configured
    # Default: always cleanup to prevent disk growth.
    # Disable explicitly with GRADE_CLEANUP_ARTIFACTS=false when debugging artifacts.
    return True

# Ensure upload directories exist
for d in [UPLOAD_FOLDER]:
    os.makedirs(d, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# === ROUTES ===

# @app.route('/')
# def index():
#     """Serve the grading web UI."""
#     return render_template('index.html')

# upload file API
@app.post('/grade')
@app.post('/api/grade')
def grade_lab(file: UploadFile | None = File(default=None)):
    """
    Accepts a .lab/.zib file upload, runs the grading pipeline,
    and returns a clean JSON result for the student.
    """
    # 1. Validate file
    if file is None:
        return JSONResponse({'error': 'Không tìm thấy file trong request.'}, status_code=400)

    filename = os.path.basename(file.filename or '')

    if filename == '':
        return JSONResponse({'error': 'Chưa chọn file nào.'}, status_code=400)

    if not allowed_file(filename):
        return JSONResponse({'error': 'Định dạng không hỗ trợ. Vui lòng upload file .lab hoặc .zib'}, status_code=400)

    # 2. Save uploaded file
    filepath = os.path.join(UPLOAD_FOLDER, filename) # upload vao folder tmp/labs
    submission_key = os.path.splitext(filename)[0]

    # Remove stale artifacts for this same submission key before processing.
    instructor_grade.cleanup_submission_artifacts(BASE_DIR, submission_key)
    with open(filepath, 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if os.path.getsize(filepath) > MAX_CONTENT_LENGTH:
            return JSONResponse({'error': 'File quá lớn.'}, status_code=413)

        # 3. Run the grading pipeline
        raw_result = instructor_grade.instructor_grade_lab(filepath)

        # Handle wrong input file
        if raw_result == 'wrong_input_file':
            return JSONResponse({
                'error': f'File không hợp lệ. Không tìm thấy lab tương ứng trong hệ thống.'
            }, status_code=400)

        if raw_result == {} or raw_result is None:
            return JSONResponse({
                'error': 'Không thể chấm điểm. File có thể bị lỗi hoặc không đúng định dạng.'
            }, status_code=400)

        # 4. Build pure grading JSON from goals/tasks
        key = list(raw_result.keys())[0]
        sv_data = raw_result[key]

        grades = sv_data.get('grades', {})

        tasks = []
        completed_count = 0
        for task_name, raw_value in grades.items():
            # Skip internal keys that are not real tasks.
            if task_name.startswith('_') or task_name.startswith('cw_'):
                continue

            completed = False
            if isinstance(raw_value, bool):
                completed = raw_value
            elif isinstance(raw_value, int):
                completed = raw_value > 0

            if completed:
                completed_count += 1

            tasks.append({
                'task': task_name,
                'completed': completed
            })

        total_tasks = len(tasks)
        score = round(10 * completed_count / total_tasks, 1) if total_tasks > 0 else 0.0

        # Extract email and lab name from key
        parts = key.split('.')
        lab_name = parts[-1] if parts else 'unknown'
        email = '.'.join(parts[:-1]) if len(parts) > 1 else 'unknown'

        # Build response
        result = {
            'email': email,
            'lab_name': lab_name,
            'score': score,
            'completed_tasks': completed_count,
            'total_tasks': total_tasks,
            'tasks': tasks,
        }

        return JSONResponse(result, status_code=200)

    except Exception as e:
        return JSONResponse({
            'error': f'Lỗi khi xử lý: {str(e)}'
        }, status_code=500)

    finally:
        if _should_cleanup_artifacts():
            instructor_grade.cleanup_submission_artifacts(BASE_DIR, submission_key)

        # Clean up uploaded file
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

        try:
            file.file.close()
        except Exception:
            pass


if __name__ == '__main__':
    # Run on all interfaces so other machines can access
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=5000)
