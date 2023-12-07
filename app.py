from flask import Flask, render_template
app = Flask(__name__)


@app.route('/')
def index():
    student_name = "John Doe"  # 替换为学生的姓名
    student_id = "123456"  # 替换为学生的学号
    photo_url = "/yh"  # 替换为学生的照片 URL

    return render_template('index.html', name=student_name, id=student_id, photo_url=photo_url)


if __name__ == '__main__':
    app.run()
