# coding:utf-8
import requests
import hashlib
import json


def proof_of_work(last_proof):
    """
    简单的工作量证明:
     - 查找一个 p' 使得 hash(pp') 以4个0开头
     - p 是上一个块的证明,  p' 是当前的证明
    :param last_proof: <int>
    :return: <int>
    """

    proof = 0
    while valid_proof(last_proof, proof) is False:
        proof += 1

    return proof


def valid_proof(last_proof, proof):
    """
    验证证明: 是否hash(last_proof, proof)以4个0开头?
    :param last_proof: <int> Previous Proof
    :param proof: <int> Current Proof
    :return: <bool> True if correct, False if not.
    """

    guess = (str(last_proof) + str(proof)).encode()
#    print guess
    guess_hash = hashlib.sha256(guess).hexdigest()
    return guess_hash[:4] == "0000"


if __name__ == '__main__':
    response = requests.get(url="http://127.0.0.1:5000/last")
    last_proof = json.loads(response.text)["proof"]
    proof = proof_of_work(last_proof)
    PostData = {
        "proof": proof
    }
    print PostData
    response = requests.post(url="http://127.0.0.1:5000/mine", data=PostData)#    print response.text