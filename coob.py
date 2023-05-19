#!/usr/bin/env python3

import argparse
import itertools
import os
import subprocess
import sys
import tempfile


from flask import abort, Flask, flash, request, redirect, url_for, render_template, send_file
from werkzeug.utils import secure_filename


BRIGHTNESS = 100
# Add in the following once soldered:
# --led-gpio-mapping=adafruit-hat-pwm
IMAGE_PROCESS = [
    '/usr/bin/taskset',
    '-c',
    '3',
    '/usr/local/bin/led-image-viewer',
    '--led-cols=64',
    '--led-rows=64',
    '--led-chain=4',
    '--led-no-drop-privs',
    '--led-gpio-mapping=adafruit-hat-pwm',
]
DVD_PROCESS = [
    '/usr/bin/taskset',
    '-c',
    '3',
    '/root/coob/src/image-bounce.py',
    '--led-rows=64',
    '--led-cols=64',
    '--led-chain',
    '4',
    '--led-gpio-mapping=adafruit-hat-pwm',
    '--image',
    '/home/pi/dvd.png',
]
UPLOAD_FOLDER = '/root/coob/assets'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


app = Flask(__name__, static_url_path='/static', static_folder='../static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000


cube_process = None


def kill_cube_process():
    global cube_process

    if cube_process:
        cube_process.kill()

    cube_process = None


def run_cube_process(args):
    print(args)
    global cube_process

    kill_cube_process()
    cube_process = subprocess.Popen(args)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_brightness_arg(brightness):
    try:
        brightness = int(request.form.get('brightness', 100))
    except:
        brightness = 50

    if brightness < 0:
        brightness = 0
    if brightness > 100:
        brightness = 100

    return f'--led-brightness={brightness}'


@app.route('/upload', methods=['POST'])
def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return redirect('/')


@app.route('/upload', methods=['GET'])
def upload_get():
    return render_template('upload.html')


@app.route('/prepare', methods=['POST'])
def prepare_post():
    file = request.files['file']
    try:
        iterations = int(request.form.get('iterations', 0))
    except:
        flash('Invalid iterations')
        return redirect(request.url)

    if not file:
        return render_template('prepare.html')

    with tempfile.TemporaryDirectory() as temp_dir:
        filename = secure_filename(file.filename)
        local_path = os.path.join(temp_dir, filename)
        file.save(local_path)
        file.close()

        base_path, base_extension, *_ = os.path.splitext(local_path)

        if iterations:
            result_path = os.path.join(
                temp_dir,
                f'{base_path}x{iterations}{base_extension}',
            )

            command = [
                '/usr/bin/montage',
                *itertools.repeat(local_path, iterations),
                '-background',
                'none',
                '-tile',
                f'{iterations}x1',
                '-geometry',
                '+0+0',
                result_path,
            ]

            subprocess.run(
                command,
                check=True,
                timeout=300,
            )

            return send_file(result_path, as_attachment=True)

        new_path = f'{base_path}.gif'

        subprocess.run(
            ['/usr/local/bin/convert-to-gif.sh', local_path, new_path],
            check=True,
            timeout=300,
        )

        return send_file(new_path, as_attachment=True)


@app.route('/prepare', methods=['GET'])
def prepare_get():
    return render_template('prepare.html')


@app.route('/reboot', methods=['POST'])
def reboot_post():
    subprocess.run('/usr/sbin/reboot')
    return redirect('/')


@app.route('/restart', methods=['POST'])
def restart_post():
    sys.exit(0)


@app.route('/', methods=['POST'])
def index_post():
    selection = request.form.get('content_selection')
    brightness_arg = get_brightness_arg(request.form.get('brightness'))

    if not selection:
        return 'Error: no selection passed'

    if selection == 'none':
        kill_cube_process()
    elif selection == 'dvd.png':
        # clowny, I know
        dvd_process = DVD_PROCESS.copy()
        dvd_process.append(brightness_arg)
        run_cube_process(dvd_process)
    else:
        image_process = IMAGE_PROCESS.copy()
        image_process.append(brightness_arg)
        image_process.append(os.path.join(UPLOAD_FOLDER, selection))
        run_cube_process(image_process)

    return redirect('/')


@app.route('/', methods=['GET'])
def index_get():
    entries = [
        entry for entry in os.listdir(UPLOAD_FOLDER)
        if entry.lower().endswith(tuple(ALLOWED_EXTENSIONS))
    ]

    return render_template('index.html', entries=entries)


def parse_args():
    parser = argparse.ArgumentParser()

    return parser.parse_args()


def main():
    args = parse_args()
    app.run(debug=True, host='0.0.0.0', port=80)


if __name__ == '__main__':
    main()
