# server_table_nysdos.py
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy import func, desc, asc, String, Text
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

# 258200


class Notary(db.Model):
    __tablename__ = "Notaries"
    id = db.Column(db.Integer, primary_key=True)
    commission_holder_name = db.Column(db.String(255), nullable=False)
    commission_number_uid = db.Column(db.String(100), nullable=False, unique=True)
    business_name_if_available = db.Column(db.String(255))
    business_address_1_if_available = db.Column(db.String(255))
    business_address_2_if_available = db.Column(db.String(255))
    business_city_if_available = db.Column(db.String(100))
    business_state_if_available = db.Column(db.String(2))
    business_zip_if_available = db.Column(db.String(10))
    commissioned_county = db.Column(db.String(255))
    commission_type_traditional_or_electronic = db.Column(db.String(255))
    term_issue_date = db.Column(db.Date, nullable=False)
    term_expiration_date = db.Column(db.Date, nullable=False)

    def to_dict(self):
        return {
            "commission_holder_name": self.commission_holder_name.title(),
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
        }


db.create_all()


def fetch_and_insert_data():
    logging.info("*****fetch_and_insert_data function called*****")
    # specifies that each request to the API should return up to 10000 records.
    url = "https://data.ny.gov/resource/rwbv-mz6z.json?$limit=10000"
    offset = 0
    total_inserted = 0

    while True:
        logging.info(f"*****Sending request to API with offset {offset}*****")
        response = requests.get(url + f"&$offset={offset}")
        data = json.loads(response.text)

        if not data:
            break

        logging.info(f"*****Received {len(data)} records from API*****")

        for item in data:
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

    # search filter explanation: When a search request is made, it checks if there is a `search` parameter in the request arguments. If there is, it filters the `Notary` query to only include records where the `commission_holder_name` or `commission_number_uid` fields contain the search term.
    search = request.args.get("search")
    if search:
        query = query.filter(
            db.or_(
                Notary.commission_holder_name.ilike(f"%{search}%"),
                Notary.commission_number_uid.ilike(f"%{search}%"),
                Notary.commission_type_traditional_or_electronic.ilike(f"%{search}%"),
            )
        )
    total = query.count()

    # sorting
    sort = request.args.get("sort")
    if sort:
        for sort_field in sort.split(","):
            direction = asc if sort_field.startswith("+") else desc
            field_name = sort_field[1:]
            column = getattr(Notary, field_name, None)
            if column is not None:
                if isinstance(column.type, (String, Text)):
                    query = query.order_by(direction(func.lower(column)))
                else:
                    query = query.order_by(direction(column))
    # if sort:
    #     order = []
    #     for s in sort.split(","):
    #         direction = s[0]
    #         name = s[1:]
    #         if name not in [
    #             "commission_holder_name",
    #             "commission_number_uid",
    #             "commissioned_county",
    #             "commission_type_traditional_or_electronic",
    #             "term_issue_date",
    #             "term_expiration_date",
    #         ]:
    #             name = "commission_holder_name"
    #         col = getattr(Notary, name)
    #         col = func.lower(col)  # convert to lowercase before sorting
    #         if direction == "-":
    #             col = col.desc()
    #         order.append(col)
    #     if order:
    #         query = query.order_by(*order)

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
