import binascii
import hashlib
import json
from collections import OrderedDict
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

MINING_SENDER = "THE BLOCKCHAIN"
MINING_REWARD = 1
MINING_DIFFICULTY = 2


class Blockchain:

    def __init__(self):

        self.votes = []
        self.chain = []
        self.candidate_votes = []
        self.nodes = set()
        # Generate random number to be used as node_id
        self.node_id = str(uuid4()).replace('-', '')
        # Create genesis block
        self.create_block(0, '00')

    # def get_candidate_votes(self):
    #     return self.candidate_votes

    def register_node(self, node_url):
        # Checking node_url has valid format
        parsed_url = urlparse(node_url)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts a URL without scheme like '192.168.0.5:5050'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    @staticmethod
    def verify_vote_signature(voter_address, signature, vote):
        public_key = RSA.importKey(binascii.unhexlify(voter_address))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA.new(str(vote).encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(signature))

    def submit_vote(self, voter_address, candidate_address, choice, signature):
        vote = OrderedDict({'voter_address': voter_address,
                            'candidate_address': candidate_address,
                            'choice': choice})

        # Reward for mining a block
        if voter_address == MINING_SENDER:
            self.votes.append(vote)
            return len(self.chain) + 1
        # Manages votes from wallet to another wallet
        else:
            vote_verification = self.verify_vote_signature(voter_address, signature, vote)
            if vote_verification:
                self.votes.append(vote)
                return len(self.chain) + 1
                # Count votes for each candidate
                # if candidate_address not in self.candidate_votes:
                #   self.candidate_votes[candidate_address] = 0
                #   self.candidate_votes[candidate_address] += 1
            else:
                return False

    def create_block(self, nonce, previous_hash):
        """
        Add a block of votes to the blockchain
        """
        block = {'block_number': len(self.chain) + 1,
                 'timestamp': time(),
                 'votes': self.votes,
                 'nonce': nonce,
                 'previous_hash': previous_hash}

        # Reset the current list of votes
        self.votes = []

        self.chain.append(block)
        return block

    @staticmethod
    def hash(block):
        """
        Create an SHA-256 hash of a block
        """
        block_string = json.dumps(block, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self):
        """
        Proof of work algorithm
        """
        last_block = self.chain[-1]
        last_hash = self.hash(last_block)

        nonce = 0
        while self.valid_proof(self.votes, last_hash, nonce) is False:
            nonce += 1

        return nonce

    @staticmethod
    def valid_proof(votes, last_hash, nonce, difficulty=MINING_DIFFICULTY):
        """
        Check if a hash value satisfies the mining conditions. This function is used within the proof_of_work function.
        """
        guess = (str(votes) + str(last_hash) + str(nonce)).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:difficulty] == '0' * difficulty

    def valid_chain(self, chain):
        """
        check if a blockchain is valid
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            votes = block['votes'][:-1]
            # Need to make sure that the dictionary is ordered. Otherwise, we'll get a different hash
            vote_elements = ['voter_address', 'candidate_address', 'choice']
            votes = [OrderedDict((k, vote[k]) for k in vote_elements) for vote in votes]

            if not self.valid_proof(votes, block['previous_hash'], block['nonce'], MINING_DIFFICULTY):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Resolve conflicts between blockchain's nodes
        by replacing our chain with the longest one in the network.
        """
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            print('https://' + node + '/chain')
            response = requests.get('https://' + node + '/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False


# Instantiate the Node
app = Flask(__name__)
CORS(app)

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/')
def index():
    return render_template('./main.html')

@app.route('/configure')
def configure():
    return render_template('./configure.html')


@app.route('/votes/new', methods=['POST'])
def new_vote():
    values = request.form

    # Check that the required fields are in the POST data
    required = ['voter_address', 'candidate_address', 'choice', 'signature']
    if not all(k in values for k in required):
        return 'Missing values', 400
    # Create a new vote
    vote_result = blockchain.submit_vote(values['voter_address'], values['candidate_address'], values['choice'],
                                         values['signature'])

    if not vote_result:
        response = {'message': 'Invalid Vote!'}
        return jsonify(response), 406
    else:
        response = {'message': 'Vote will be added to Block ' + str(vote_result)}
        return jsonify(response), 201

@app.route('/votes/get', methods=['GET'])
def get_votes():
    # Get votes from votes pool
    votes = blockchain.votes

    response = {'votes': votes}
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.chain[-1]
    nonce = blockchain.proof_of_work()

    # We must receive a reward for finding the proof.
    blockchain.submit_vote(voter_address=MINING_SENDER, candidate_address=blockchain.node_id,
                           choice=MINING_REWARD, signature="")

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(nonce, previous_hash)

    response = {
        'message': "New Block Forged",
        'block_number': block['block_number'],
        'votes': block['votes'],
        'nonce': block['nonce'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.form
    nodes = values.get('nodes').replace(" ", "").split(',')

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': [node for node in blockchain.nodes],
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


@app.route('/nodes/get', methods=['GET'])
def get_nodes():
    nodes = list(blockchain.nodes)
    response = {'nodes': nodes}
    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5050, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port)
