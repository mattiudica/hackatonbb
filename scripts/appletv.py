import sys
import os
path = os.path.abspath('.')
sys.path.insert(1, path)
import db_conection
data = [{"name":"samu", "age":15},{"name":"facu", "age":12},{"name":"juli", "age":20}]

db_conection.insertMany(data)
