from flask import Flask, render_template

#Write function to get ann from admin:
def check_for_ann():
    return "Welcome to the LionBase certification program!"

app = Flask(__name__)


@app.route('/homepage')
def homepage():
    ann = check_for_ann()
    return render_template('base_homepage.html', ann=ann)


if __name__ == '__main__':
    app.run()
