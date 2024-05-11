# flask-gridjs
Render beautiful tables in your Flask templates with grid.js

![Table Example](table.gif)

tutorial that covers this repository is located [here](https://blog.miguelgrinberg.com/post/beautiful-flask-tables-part-2)

## my notes

steps to install and run this application

1. create a virtual environment in the project folder:

`python3 -m venv venv`

2. activate the virtual environment:

`source venv/bin/activate`

3.  Once the virtual environment is activated, you can install the requirements using pip:

`pip install -r requirements.txt`

4.  To work with fake data for any of the tables you can run the command below which will create 100 users: 

`python create_fake_users.py 100`

## Explanation of the Server Driven Table approach 

### server_table.py

```
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    age = db.Column(db.Integer, index=True)
    address = db.Column(db.String(256))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'address': self.address,
            'phone': self.phone,
            'email': self.email
        }


db.create_all()


@app.route('/')
def index():
    return render_template('server_table.html')


@app.route('/api/data')
def data():
    query = User.query

    # search filter
    search = request.args.get('search')
    if search:
        query = query.filter(db.or_(
            User.name.like(f'%{search}%'),
            User.email.like(f'%{search}%')
        ))
    total = query.count()

    # sorting
    sort = request.args.get('sort')
    if sort:
        order = []
        for s in sort.split(','):
            direction = s[0]
            name = s[1:]
            if name not in ['name', 'age', 'email']:
                name = 'name'
            col = getattr(User, name)
            if direction == '-':
                col = col.desc()
            order.append(col)
        if order:
            query = query.order_by(*order)

    # pagination
    start = request.args.get('start', type=int, default=-1)
    length = request.args.get('length', type=int, default=-1)
    if start != -1 and length != -1:
        query = query.offset(start).limit(length)

    # response
    return {
        'data': [user.to_dict() for user in query],
        'total': total,
    }


if __name__ == '__main__':
    app.run()
```

### server_table.py - explained in depth

1. The script begins by importing necessary modules: `Flask` for creating the web application, `render_template` for rendering HTML files, and `request` for handling HTTP requests. `SQLAlchemy` is imported for handling database operations.

```
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
```

---

2. An instance of the `Flask` class is created and named `app`. This instance will be used to handle all the requests.

```
app = Flask(__name__)
```

---

3. The `app` instance is configured to use an SQLite database named `db.sqlite` and to disable SQLAlchemy's event system.

```
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
```

---

4. An instance of the `SQLAlchemy` class is created and named `db`. This instance will be used to interact with the database.

```
db = SQLAlchemy(app)
```

---

5. A `User` class is defined as a subclass of `db.Model`. This class represents the `User` table in the database. Each attribute of the `User` class represents a column in the table.

- `class User(db.Model):` defines a new class `User` that inherits from `db.Model` which is a base class for all models from Flask-SQLAlchemy that includes methods for querying the database.
- `id = db.Column(db.Integer, primary_key=True)` defines a column `id` in the `User` table,  `db.Integer` specifies that the data type of this column is 'Integer' and `primary_key=True` indicates that this column is the primary key of the table.
- `name = db.Column(db.String(64), index=True)` defines a column `name` with data type String of maximum length 64 and `index=True` means that an index will be created for this column, which can speed up queries that filter this column.
- `age = db.Column(db.Integer, index=True)` defines a column `age` with data type Integer. An index will be created for this column as well.
- `address = db.Column(db.String(256))` defines a column `address` with data type String of maximum length 256.
- `phone = db.Column(db.String(20))` defines a column `phone` with data type String of maximum length 20.
- `email = db.Column(db.String(120))` defines a column email with data type String of maximum length 120.
- Finally, the `to_dict` method converts a `User` object into a dictionary. This can be useful when you want to serialize a `User` object into a format that can be easily converted to JSON, for example when sending data to a client over HTTP.

```
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    age = db.Column(db.Integer, index=True)
    address = db.Column(db.String(256))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'address': self.address,
            'phone': self.phone,
            'email': self.email
        }
```

---

6. The `db.create_all()` function is called to create all tables in the database.


```
db.create_all()
```

---

7. The `index` function is defined to handle requests to the root URL (`/`). It returns the rendered `server_table.html` template.  Also, `@app.route('/')` is a decorator that binds the root URL (`http://<your-domain>/`) to the `index` function. When a client sends a GET request to the root URL, Flask will call the `index` function. This function renders the `server_table.html` template and returns it as an HTML response.

```
@app.route('/')
def index():
    return render_template('server_table.html')
```

---

8. The `data` function is defined to handle requests to the `/api/data` URL. This function queries the `User` table, applies filters, sorting, and pagination based on the request parameters, and returns the data as a JSON object.  Also, `@app.route('/api/data')` is a decorator that binds the `/api/data` URL (`http://<your-domain>/api/data`) to the `data` function. When a client sends a GET request to this URL, Flask will call the `data` function. This function queries the `User` table in the SQLite database, applies filters, sorting, and pagination based on the request parameters, and returns the data as a JSON response.

- `@app.route('/api/data') def data():` is a route decorator in Flask which instructs Flask to call the function `data()` when a client requests the `/api/data` URL.
- `query = User.query` initializes a SQLAlchemy Query object that will be used to query the `User` table in the database.
- `search = request.args.get('search')` gets the 'search' parameter from the request's query string.  A ternary expression follows where if a 'search' parameter is provided then it filters the query to only include `User` records where the 'name' or 'email' fields contain the 'search' string.
- `total = query.count()` counts the total number of records that match the query.
- `sort = request.args.get('sort')` gets the 'sort' parameter from the request's query string. A ternary expression follows where if a 'sort' parameter is provided, it splits the parameter by commas and iterates over each item. Each item is expected to be a field name optionally prefixed with a '-' for descending order. The query is then ordered by these fields.
- `start = request.args.get('start', type=int, default=-1)` gets the 'start' parameter from the request's query string. 
- `length = request.args.get('length', type=int, default=-1)` gets the 'length' parameters from the request's query string. 
- `if start != -1 and length != -1: query = query.offset(start).limit(length)` if both 'start' and 'length' parameters are provided, it applies pagination to the query.
- `return {'data': [user.to_dict() for user in query], 'total': total,}` executes the query, converts each `User` record to a dictionary using the `to_dict()` method, and returns a JSON response containing the list of user dictionaries and the total count of matching records.

```
@app.route('/api/data')
def data():
    query = User.query

    # search filter
    search = request.args.get('search')
    if search:
        query = query.filter(db.or_(
            User.name.like(f'%{search}%'),
            User.email.like(f'%{search}%')
        ))
    total = query.count()

    # sorting
    sort = request.args.get('sort')
    if sort:
        order = []
        for s in sort.split(','):
            direction = s[0]
            name = s[1:]
            if name not in ['name', 'age', 'email']:
                name = 'name'
            col = getattr(User, name)
            if direction == '-':
                col = col.desc()
            order.append(col)
        if order:
            query = query.order_by(*order)

    # pagination
    start = request.args.get('start', type=int, default=-1)
    length = request.args.get('length', type=int, default=-1)
    if start != -1 and length != -1:
        query = query.offset(start).limit(length)

    # response
    return {
        'data': [user.to_dict() for user in query],
        'total': total,
    }
```

---

9. The script checks if it is being run directly (not imported as a module) and if so, it starts the Flask development server.

```
if __name__ == '__main__':
    app.run()
```

#### Overview and use case example:

When the user first loads the page, the `index()` function is called due to the `@app.route('/')` decorator. This function renders the `server_table.html` template and returns it as an HTML response. This HTML page contains a table that is populated with data from the `/api/data` endpoint.

If the user sorts the table by 'age', a GET request is sent to the `/api/data` endpoint with a 'sort' parameter in the query string. The value of this parameter would be 'age' for ascending order or '-age' for descending order.

The `data()` function is called due to the `@app.route('/api/data')` decorator which handles the GET request by: 
1. creating a SQLAlchemy Query object that will be used to query the `User` table in the database, 
2. checking if a 'search' parameter is provided in the request's query string (if provided, it filters the query to only include `User` records where the 'name' or 'email' fields contain the 'search' string), 
3. checking if a 'sort' parameter is provided in the request's query string (if provided, it splits the parameter by commas and iterates over each item which is expected to be a field name optionally prefixed with a '-' for descending order and the query is then ordered by these fields), 
4. checking if both 'start' and 'length' parameters are provided in the request's query string (if provided, it applies pagination to the query), and 
5. executing the query by converting each `User` record to a dictionary using the `to_dict()` method that returns a JSON response containing the list of user dictionaries and the total count of matching records.

This JSON response is then used to update the table on the HTML page. The table is sorted by 'age' as per the user's action.

---

### server_table.html:

```
<html>
  <head>
    <title>Server-Driven Table</title>
    <link href="https://unpkg.com/gridjs/dist/theme/mermaid.min.css" rel="stylesheet" />
    <style>
      body {
        font-family: Sans-Serif;
      }
    </style>
  </head>
  <body>
    <div>
      <h1>Server-Driven Table</h1>
      <hr>
      <div id="table"></div>
    </div>
    <script src="https://unpkg.com/gridjs/dist/gridjs.umd.js"></script>
    <script>
      const updateUrl = (prev, query) => {
        return prev + (prev.indexOf('?') >= 0 ? '&' : '?') + new URLSearchParams(query).toString();
      };

      new gridjs.Grid({
        columns: [
          { id: 'name', name: 'Name' },
          { id: 'age', name: 'Age' },
          { id: 'address', name: 'Address', sort: false },
          { id: 'phone', name: 'Phone Number', sort: false },
          { id: 'email', name: 'Email', formatter: (cell, row) => {
            return gridjs.html('<a href="mailto:' + cell + '">' + cell + '</a>');
          }},
        ],
        server: {
          url: '/api/data',
          then: results => results.data,
          total: results => results.total,
        },
        search: {
          enabled: true,
          server: {
            url: (prev, search) => {
              return updateUrl(prev, {search});
            },
          },
        },
        sort: {
          enabled: true,
          multiColumn: true,
          server: {
            url: (prev, columns) => {
              const columnIds = ['name', 'age', 'address', 'phone', 'email'];
              const sort = columns.map(col => (col.direction === 1 ? '+' : '-') + columnIds[col.index]);
              return updateUrl(prev, {sort});
            },
          },
        },
        pagination: {
          enabled: true,
          server: {
            url: (prev, page, limit) => {
              return updateUrl(prev, {start: page * limit, length: limit});
            },
          },
        },
      }).render(document.getElementById('table'));
    </script>
  </body>
</html>

```
 
 ### server_table.html explained in depth:

1. The HTML file starts with the standard HTML tags. The `head` section includes a title for the webpage, a link to the CSS file for the Grid.js library, and some custom CSS styles.

 ```
<html>
  <head>
    <title>Server-Driven Table</title>
    <link href="https://unpkg.com/gridjs/dist/theme/mermaid.min.css" rel="stylesheet" />
    <style>
      body {
        font-family: Sans-Serif;
      }
    </style>
  </head>
  ...
</html>

 ```

---

2. The `body` section contains a `div` element with a heading and another `div` where the table will be inserted.

```
<body>
    <div>
      <h1>Server-Driven Table</h1>
      <hr>
      <div id="table"></div>
    </div>
    ...
  </body>
```

---

3. The Grid.js library is included using a `script` tag another `script` tag contains JavaScript code that initializes a new Grid.js table. The table is configured with columns, server-side data fetching, search, sort, and pagination functionalities.
- `const updateUrl = (prev, query) => {...}`: is a function declaration for `updateUrl` which takes two parameters: `prev`, which is the previous URL, and `query`, which is an object containing the query parameters to be added to the URL. 
- `return prev + (prev.indexOf('?') >= 0 ? '&' : '?') + new URLSearchParams(query).toString();` The `updateUrl` function returns a new URL with the query parameters added. Also, if the previous URL already contains query parameters (i.e., it contains a '?'), the new parameters are appended with an '&'. Otherwise, they are appended with a '?'.
- `new gridjs.Grid({...}).render(document.getElementById('table'));:` creates a new instance of a Grid.js grid and renders it in the HTML element with the id 'table'. The configuration for the grid is passed as an object to the `Grid` constructor.    
- `columns: [...]` is an array of objects that define the columns of the grid. Each object has an `id` (used for sorting and other operations), a `name` (displayed as the column header), and optionally a `sort` property (if false, disables sorting for that column) and a `formatter` function (used to customize how the data in the column is displayed).
- `server: {...}` is an object that configures the server-side processing of the grid. The `url` property is the endpoint that the grid will fetch data from. The `then` function is used to extract the array of data rows from the server response. The `total` function is used to extract the total number of rows from the server response.
- `search: {...}` is an object that configures the server-side search functionality of the grid. If `enabled` is true, a search input is displayed above the grid. The `server.url` function is used to update the server URL when a search is performed.
- `sort: {...}` is an object that configures the server-side sorting functionality of the grid. If `enabled` is true, the columns can be clicked to sort the data. The `server.url` function is used to update the server URL when a column is sorted.
- `pagination: {...}` is an object that configures the server-side pagination functionality of the grid. If `enabled` is true, a pagination control is displayed below the grid. The `server.url` function is used to update the server URL when the page is changed.

In the context of the application as a whole, this script tag code is responsible for creating and configuring the Grid.js grid that displays the data. It sets up the grid to fetch, search, sort, and paginate the data on the server side, using the `/api/data` endpoint defined in the Flask application. The `updateUrl` function is used to add the appropriate query parameters to the server URL for these operations.

```
<body>
    ...
    <script src="https://unpkg.com/gridjs/dist/gridjs.umd.js"></script>
    <script>
      const updateUrl = (prev, query) => {
        return prev + (prev.indexOf('?') >= 0 ? '&' : '?') + new URLSearchParams(query).toString();
      };

      new gridjs.Grid({
        columns: [
          { id: 'name', name: 'Name' },
          { id: 'age', name: 'Age' },
          { id: 'address', name: 'Address', sort: false },
          { id: 'phone', name: 'Phone Number', sort: false },
          { id: 'email', name: 'Email', formatter: (cell, row) => {
            return gridjs.html('<a href="mailto:' + cell + '">' + cell + '</a>');
          }},
        ],
        server: {
          url: '/api/data',
          then: results => results.data,
          total: results => results.total,
        },
        search: {
          enabled: true,
          server: {
            url: (prev, search) => {
              return updateUrl(prev, {search});
            },
          },
        },
        sort: {
          enabled: true,
          multiColumn: true,
          server: {
            url: (prev, columns) => {
              const columnIds = ['name', 'age', 'address', 'phone', 'email'];
              const sort = columns.map(col => (col.direction === 1 ? '+' : '-') + columnIds[col.index]);
              return updateUrl(prev, {sort});
            },
          },
        },
        pagination: {
          enabled: true,
          server: {
            url: (prev, page, limit) => {
              return updateUrl(prev, {start: page * limit, length: limit});
            },
          },
        },
      }).render(document.getElementById('table'));
    </script>
  </body>
```

---

1. The `updateUrl` function is used to update the URL for server-side operations based on the current state of the table (search, sort, and pagination).

```
<body>
    ...
    <script>
      const updateUrl = (prev, query) => {
        return prev + (prev.indexOf('?') >= 0 ? '&' : '?') + new URLSearchParams(query).toString();
      };
    ...
    </script>
  </body>
```

---

5. The `gridjs.Grid` function is called to create a new table. The table is configured with column definitions, server-side data fetching, search, sort, and pagination.

```
<body>
    ...
    <script>
        new gridjs.Grid({
            columns: [
                { id: 'name', name: 'Name' },
                { id: 'age', name: 'Age' },
                { id: 'address', name: 'Address', sort: false },
                { id: 'phone', name: 'Phone Number', sort: false },
                { id: 'email', name: 'Email', formatter: (cell, row) => {
                    return gridjs.html('<a href="mailto:' + cell + '">' + cell + '</a>');
                }},
            ],
            server: {
                url: '/api/data',
                then: results => results.data,
                total: results => results.total,
            },
            search: {
                enabled: true,
                server: {
                    url: (prev, search) => {
                        return updateUrl(prev, {search});
                    },
                },
            },
            sort: {
                enabled: true,
                multiColumn: true,
                server: {
                    url: (prev, columns) => {
                    const columnIds = ['name', 'age', 'address', 'phone', 'email'];
                    const sort = columns.map(col => (col.direction === 1 ? '+' : '-') + columnIds[col.index]);
                    return updateUrl(prev, {sort});
                    },
                },
            },
            pagination: {
                enabled: true,
                server: {
                    url: (prev, page, limit) => {
                    return updateUrl(prev, {start: page * limit, length: limit});
                    },
                },
            },
        }).render(document.getElementById('table'));
    </script>
</body>
```

---

6. The `render` method is called to insert the table into the `div` with the id `table`.

```
<body>
    ...
    <script>
      new gridjs.Grid({
        ...
      }).render(document.getElementById('table'));
    </script>
</body>
```

---

## explanation of the fetch_and_insert_data function

```
# This is the definition of the function that fetches and inserts the data.
def fetch_and_insert_data():
    # This is the URL of the API endpoint. The $limit=50000 part is a query parameter that limits the number of records returned in each request to 50000.
    url = "https://data.ny.gov/resource/rwbv-mz6z.json?$limit=50000"
    # This is a variable that keeps track of the number of records that have been fetched so far.
    offset = 0
    # This is an infinite loop that keeps running until it's explicitly broken. Inside the loop, a request is made to the API endpoint with the current offset value. The response is then parsed as JSON, and if there are no records in the response, the loop is broken. Otherwise, each record is processed and inserted into the database as a Notary object.
    total_inserted = 0


    while True:
        # This line sends a GET request to the API endpoint, with the current offset as a query parameter.
        response = requests.get(url + f"&$offset={offset}")
        # This line parses the JSON response from the API into a Python list of dictionaries.
        data = json.loads(response.text)
        # If the API returns an empty list (which means there are no more records to fetch), the loop is broken and the function ends.
        if not data:
            break
        # This is a loop that iterates over each record in the data.
        for item in data:
            # This line creates a new instance of the `Notary` class, using the data from the current record. The `item.get('field_name')` calls are used to safely get the value of each field from the record. The datetime.strptime function is used to parse the date strings into datetime objects.
            notary = Notary(
                commission_holder_name=item.get("commission_holder_name"),
                commission_number_uid=item.get("commission_number_uid"),
                business_name_if_available=item.get("business_name_if_available"),
                business_address_1_if_available=item.get(
                    "business_address_1_if_available"
                ),
                business_address_2_if_available=item.get(
                    "business_address_2_if_available"
                ),
                business_city_if_available=item.get("business_city_if_available"),
                business_state_if_available=item.get("business_state_if_available"),
                business_zip_if_available=item.get("business_zip_if_available"),
                commissioned_county=item.get("commissioned_county"),
                commission_type_traditional_or_electronic=item.get(
                    "commission_type_traditional_or_electronic"
                ),
                term_issue_date=datetime.strptime(
                    item.get("term_issue_date"), "%Y-%m-%dT%H:%M:%S.%f"
                ),
                term_expiration_date=datetime.strptime(
                    item.get("term_expiration_date"), "%Y-%m-%dT%H:%M:%S.%f"
                ),
                georeference=item.get("georeference"),
            )
            # This line adds the new Notary instance to the database session. This doesn't actually insert the record into the database yet, it just stages it for insertion.
            db.session.add(notary)
        # This line commits the database session, which inserts all staged records into the database.
        db.session.commit()
        # This line increments the offset by 50000, so that the next API request will fetch the next batch of records.
        offset += 50000
```

## old version of server_table_nysdos.py that works without georeference and ENUM functions:

```
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension

# from sqlalchemy.dialects.postgresql import ENUM
# from geoalchemy2 import Geometry
# from geoalchemy2.functions import ST_MakePoint
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

import requests
import json
import logging
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://haus:Laylacharlie22!@localhost/nysdos_notaries_test"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "count_duckula"
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

toolbar = DebugToolbarExtension(app)

db = SQLAlchemy(app)

logging.basicConfig(level=logging.INFO)


# commission_type = ENUM("Traditional", "Electronic", name="commission_type")

# new_york_county = ENUM(
#     "Albany",
#     "Allegany",
#     "Bronx",
#     "Broome",
#     "Cattaraugus",
#     "Cayuga",
#     "Chautauqua",
#     "Chemung",
#     "Chenango",
#     "Clinton",
#     "Columbia",
#     "Cortland",
#     "Delaware",
#     "Dutchess",
#     "Erie",
#     "Essex",
#     "Franklin",
#     "Fulton",
#     "Genesee",
#     "Greene",
#     "Hamilton",
#     "Herkimer",
#     "Jefferson",
#     "Kings (Brooklyn)",
#     "Lewis",
#     "Livingston",
#     "Madison",
#     "Monroe",
#     "Montgomery",
#     "Nassau",
#     "New York (Manhattan)",
#     "Niagara",
#     "Oneida",
#     "Onondaga",
#     "Ontario",
#     "Orange",
#     "Orleans",
#     "Oswego",
#     "Otsego",
#     "Putnam", "Queens",
#     "Rensselaer",
#     "Richmond (Staten Island)",
#     "Rockland",
#     "Saint Lawrence",
#     "Saratoga",
#     "Schenectady",
#     "Schoharie",
#     "Schuyler",
#     "Seneca",
#     "Steuben",
#     "Suffolk",
#     "Sullivan",
#     "Tioga",
#     "Tompkins",
#     "Ulster",
#     "Warren",
#     "Washington",
#     "Wayne",
#     "Westchester",
#     "Wyoming",
#     "Yates",
#     name="new_york_county",
# )

# state = ENUM(
#     "AL",
#     "AK",
#     "AZ",
#     "AR",
#     "CA",
#     "CO",
#     "CT",
#     "DE",
#     "DC",
#     "FL",
#     "GA",
#     "GU",
#     "HI",
#     "ID",
#     "IL",
#     "IN",
#     "IA",
#     "KS",
#     "KY",
#     "LA",
#     "ME",
#     "MD",
#     "MA",
#     "MI",
#     "MN",
#     "MS",
#     "MO",
#     "MT",
#     "NE",
#     "NV",
#     "NH",
#     "NJ",
#     "NM",
#     "NY",
#     "NC",
#     "ND",
#     "OH",
#     "OK",
#     "OR",
#     "PA",
#     "PR",
#     "RI",
#     "SC",
#     "SD",
#     "TN",
#     "TX",
#     "UT",
#     "VT",
#     "VA",
#     "VI",
#     "WA",
#     "WV",
#     "WI",
#     "WY",
#     name="state",
# )


class Notary(db.Model):
    __tablename__ = "Notaries"
    id = db.Column(db.Integer, primary_key=True)
    commission_holder_name = db.Column(db.String(255), nullable=False)
    commission_number_uid = db.Column(db.String(100), nullable=False, unique=True)
    business_name_if_available = db.Column(db.String(255))
    business_address_1_if_available = db.Column(db.String(255))
    business_address_2_if_available = db.Column(db.String(255))
    business_city_if_available = db.Column(db.String(100))
    # business_state_if_available = db.Column(state)
    business_state_if_available = db.Column(
        db.String(2)
    )  # Changed to db.String because ENUM was causing issues
    business_zip_if_available = db.Column(db.String(10))
    # commissioned_county = db.Column(new_york_county, nullable=False)
    commissioned_county = db.Column(
        db.String(255)
    )  # Changed to db.String because ENUM was causing issues
    # commission_type_traditional_or_electronic = db.Column(
    #     commission_type, nullable=False
    # )
    commission_type_traditional_or_electronic = db.Column(
        db.String(255)
    )  # Changed to db.String because ENUM was causing issues
    term_issue_date = db.Column(db.Date, nullable=False)
    term_expiration_date = db.Column(db.Date, nullable=False)
    # georeference = db.Column(Geometry('POINT'))

    def to_dict(self):
        return {
            "commission_holder_name": self.commission_holder_name,
            "commission_number_uid": self.commission_number_uid,
            "business_name_if_available": self.business_name_if_available,
            "business_address_1_if_available": self.business_address_1_if_available,
            "business_address_2_if_available": self.business_address_2_if_available,
            "business_city_if_available": self.business_city_if_available,
            "business_state_if_available": self.business_state_if_available,
            "business_zip_if_available": self.business_zip_if_available,
            "commissioned_county": self.commissioned_county,
            "commission_type_traditional_or_electronic": self.commission_type_traditional_or_electronic,
            "term_issue_date": self.term_issue_date,
            "term_expiration_date": self.term_expiration_date,
            # "georeference": self.georeference,
        }


db.create_all()


def fetch_and_insert_data():
    logging.info("*****fetch_and_insert_data function called*****")
    url = "https://data.ny.gov/resource/rwbv-mz6z.json?$limit=6000"
    offset = 0
    total_inserted = 0

    while True:
        logging.info(f"*****Sending request to API with offset {offset}*****")
        response = requests.get(url + f"&$offset={offset}")
        data = json.loads(response.text)

        # Print the response text
        # print(response.text)
        # print(f"********")

        data = json.loads(response.text)

        # Print the parsed JSON data
        # print(data)

        if not data:
            break

        logging.info(f"*****Received {len(data)} records from API*****")

        for item in data:
            # georeference = item.get("georeference")
            # if georeference:
            #     # Extract the coordinates from the georeference object
            #     longitude, latitude = georeference['coordinates']
            #     # Create a geometry object from the coordinates
            #     georeference = ST_MakePoint(longitude, latitude)
            commission_number_uid = item.get("commission_number_uid")
            existing_record = Notary.query.filter_by(
                commission_number_uid=commission_number_uid
            ).first()

            if existing_record is None:
                notary = Notary(
                    commission_holder_name=item.get("commission_holder_name"),
                    commission_number_uid=item.get("commission_number_uid"),
                    business_name_if_available=item.get("business_name_if_available"),
                    business_address_1_if_available=item.get(
                        "business_address_1_if_available"
                    ),
                    business_address_2_if_available=item.get(
                        "business_address_2_if_available"
                    ),
                    business_city_if_available=item.get("business_city_if_available"),
                    business_state_if_available=item.get("business_state_if_available"),
                    business_zip_if_available=item.get("business_zip_if_available"),
                    commissioned_county=item.get("commissioned_county"),
                    commission_type_traditional_or_electronic=item.get(
                        "commission_type_traditional_or_electronic"
                    ),
                    term_issue_date=datetime.strptime(
                        item.get("term_issue_date"), "%Y-%m-%dT%H:%M:%S.%f"
                    ),
                    term_expiration_date=datetime.strptime(
                        item.get("term_expiration_date"), "%Y-%m-%dT%H:%M:%S.%f"
                    ),
                    # georeference=georeference,
                )
                db.session.add(notary)
                total_inserted += 1

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        offset += 50000

    logging.info(f"*****Inserted {total_inserted} records into the database*****")


@app.route("/")
def index():
    return render_template("server_table_nysdos.html")


@app.route("/api/data")
def data():
    query = Notary.query

    # search filter
    search = request.args.get("search")
    if search:
        query = query.filter(
            db.or_(
                Notary.commission_holder_name.like(f"%{search}%"),
                Notary.commission_number_uid.like(f"%{search}%"),
            )
        )
    total = query.count()

    # sorting
    sort = request.args.get("sort")
    if sort:
        order = []
        for s in sort.split(","):
            direction = s[0]
            name = s[1:]
            if name not in ["commission_holder_name", "commission_number_uid"]:
                name = "commission_holder_name"
            col = getattr(Notary, name)
            if direction == "-":
                col = col.desc()
            order.append(col)
        if order:
            query = query.order_by(*order)

    # pagination
    start = request.args.get("start", type=int, default=-1)
    length = request.args.get("length", type=int, default=-1)
    if start != -1 and length != -1:
        query = query.offset(start).limit(length)

    # response
    return {
        "data": [notary.to_dict() for notary in query],
        "total": total,
    }


@app.route("/fetch_data", methods=["POST"])
def fetch_data():
    logging.info("*****fetch_data route called*****")
    fetch_and_insert_data()
    logging.info("*****Data fetching completed*****")
    return {"status": "success"}


if __name__ == "__main__":
    app.run()

```

## To Do List: 

1. optimize the notaries database:
- The name field contains the notary's whole name instead of having first name, last name, middle name, etc.  I want to be able to authenticate my users by having them enter their first name, middle name, last name instead of their full name.
- I need to make sure all authentication and search functionality is NOT case sensitive.
- I should make sure querying electronic notaries versus traditional notaries is efficient.
2. refactor the html table:
- I want to have a different version of the table for principals, traditional notaries, electronic notaries and admins.
- The table can be improved on the front end by having the notary's business name and address info all in one <td> as opposed to multiple columns.  This will save space in the table but I still want to be able to sort and filter based on each field.
- The Term Issue and Expiration dates can be reformatted so instead of `Thu, 09 Jul 2020 00:00:00 GMT` and `Tue, 09 Jul 2024 00:00:00 GMT` I want to just display the dates as `7/9/2020` and `7/9/2024`.
- For now eliminate the Georeference column.
- Reformat the commission holder's name to be Title case but make sure that any search query is all lower case on both the front and back end.
- a search field above each column.  try to enable multiple search filters (e.g. filter by name AND commission county).
- The Principal table view will have additional columns/features such as:
  - a button that adds the notary to their "favorites list"
  - a button that sends them a message
  - an image representing the account profile
  - teleconference options (e.g. zoom, google meet, etc.)
  - Ratings and Reviews: You could include a rating system where principals can rate the notaries they've worked with. This could be a simple star rating or a more detailed review system. This would help other principals in choosing a notary.
  - Location: If notaries are willing to travel for in-person services, you could include their travel radius or specific areas they cover.
  - Languages Spoken: If a notary speaks multiple languages, this could be valuable information for principals who are more comfortable in a language other than English.
  - Specializations: If a notary specializes in certain types of documents or services, this could be included in the table.
  - Certifications: Any additional certifications or qualifications the notary has could be included.
  - Availability: A notary's general availability or specific time slots could be included. This could be integrated with a booking system.
  - Social Proof: Testimonials from previous clients could be included to provide social proof.
  - Contact Information: While you have a messaging system, including direct contact information such as an email or phone number could be beneficial.
  - Downloadable vCard: A button to download the notary's contact information as a vCard could be useful for principals.
  - Notary's Website or LinkedIn Profile: If the notary has a professional website or LinkedIn profile, a link could be included.