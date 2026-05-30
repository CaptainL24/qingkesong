from pathlib import Path
import threading
import webbrowser

from flask import Flask, render_template

app = Flask(__name__, template_folder=str(Path(__file__).resolve().parent / "templates"))


@app.route("/")
def index():
    return render_template("test.html")


@app.route("/game1")
def game1():
    return render_template("game1.html")


@app.route("/game2")
def game2():
    return render_template("game2.html")


def open_browser():
    webbrowser.open("http://127.0.0.1:5002")


if __name__ == "__main__":
    threading.Timer(1.0, open_browser).start()
    app.run(host="127.0.0.1", port=5002, debug=False, use_reloader=False)
