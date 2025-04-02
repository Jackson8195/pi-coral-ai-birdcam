from flask import Flask

# Create a Flask application instance
app = Flask(__name__)

# Define a route for the root URL
@app.route('/')
def hello_world():
    return 'Hello, World!'

# Run the app on 0.0.0.0:5000 (accessible on all network interfaces)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)