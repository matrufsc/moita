import config
import boto
import boto.exception
import boto.s3.bucket as s3bucket
import boto.s3.key as s3key
import flask
import json

app = flask.Flask(__name__)
app.config.from_object(config)

routes = flask.Blueprint('moita', __name__)

s3 = boto.connect_s3()


def make_key(filename: str) -> str:
    return '%s.json' % (filename,)


def download(bucket: s3bucket.Bucket, filename: str) -> str:
    key = bucket.get_key(make_key(filename))

    if key is not None:
        filedata = key.get_contents_as_string()
        return json.loads(filedata.decode('utf-8'))

    return None


def upload(bucket: s3bucket.Bucket, filename: str, filedata) -> s3key.Key:
    key = s3key.Key(bucket)
    key.key = make_key(filename)
    key.set_contents_from_string(json.dumps(filedata), headers={
        'Content-Type': 'application/json',
    })
    return key


@app.before_request
def before_request():
    flask.g.bucket = s3.get_bucket(app.config['AWS_BUCKET_NAME'])


@routes.route('/load/<identifier>', methods=['GET'])
def load_timetable(identifier) -> (str, int):
    payload = download(flask.g.bucket, identifier)

    if payload is None:
        flask.abort(404)

    return flask.jsonify(**payload), 200


@routes.route('/store/<identifier>', methods=['PUT'])
def store_timetable(identifier) -> (str, int):
    data = flask.request.form.to_dict()
    upload(flask.g.bucket, identifier, data)

    return '', 204


def create_app(**kwargs) -> flask.Flask:
    app.config.update(kwargs)
    app.register_blueprint(routes,
                           url_prefix=app.config.get('APPLICATION_ROOT'))
    return app


if __name__ == '__main__':  # pragma: no cover
    app = create_app()
    app.run()
