
from bson.objectid import ObjectId
from flask import Flask, request, Response
from flask_pymongo import PyMongo
from bson import json_util
from werkzeug.wrappers import response



app= Flask(__name__)
app.config["MONGO_URI"] = 'mongodb://localhost/hackaton'

mongo = PyMongo(app)

@app.route('/platforms',methods=['GET'])
def get_platforms():
    platforms = mongo.db.platforms.find()
    response = json_util.dumps(platforms)
    return Response(response,mimetype='application/json')


@app.route('/platforms/platformCode=<platformCode>',methods=['GET'])
def get_one_platform_code(platformCode):
    platform = mongo.db.platforms.find({'PlatformCode':platformCode})
    response = json_util.dumps(platform)
    return Response(response,mimetype='application/json')

@app.route('/platforms/platformCode=<platformCode>&top=<type>',methods=['GET'])
def get_platform_code_top(platformCode,type):
    platform = mongo.db.platforms.find({'PlatformCode':platformCode,
                                        'top':type})
    response = json_util.dumps(platform)
    return Response(response,mimetype='application/json')


if __name__ == "__main__":
    app.run(debug=True)