from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def presentation():
    return render_template("index.html")

@app.route("/demo")
def demo():
    return "Python code is running!"

if __name__ == "__main__":
    app.run(debug=True)