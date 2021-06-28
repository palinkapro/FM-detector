import os
from pathlib import Path
from flask import Flask, flash, send_from_directory, redirect, url_for,  render_template, request
import torch
from PIL import Image
import argparse
import io
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
RESULT_FOLDER = '/var/www/fmdetector/fmdetector/uploads/results'
UPLOAD_FOLDER = '/var/www/fmdetector/fmdetector/uploads'
os.environ['RESULT_FOLDER'] = '/var/www/fmdetector/fmdetector/uploads/results'
os.environ['UPLOAD_FOLDER'] = '/var/www/fmdetector/fmdetector/uploads'
os.environ['MPLCONFIGDIR'] = '/tmp/'


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(413)
def error413(e):
    flash("No file uploaded.")
    flash("Check if file size is reasonable(up to 16MB)")
    return redirect(request.url)

@app.route('/uploads/results/<path:filename>')
def download_file(filename):
    return send_from_directory(RESULT_FOLDER, filename, as_attachment=False)

@app.route('/uploads/<path:filename>')
def upload_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)


model = torch.hub.load('/var/www/fmdetector/fmdetector/yolov5', 'custom', path='/var/www/fmdetector/fmdetector/yolov5/models/best.pt', source='local')

model.eval()

def get_prediction(img):
    with Image.open(img) as img:
        imgs = [img]
        model.conf = 0.35 
        results = model(imgs, size=320) 
    return results

def predict(template):
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files.get('file')
        if not file:
            return
        if allowed_file(file.filename):
            original = secure_filename(file.filename)
            im = Image.open(file) #consider exif(no-rotation or flip
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], original)
            im.save(file_path)
            results = get_prediction(file_path)
            results.save(save_dir=Path(RESULT_FOLDER))
            predicted = os.path.splitext(original)[0] + '.jpg'
            flash("File uploaded successfully!")
            return render_template(template, original=original, predicted=predicted)
        else:
            flash("No file uploaded.")
            flash("Check if image extention is allowed('png', 'jpg', 'jpeg')") 

    return render_template(template)

@app.route('/', methods=['POST'])
def tmpl():
    return predict('index.html')

@app.route('/index_ru.html', methods=['POST'])
def tmpl_ru():
    return predict('index_ru.html')

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/index_ru.html")
def ru():
    return render_template('index_ru.html')

if __name__ == "__main__":
    app.run()

