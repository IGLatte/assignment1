from flask import Flask, render_template, url_for
app = Flask(__name__)


@app.route('/')
def index():
    student_name = "Yang Heyu"  # 替换为学生的姓名
    student_id = "75979"  # 替换为学生的学号
    photo_url = url_for('static', filename='yhy.jpeg')  # 替换为学生的照片 URL

    return render_template('index.html', name=student_name, id=student_id, photo_url=photo_url)


if __name__ == '__main__':
    app.run()
