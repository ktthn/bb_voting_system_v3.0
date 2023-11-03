import binascii
from collections import OrderedDict

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from flask import Flask, jsonify, request, render_template, redirect



class Vote:

    def __init__(self, voter_address, voter_private_key, candidate_address, choice):
        self.voter_address = voter_address
        self.voter_private_key = voter_private_key
        self.candidate_address = candidate_address
        self.choice = choice

    def __getattr__(self, attr):
        return self.data[attr]

    def to_dict(self):
        return OrderedDict({'voter_address': self.voter_address,
                            'candidate_address': self.candidate_address,
                            'choice': self.choice})

    def sign_vote(self):
        private_key = RSA.importKey(binascii.unhexlify(self.voter_private_key))
        voter = PKCS1_v1_5.new(private_key)
        h = SHA.new(str(self.to_dict()).encode('utf8'))
        return binascii.hexlify(voter.sign(h)).decode('ascii')

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/make/vote')
def make_vote():
    return render_template('make_vote.html')


@app.route('/view/votes')
def view_votes():
    return render_template('view_votes.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/help')
def vote_help():
    return render_template('help.html')


@app.route('/wallet/new', methods=['GET'])
def new_wallet():
    random_gen = Crypto.Random.new().read
    private_key = RSA.generate(1024, random_gen)
    public_key = private_key.publickey()
    response = {
        'private_key': binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
        'public_key': binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
    }

    return jsonify(response), 200


@app.route('/generate/vote', methods=['POST'])
def generate_vote():
    voter_address = request.form['voter_address']
    voter_private_key = request.form['voter_private_key']
    candidate_address = request.form['candidate_address']
    choice = request.form['choice']

    vote = Vote(voter_address, voter_private_key, candidate_address, choice)

    response = {'vote': vote.to_dict(), 'signature': vote.sign_vote()}

    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=8080, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port)
