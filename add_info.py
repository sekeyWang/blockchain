# coding:utf-8
#1小麦 2酒曲 3瓶子 4包装 5瓶装酒
#factory: 1-3小麦 4-6酒曲 7-9瓶子 10-12包装 13-15瓶装酒
import random
from datetime import datetime
import requests
import hashlib
import json
import time
from graphviz import Digraph


class Collection(object):
    def __init__(self):
        self.type = {}
        self.remaining = [[]]
        self.total_item_id = 0
        self.total_place_id = 0

    def new_place(self):
        self.total_place_id = self.total_place_id + 1
        return self.total_place_id

    def add_factory(self, name):
        self.remaining.append([])
        place_id = self.new_place()
        for item in self.type:
            if item == name:
                self.type[item].append(place_id)
                return
        self.type[name] = [place_id]

    def add_item(self, factory_id):
        self.total_item_id = self.total_item_id+1
        self.remaining[factory_id].append(self.total_item_id)
        return self.total_item_id

    def take_item(self, name, delete):
        for id in self.type[name]:
            if len(self.remaining[id]) > 0:
                ret = self.remaining[id][0]
                if delete is True: del self.remaining[id][0]
                return id,ret

    def check_item(self, name):
        if name not in self.type: return False
        for id in self.type[name]:
            if len(self.remaining[id]) > 0: return True
        return False


collection = Collection()


class Block(object):
    def __init__(self):
        self.block=[]
        self.event_id = 0

    def add_item(self, item_id, item_name, factory_id, date, material_id=None, material_name=None):
        self.event_id = self.event_id + 1
        new_item={
            'id' : self.event_id,
            'type': 'produce',
            'item_id': item_id,
            'item_name': item_name,
            'factory_id': factory_id,
            'material_id': material_id,
            'material_name': material_name,
            'date': date
        }
        self.block.append(new_item)
        return self.event_id
#        print new_item

    def add_trans(self, place_id, date, item_id, status):
        self.event_id = self.event_id + 1
        new_trans={
            'id' : self.event_id,
            'type': 'transfer',
            'place_id': place_id,
            'date': date,
            'item_id': item_id,
            'status':status
        }
        self.block.append(new_trans)
        return self.event_id
#        print new_trans

    def add_sell(self, factory_id, item_id, date):
        self.event_id = self.event_id + 1
        new_sell={
            'id' : self.event_id,
            'type': 'sell',
            'factory_id': factory_id,
            'item_id': item_id,
            'date': date
        }
        self.block.append(new_sell)
        return self.event_id

    def full_block(self):
        return self.block

    def empty_block(self):
        self.block = []


block = Block()


