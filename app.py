from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return render_template('index.html')

@app.route('/generate-picking', methods=['POST'])
def generate_picking():
    # todo decide if this should be triggered over js with context
    product_count = request.form.get('product_count')  # Get data from form submission
    return f"Processing {product_count} products"



if __name__ == '__main__':
    app.run()
