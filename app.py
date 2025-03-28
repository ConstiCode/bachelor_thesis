from flask import Flask, render_template, request
import random

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return render_template('index.html')

@app.route('/generate-test-locations', methods=['POST'])
def generate_test_locations() -> [(int, int)]:
    """Computes the number of locations and generates random locations"""

    info = request.get_json()

    number_of_shelf_columns = info.get('numAisles') # todo fix this naming issue
    number_of_rows = info.get('numCrossings')
    product_count = info.get('product_count')

    # As each shelf is 6 grids high and 2 grids wide we assume that shelf has 12 stock locations
    number_of_shelves = number_of_rows * number_of_shelf_columns
    number_of_locations = number_of_shelves * 12

    locations = [random.randint(0, number_of_locations) for _ in range(product_count)]

    return
    # Todo letzter status: versucht die locations in die grid tuples zu übertragen. Hierfür dachte ich daran im
    # frontend die obere ecke des squares für die berechnung zu nehmen. Die Koordinate der oberen ecke ist
    # (wareHouseFloorPlan.canvas.height / 2) + wareHouseFloorPlan.offset + die höhe der anderen regale und lücken

    # Todo: Überlege welche varialblen im frontend wirklich this sein müssen und welche nicht.



if __name__ == '__main__':
    app.run()