class System(object):
    def __init__(self):
        pass

    def now_time(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    def made(self, name, input = []):
        for material in input:
            result = collection.check_item(material['name'])
            if result is False:
                print "Fail to made " + name
                print "Reason: No "+ material['name'] + " available"
                return False
        item_name = name
        factory_id = random.sample(collection.type[item_name],1)[0]
        item_id = collection.add_item(factory_id)
        time.sleep(1)
        if input == []:
            block.add_item(
                item_id=item_id,
                item_name=item_name,
                factory_id=factory_id,
                date=self.now_time()
            )
        else:
            material_list=[]
            for i in input:
                ret = collection.take_item(i['name'], i['delete'])
                material_factory_id = ret[0]
                material_id = ret[1]
                material_list.append([material_id, i['name']])
                block.add_trans(
                    place_id=material_factory_id,
                    status='begin',
                    item_id=material_id,
                    date=self.now_time()
                )
                time.sleep(1)
                block.add_trans(
                    place_id=factory_id,
                    status='end',
                    item_id=material_id,
                    date=self.now_time()
                )
                time.sleep(1)
#            print material_list
            for material in material_list:
                material_id = material[0]
                material_name = material[1]
                block.add_item(
                    item_id=item_id,
                    item_name=item_name,
                    factory_id=factory_id,
                    material_name=material_name,
                    material_id=material_id,
                    date=self.now_time()
                )
        print "Made " + name + " successfully"
        print "Item id: " + str(item_id)
        return True

    def sell(self, name):
        res = collection.check_item(name)
        if res is False:
            print "Fail to sell " + name
            print "Reason: No " + name + " available"
            return False
        res = collection.take_item(name, True)
        factory_id = res[0]
        item_id = res[1]
        now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        id = block.add_sell(
            factory_id=factory_id,
            item_id=item_id,
            date=now_time
        )
        print "Sell " + name + " successfully"
        print "Sell id: " + str(id)

    def trace(self, id):
        postdata = {'id': id}
        response = requests.post(url="http://127.0.0.1:5000/find", data=postdata)
        return json.loads(response.text)


system = System()


class Miner(object):
    def __init__(self):
        pass

    def valid_proof(self, last_proof, proof):
        guess = (str(last_proof) + str(proof)).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    def mine(self):
        response = requests.get(url="http://127.0.0.1:5000/last")
        last_proof = json.loads(response.text)["proof"]
        index = json.loads(response.text)["index"] + 1
        print 'I am mining block ' + str(index)

        proof = self.proof_of_work(last_proof)
        data = block.full_block()
        postdata = {
            'data': json.dumps(data),
            'proof': proof
        }
        block.empty_block()
        response = requests.post(url="http://127.0.0.1:5000/mine", data=postdata)
        print response.text


miner = Miner()


def test1():
    system.sell("wine_last")
    system.made(name="wine_first", input=[{'name': 'wheat', 'delete': True}, {'name': 'yeast', 'delete': False}])
    # No wheat, Fail
    system.made(name='wheat')
    system.made(name='yeast')
    system.made(name='bottle')
    system.made(name="wine_first", input=[{'name': 'wheat', 'delete': True}, {'name': 'yeast', 'delete': False}])
    system.made(name="wine_last", input=[{'name': 'bottle', 'delete': True}, {'name': 'decoration', 'delete': True},
                                          {'name': 'wine_first', 'delete': True}])
    # No decoration
    system.made(name='decoration')
    system.made(name="wine_last", input=[{'name': 'bottle', 'delete': True}, {'name': 'decoration', 'delete': True},
                                          {'name': 'wine_first', 'delete': True}])

    system.sell("wine_last")
    miner.mine()
#    print "Resources:", collection.item


def test2():
    for i in range(0, 2):
        collection.add_factory('wheat')
    for i in range(0, 3):
        collection.add_factory('yeast')
    for i in range(0, 2):
        collection.add_factory('bottle')
    for i in range(0, 1):
        collection.add_factory('decoration')
    for i in range(0, 3):
        collection.add_factory('wine_first')
    for i in range(0, 4):
        collection.add_factory('wine_last')


def test3():
    res = system.trace(20)
#    print res
    produce = res['produce']
    transfer = res['transfer']
    dot = Digraph(comment='Graph')
    item = []
    for p in produce:
        if p['item_id'] not in item:
            item.append(p['item_id'])
            dot.node(str(p['factory_id']),
                    'Name: ' + p['item_name']
                     + '\n' + 'Item id: ' + str(p['item_id'])
                     + '\n' + 'Factory id:' + str(p['factory_id'])
                     + '\n' + 'Time: ' + str(p['date'])
                     )
    for i in item:
        begin = 0
        end = 0
        for t in transfer:
            print i, t['item_id']
            if t['item_id'] == i:
                print "yes"
                if t['status'] == 'begin': begin = t
                if t['status'] == 'end': end = t
        print begin
        print end
        if (begin != 0 and end != 0):
            dot.edge(str(begin['place_id']), str(end['place_id']),
                     'Begin time: ' + begin['date']
                     + '\n' + 'End time: ' + end['date'])
    print(dot.source)
    dot.render('test-output/round-table.gv', view=True)


if __name__ == '__main__':
    test2()
    test1()
    test3()
