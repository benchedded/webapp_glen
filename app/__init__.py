from flask import Flask, render_template, request, redirect, url_for # type: ignore

import shelve


app = Flask(__name__)
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/resources')
def resources():
    return render_template('resources.html', )

@app.route('/learningModules')
def learningModules():
    return render_template('learningModules.html')


if __name__ == '__main__':
    app.run(debug=True)
