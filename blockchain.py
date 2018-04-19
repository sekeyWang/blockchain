# coding:utf-8
from time import time
import hashlib
from flask import Flask, jsonify, request
import json


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.produce_res=[]
        self.transfer_res=[]
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, data=[], previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': data,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.chain.append(block)
        return block

    def sell_to_item(self, sell_id):
        for blocks in self.chain:
            trans = blocks['transactions']
            for t in trans:
                if t['id'] == sell_id:
                    return t['item_id']

    def find(self, sell_id):
        self.produce_res=[]
        self.transfer_res=[]
        id = self.sell_to_item(sell_id)
        self.dfs(id)
        return self.produce_res, self.transfer_res

    def dfs(self, id):
        for blocks in self.chain:
            trans = blocks['transactions']
            for t in trans:
                if t['item_id'] == id:
                    if t['type'] == 'produce':
                        self.produce_res.append(t)
                        if t['material_id'] is not None:
                            self.dfs(t['material_id'])
                    if t['type'] == 'transfer':
                        self.transfer_res.append(t)

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = (str(last_proof)+str(proof)).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Instantiate our Node
app = Flask(__name__)

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['POST'])
def mine():
    proof = request.form['proof']
    data = request.form['data']
    data = json.loads(data)

    last_block = blockchain.last_block
    last_proof = last_block['proof']

    if blockchain.valid_proof(last_proof, proof) is False:
        return 'False proof', 401

    # Forge the new Block by adding it to the chain
    block = blockchain.new_block(proof=proof, data=data)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
#        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return jsonify(response), 200


@app.route('/last', methods=['GET'])
def last():
    last_block = blockchain.last_block
    response = {
        'proof': last_block['proof'],
        'index': last_block['index']
    }
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/find', methods=['POST'])
def find():
    id = request.form['id']
    res = blockchain.find(int(id))
    response = {
        'produce' : res[0],
        'transfer' : res[1],
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True,threaded=True)