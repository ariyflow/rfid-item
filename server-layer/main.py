from flask import Flask, make_response

app = Flask(__name__)

@app.route("/")
def default_handler():
    return make_response("ok", 200) 

if __name__ == "__main__":
    app.run("127.0.0.1", port=5353, debug=True)
