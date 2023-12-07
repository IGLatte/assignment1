import csv

from flask import Flask, render_template, url_for
app = Flask(__name__)


@app.route('/')
def index():
    student_name = "Yang Heyu"  # 替换为学生的姓名
    student_id = "75979"  # 替换为学生的学号
    photo_url = url_for('static', filename='yhy.jpeg')  # 替换为学生的照片 URL

    return render_template('index.html', name=student_name, id=student_id, photo_url=photo_url)
@app.route('/reviews')
def reviews():
    data = []
    with open('data/amazon-reviews.csv', 'r') as file:
        reader = csv.reader(file)
        first_row = next(reader)
        for row in reader:
            photo_row = []
            for cell in row:
                if row[0] == '1':
                    row[0] = photo_row.append(url_for('static', filename='score-1.jpg'))
                elif row[0] == '2':
                    row[0] = photo_row.append(url_for('static', filename='score-2.jpg'))
                elif row[0] == '3':
                    row[0] = photo_row.append(url_for('static', filename='score-3.jpg'))
                elif row[0] == '4':
                    row[0] = photo_row.append(url_for('static', filename='score-4.jpg'))
                elif row[0] == '5':
                    row[0] = photo_row.append(url_for('static', filename='score-5.jpg'))
                else:
                    photo_row.append(cell)
            data.append(photo_row)
    return render_template('reviews.html', data=data, review_head=first_row)

if __name__ == '__main__':
    app.run()
