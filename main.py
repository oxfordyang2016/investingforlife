# from werkzeug.utils import secure_filename
import re
from flask import Flask, flash, request, redirect, render_template
import urllib.request
import os
from flask import Flask


UPLOAD_FOLDER = './files'

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
#import magic
# from app import app

ALLOWED_EXTENSIONS = set(['txt','json', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

# http://einverne.github.io/post/2017/07/flask-upload-files.html
def secure_filename(filename):
    """
    确保文件名不包含 / -
    :param filename:
    :return:
    """
    filename = re.sub('[" "\/\--]+', '-', filename)
    filename = re.sub(r':-', ':', filename)
    filename = re.sub(r'^-|-$', '', filename)
    return filename



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def upload_form():
    return render_template('upload.html')


@app.route('/', methods=['POST'])
def upload_file():
    if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            print(file.filename)
            if file.filename == '':
                flash('No file selected for uploading')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                print(filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                flash('File successfully uploaded')
                return redirect('/')
            else:
                flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif,json')
                return redirect(request.url)



# @app.route('/finance/uploadfile', methods=['POST'])
# def upload_file():
#     if request.method == 'POST':
#             # check if the post request has the file part
#         if 'file' not in request.files:
#             flash('No file part')
#             return "ok"
#         file = request.files['file']
#         print(file.filename)
#         if file.filename == '':
#             flash('No file selected for uploading')
#             return "ok1"
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             print(filename)
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             flash('File successfully uploaded')
#             return "ok2"
#         else:
#             flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif,json')
#             return "ok3"




if __name__ == "__main__":
    app.run()
